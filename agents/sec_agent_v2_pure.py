"""
SEC Agent V2 - 순수 A2A 구현

SEC 공시 데이터를 수집하는 독립적인 V2 에이전트
V1 의존성 없이 직접 SEC EDGAR API 호출
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup
import json

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from pydantic import BaseModel
from fastapi import Depends

# 설정 관리자 및 커스텀 에러 임포트
from utils.config_manager import config
from utils.errors import APIRateLimitError, APITimeoutError, DataNotFoundError
from utils.auth import verify_api_key
from utils.translation_manager import translation_manager, translate_text

load_dotenv(override=True)

# 로깅 설정
logger = logging.getLogger(__name__)


class SECRequest(BaseModel):
    ticker: str


class SECAgentV2(BaseAgent):
    """SEC 공시 수집 V2 에이전트"""
    
    def __init__(self):
        # 설정에서 에이전트 정보 가져오기
        agent_config = config.get_agent_config("sec")
        
        super().__init__(
            name=agent_config.get("name", "SEC Agent V2"),
            description="SEC 공시 데이터를 수집하는 A2A 에이전트",
            port=agent_config.get("port", 8210),
            registry_url="http://localhost:8001"
        )
        
        # API 설정
        self.user_agent = config.get_env("SEC_API_USER_AGENT", "A2A-Agent/1.0")
        self.max_filings = int(config.get_env("MAX_SEC_FILINGS", "20"))
        
        # 타임아웃 설정
        self.timeout = agent_config.get("timeout", 60)
        
        # 더미 데이터 사용 여부
        self.use_mock_data = config.is_mock_data_enabled()
        
        # 캐시 설정
        self.cik_cache = {}  # CIK 매핑 캐시
        
        # HTTP 엔드포인트 설정
        self._setup_http_endpoints()
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "sec_data_collection",
            "version": "2.0",
            "description": "SEC 공시 데이터 수집",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "주식 티커"}
                },
                "required": ["ticker"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "array"},
                    "count": {"type": "integer"},
                    "source": {"type": "string"}
                }
            }
        })
        
        print("✅ SEC Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 SEC Agent V2 종료 중...")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                
                if action == "sec_data_collection":
                    await self._handle_sec_collection(message)
                else:
                    await self.reply_to_message(
                        message,
                        result={"error": f"Unsupported action: {action}"},
                        success=False
                    )
                    
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
            
    async def _handle_sec_collection(self, message: A2AMessage):
        """SEC 공시 수집 요청 처리"""
        payload = message.body.get("payload", {})
        ticker = payload.get("ticker", "")
        
        print(f"📄 SEC 공시 수집 시작: {ticker}")
        
        try:
            # SEC EDGAR API로 공시 수집
            filings_data = await self._fetch_sec_filings(ticker)
            
            # 결과 포맷팅
            result = {
                "data": filings_data,
                "count": len(filings_data),
                "source": "sec",
                "log_message": f"✅ {ticker} 공시 {len(filings_data)}개 수집 완료"
            }
            
            # 데이터 수집 완료 이벤트 브로드캐스트
            await self.broadcast_event(
                event_type="data_collected",
                event_data={
                    "source": "sec",
                    "ticker": ticker,
                    "count": len(filings_data)
                }
            )
            
            await self.reply_to_message(message, result=result, success=True)
            
        except Exception as e:
            print(f"❌ SEC 공시 수집 오류: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e), "data": [], "count": 0},
                success=False
            )
            
    async def _extract_filing_content(self, filing_url: str, form_type: str) -> Dict[str, Any]:
        """공시 문서에서 핵심 정보 추출 및 번역"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    filing_url,
                    headers={"User-Agent": self.user_agent}
                )
                
                if response.status_code != 200:
                    return {}
                    
                content = response.text
                
                # HTML 문서인 경우 BeautifulSoup으로 파싱
                if "<html" in content.lower():
                    soup = BeautifulSoup(content, 'html.parser')
                    text_content = soup.get_text()
                else:
                    text_content = content
                    
                # 폼 타입별 핵심 정보 추출
                extracted_info = {
                    "filing_url": filing_url,
                    "extraction_timestamp": datetime.now().isoformat()
                }
                
                if form_type == "10-K":
                    # 연간 보고서에서 핵심 재무 정보 추출
                    extracted_info.update(await self._extract_10k_info_enhanced(text_content))
                elif form_type == "10-Q":
                    # 분기 보고서에서 핵심 정보 추출
                    extracted_info.update(await self._extract_10q_info_enhanced(text_content))
                elif form_type == "8-K":
                    # 임시 보고서에서 주요 이벤트 추출
                    extracted_info.update(await self._extract_8k_info_enhanced(text_content))
                elif form_type == "DEF 14A":
                    # 주주총회 위임장에서 핵심 정보 추출
                    extracted_info.update(await self._extract_proxy_info_enhanced(text_content))
                    
                return extracted_info
                
        except Exception as e:
            print(f"❌ 공시 내용 추출 오류: {e}")
            return {}
            
    async def _extract_10k_info_enhanced(self, text: str) -> Dict[str, Any]:
        """10-K 연간 보고서에서 상세 정보 추출 및 번역"""
        info = {
            "key_metrics": [],
            "key_metrics_translated": [],
            "risks": [],
            "risks_translated": [],
            "business_highlights": [],
            "business_highlights_translated": [],
            "financial_data": {},
            "md&a_summary": "",
            "md&a_summary_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())  # 다중 공백 제거
        
        # MD&A (Management Discussion and Analysis) 섹션 추출
        mda_pattern = r"(?:management.?s discussion and analysis|md&a).*?(?=item|part|\Z)"
        mda_match = re.search(mda_pattern, text[:50000], re.IGNORECASE | re.DOTALL)
        if mda_match:
            mda_text = mda_match.group(0)[:2000]  # 첫 2000자만
            # MD&A 요약
            summary_sentences = mda_text.split('.')[:5]  # 첫 5문장
            info["md&a_summary"] = '. '.join(summary_sentences)
            info["md&a_summary_translated"] = await translate_text(info["md&a_summary"], "ko")
        
        # 기존 추출 로직 계속...
        # 1. 매출 정보 추출
        revenue_patterns = [
            r"(?:total\s+)?(?:net\s+)?revenue[s]?(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"(?:total\s+)?net\s+sales(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1).replace(',', '')
                unit = "million" if "million" in match.group(0).lower() else "billion"
                multiplier = 1000000 if unit == "million" else 1000000000
                actual_value = float(value) * multiplier
                
                metric_en = f"Revenue: ${value} {unit}"
                metric_ko = f"매출: ${value} {unit}"
                
                info["key_metrics"].append(metric_en)
                info["key_metrics_translated"].append(metric_ko)
                info["financial_data"]["revenue"] = actual_value
                break
            if info["financial_data"].get("revenue"):
                break
        
        # 리스크 요인 추출 (Risk Factors 섹션)
        risk_section_pattern = r"(?:risk factors).*?(?=item|part|\Z)"
        risk_match = re.search(risk_section_pattern, text[:100000], re.IGNORECASE | re.DOTALL)
        if risk_match:
            risk_text = risk_match.group(0)[:5000]
            # 주요 리스크 키워드 추출
            risk_keywords = [
                "competition", "regulatory", "economic conditions", "cybersecurity",
                "supply chain", "pandemic", "climate change", "litigation"
            ]
            for keyword in risk_keywords:
                if keyword in risk_text.lower():
                    risk_en = f"Risk: {keyword.title()}"
                    risk_ko = await translate_text(risk_en, "ko")
                    info["risks"].append(risk_en)
                    info["risks_translated"].append(risk_ko)
        
        return info
    
    def _extract_10k_info(self, text: str) -> Dict[str, Any]:
        """10-K 연간 보고서에서 핵심 정보 추출"""
        info = {
            "key_metrics": [],
            "risks": [],
            "business_highlights": [],
            "financial_data": {}
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())  # 다중 공백 제거
        
        # 1. 매출 정보 추출 (더 정교한 패턴)
        revenue_patterns = [
            r"(?:total\s+)?(?:net\s+)?revenue[s]?(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"(?:total\s+)?net\s+sales(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"(?:total\s+)?revenue[s]?(?:\s+of)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"revenue[s]?\s+(?:increased|decreased|was).*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1).replace(',', '')
                unit = "million" if "million" in match.group(0).lower() else "billion"
                multiplier = 1000000 if unit == "million" else 1000000000
                actual_value = float(value) * multiplier
                info["key_metrics"].append(f"매출: ${value} {unit}")
                info["financial_data"]["revenue"] = actual_value
                break
            if info["financial_data"].get("revenue"):
                break
                
        # 2. 순이익 정보 추출
        income_patterns = [
            r"net\s+income(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"net\s+earnings(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"net\s+(?:income|earnings)\s+of\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        ]
        
        for pattern in income_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1).replace(',', '')
                unit = "million" if "million" in match.group(0).lower() else "billion"
                multiplier = 1000000 if unit == "million" else 1000000000
                actual_value = float(value) * multiplier
                info["key_metrics"].append(f"순이익: ${value} {unit}")
                info["financial_data"]["net_income"] = actual_value
                break
            if info["financial_data"].get("net_income"):
                break
                
        # 3. 영업이익 추출
        operating_patterns = [
            r"operating\s+income(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"income\s+from\s+operations(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        ]
        
        for pattern in operating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                unit = "million" if "million" in match.group(0).lower() else "billion"
                info["key_metrics"].append(f"영업이익: ${value} {unit}")
                break
                
        # 4. 자산 정보 추출
        asset_patterns = [
            r"total\s+assets(?:\s+(?:was|were))?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)",
            r"assets\s+of\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        ]
        
        for pattern in asset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                unit = "million" if "million" in match.group(0).lower() else "billion"
                info["key_metrics"].append(f"총자산: ${value} {unit}")
                break
                
        # 5. 성장률 추출
        growth_patterns = [
            r"revenue[s]?\s+(?:increased|grew)(?:\s+by)?\s+([\d.]+)%",
            r"([\d.]+)%\s+(?:increase|growth)\s+in\s+revenue",
            r"revenue[s]?\s+(?:decreased|declined)(?:\s+by)?\s+([\d.]+)%"
        ]
        
        for pattern in growth_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                growth = match.group(1)
                if "decreased" in match.group(0).lower() or "declined" in match.group(0).lower():
                    growth = f"-{growth}"
                info["key_metrics"].append(f"매출 성장률: {growth}%")
                break
                
        # 6. 리스크 팩터 추출 (Risk Factors 섹션에서 구체적인 내용 추출)
        risk_section = re.search(r"risk\s+factors(.*?)(?:item\s+\d|$)", text, re.IGNORECASE | re.DOTALL)
        if risk_section:
            risk_text = risk_section.group(1)[:2000]  # 처음 2000자만
            
            # 주요 리스크 키워드 찾기
            risk_keywords = [
                "competition", "regulatory", "economic conditions", "supply chain",
                "cybersecurity", "pandemic", "climate change", "currency fluctuation",
                "intellectual property", "data privacy", "market volatility"
            ]
            
            found_risks = []
            for keyword in risk_keywords:
                if keyword in risk_text.lower():
                    korean_map = {
                        "competition": "경쟁 심화",
                        "regulatory": "규제 리스크",
                        "economic conditions": "경제 상황",
                        "supply chain": "공급망 리스크",
                        "cybersecurity": "사이버보안",
                        "pandemic": "팬데믹 리스크",
                        "climate change": "기후변화",
                        "currency fluctuation": "환율 변동",
                        "intellectual property": "지적재산권",
                        "data privacy": "데이터 프라이버시",
                        "market volatility": "시장 변동성"
                    }
                    found_risks.append(korean_map.get(keyword, keyword))
            
            if found_risks:
                info["risks"] = found_risks[:5]  # 상위 5개만
            else:
                info["risks"].append("일반적인 사업 리스크")
                
        # 7. 사업 하이라이트 추출
        highlight_keywords = [
            r"launched\s+new\s+product",
            r"acquired\s+(?:company|business)",
            r"expanded\s+(?:into|operations)",
            r"partnership\s+with",
            r"investment\s+in\s+(?:R&D|research)",
            r"market\s+share\s+(?:increased|grew)"
        ]
        
        for pattern in highlight_keywords:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                info["business_highlights"].append(context.strip())
                
        return info
        
    async def _extract_10q_info_enhanced(self, text: str) -> Dict[str, Any]:
        """10-Q 분기 보고서에서 상세 정보 추출 및 번역"""
        info = {
            "quarterly_metrics": [],
            "quarterly_metrics_translated": [],
            "segment_performance": [],
            "segment_performance_translated": [],
            "quarter_highlights": "",
            "quarter_highlights_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        
        # 분기 매출 추출
        quarterly_revenue = re.search(
            r"three\s+months.*?revenue.*?\$?([\d,]+(?:\.\d+)?)[\s]?(?:million|billion)",
            text, re.IGNORECASE
        )
        if quarterly_revenue:
            value = quarterly_revenue.group(1)
            metric_en = f"Quarterly Revenue: ${value}"
            metric_ko = f"분기 매출: ${value}"
            info["quarterly_metrics"].append(metric_en)
            info["quarterly_metrics_translated"].append(metric_ko)
            
        # 전년 대비 성장률
        yoy_pattern = re.search(
            r"compared\s+to.*?prior\s+year.*?([\d.]+)%",
            text, re.IGNORECASE
        )
        if yoy_pattern:
            growth = yoy_pattern.group(1)
            metric_en = f"YoY Growth: {growth}%"
            metric_ko = f"전년 대비 성장률: {growth}%"
            info["quarterly_metrics"].append(metric_en)
            info["quarterly_metrics_translated"].append(metric_ko)
        
        # 세그먼트별 실적 추출
        segment_pattern = r"segment.*?revenue.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)"
        segment_matches = re.finditer(segment_pattern, text[:5000], re.IGNORECASE)
        for match in segment_matches[:3]:  # 최대 3개
            segment_info = match.group(0)
            translated = await translate_text(segment_info, "ko")
            info["segment_performance"].append(segment_info)
            info["segment_performance_translated"].append(translated)
        
        # 분기 하이라이트 추출
        highlight_section = re.search(
            r"(?:highlights|overview).*?(?=item|part|financial|$)",
            text[:3000], re.IGNORECASE | re.DOTALL
        )
        if highlight_section:
            highlights = highlight_section.group(0)[:500]
            info["quarter_highlights"] = highlights
            info["quarter_highlights_translated"] = await translate_text(highlights, "ko")
        
        return info
        
    def _extract_10q_info(self, text: str) -> Dict[str, Any]:
        """10-Q 분기 보고서에서 핵심 정보 추출"""
        info = {
            "quarterly_metrics": [],
            "segment_performance": []
        }
        
        # 분기 매출 추출
        quarterly_revenue = re.search(
            r"three\s+months.*?revenue.*?\$?([\d,]+(?:\.\d+)?)[\s]?(?:million|billion)",
            text, re.IGNORECASE
        )
        if quarterly_revenue:
            info["quarterly_metrics"].append(f"분기 매출: ${quarterly_revenue.group(1)}")
            
        # 전년 대비 성장률
        growth_pattern = re.search(
            r"(?:increased?|decreased?|grew|declined?).*?([\d]+(?:\.\d+)?)\s*%",
            text, re.IGNORECASE
        )
        if growth_pattern:
            info["quarterly_metrics"].append(f"성장률: {growth_pattern.group(1)}%")
            
        return info
        
    async def _extract_8k_info_enhanced(self, text: str) -> Dict[str, Any]:
        """8-K 임시 보고서에서 상세 이벤트 정보 추출 및 번역"""
        info = {
            "events": [],
            "events_translated": [],
            "event_details": [],
            "event_details_translated": [],
            "material_changes": "",
            "material_changes_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        
        # Item별 중요 이벤트 매핑
        item_patterns = {
            "Item 1.01": "중요 계약 체결",
            "Item 2.01": "자산 인수 완료",
            "Item 2.02": "운영 결과 및 재무 상태",
            "Item 2.03": "중요 의무 발생",
            "Item 2.05": "사업 중단 비용",
            "Item 3.01": "파산 또는 법정관리",
            "Item 5.02": "임원 변경",
            "Item 5.03": "정관 또는 규정 변경",
            "Item 7.01": "규제 공시",
            "Item 8.01": "기타 중요 사항"
        }
        
        # Item별 이벤트 추출
        for item_code, item_desc in item_patterns.items():
            pattern = f"{item_code}.*?(?=Item|$)"
            match = re.search(pattern, text[:10000], re.IGNORECASE)
            if match:
                event_text = match.group(0)[:500]
                event_en = f"{item_code}: {event_text[:200]}..."
                event_ko = f"{item_code}: {item_desc}"
                
                info["events"].append(event_en)
                info["events_translated"].append(event_ko)
                
                # 상세 내용 추출
                detail_text = event_text[:300]
                detail_translated = await translate_text(detail_text, "ko")
                info["event_details"].append(detail_text)
                info["event_details_translated"].append(detail_translated)
        
        # 중요 변경사항 요약
        material_section = re.search(
            r"(?:material|significant).*?(?:change|development|event).*?(?=\.|$)",
            text[:2000], re.IGNORECASE
        )
        if material_section:
            material_text = material_section.group(0)
            info["material_changes"] = material_text
            info["material_changes_translated"] = await translate_text(material_text, "ko")
        
        return info
    
    def _extract_8k_info(self, text: str) -> Dict[str, Any]:
        """8-K 임시 보고서에서 주요 이벤트 추출"""
        info = {
            "events": [],
            "material_changes": []
        }
        
        # 주요 이벤트 키워드
        event_keywords = {
            "acquisition": "인수합병",
            "merger": "합병",
            "resignation": "경영진 사임",
            "appointment": "신규 임명",
            "dividend": "배당 발표",
            "buyback": "자사주 매입",
            "restructuring": "구조조정",
            "litigation": "소송",
            "partnership": "파트너십",
            "product launch": "신제품 출시"
        }
        
        for eng, kor in event_keywords.items():
            if eng in text.lower():
                info["events"].append(kor)
                
        return info
        
    async def _extract_proxy_info_enhanced(self, text: str) -> Dict[str, Any]:
        """DEF 14A 주주총회 위임장에서 상세 정보 추출 및 번역"""
        info = {
            "executive_compensation": [],
            "executive_compensation_translated": [],
            "proposals": [],
            "proposals_translated": [],
            "board_changes": [],
            "board_changes_translated": [],
            "governance_highlights": "",
            "governance_highlights_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        
        # 임원 보수 정보 추출
        comp_patterns = [
            r"(?:CEO|chief executive).*?compensation.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand)?",
            r"named executive officers.*?total.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand)?",
            r"total compensation.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand)?"
        ]
        
        for pattern in comp_patterns[:3]:  # 최대 3개
            match = re.search(pattern, text[:10000], re.IGNORECASE)
            if match:
                comp_info = match.group(0)
                comp_translated = await translate_text(comp_info, "ko")
                info["executive_compensation"].append(comp_info)
                info["executive_compensation_translated"].append(comp_translated)
        
        # 주주 제안 추출
        proposal_pattern = r"proposal\s*\d+.*?(?=proposal|$)"
        proposal_matches = re.finditer(proposal_pattern, text[:20000], re.IGNORECASE)
        
        for i, match in enumerate(proposal_matches):
            if i >= 5:  # 최대 5개 제안
                break
            proposal_text = match.group(0)[:300]
            proposal_translated = await translate_text(proposal_text, "ko")
            info["proposals"].append(proposal_text)
            info["proposals_translated"].append(proposal_translated)
        
        # 이사회 변경사항
        board_patterns = [
            r"(?:elect|nominate|appoint).*?director",
            r"board.*?(?:resignation|retirement)",
            r"new.*?board member"
        ]
        
        for pattern in board_patterns:
            match = re.search(pattern, text[:10000], re.IGNORECASE)
            if match:
                board_info = text[max(0, match.start()-100):match.end()+100]
                board_translated = await translate_text(board_info, "ko")
                info["board_changes"].append(board_info)
                info["board_changes_translated"].append(board_translated)
        
        # 거버넌스 하이라이트
        governance_section = re.search(
            r"(?:corporate governance|governance highlights).*?(?=item|proposal|$)",
            text[:5000], re.IGNORECASE | re.DOTALL
        )
        if governance_section:
            governance_text = governance_section.group(0)[:500]
            info["governance_highlights"] = governance_text
            info["governance_highlights_translated"] = await translate_text(governance_text, "ko")
        
        return info
    
    def _extract_proxy_info(self, text: str) -> Dict[str, Any]:
        """DEF 14A 주주총회 위임장에서 핵심 정보 추출"""
        info = {
            "executive_compensation": [],
            "proposals": []
        }
        
        # 임원 보수 정보
        comp_pattern = re.search(
            r"total\s+compensation.*?\$?([\d,]+(?:\.\d+)?)[\s]?(?:million)?",
            text, re.IGNORECASE
        )
        if comp_pattern:
            info["executive_compensation"].append(f"임원 총 보수: ${comp_pattern.group(1)}")
            
        # 주주 제안 사항
        if "proposal" in text.lower():
            info["proposals"].append("주주 제안 사항 포함")
            
        return info
    
    async def _get_cik_for_ticker(self, ticker: str) -> str:
        """티커에서 CIK(Central Index Key) 조회"""
        # 캐시 확인
        if ticker.upper() in self.cik_cache:
            return self.cik_cache[ticker.upper()]
            
        try:
            # SEC의 공식 티커-CIK 매핑 파일 다운로드
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    tickers_data = response.json()
                    
                    # 모든 회사 정보를 캐시에 저장
                    for company_data in tickers_data.values():
                        company_ticker = company_data.get('ticker', '').upper()
                        cik = str(company_data.get('cik_str', '')).zfill(10)
                        if company_ticker:
                            self.cik_cache[company_ticker] = cik
                    
                    # 요청된 티커의 CIK 반환
                    result = self.cik_cache.get(ticker.upper(), None)
                    if not result:
                        raise DataNotFoundError("CIK", ticker)
                    return result
                elif response.status_code == 429:
                    raise APIRateLimitError("SEC", 60)
                else:
                    logger.error(f"❌ SEC 티커 데이터 조회 실패: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ CIK 조회 오류: {e}")
            # 폴백: 기본 CIK 매핑 사용
            fallback_map = {
                "AAPL": "0000320193",
                "TSLA": "0001318605",
                "NVDA": "0001045810",
                "GOOGL": "0001652044",
                "MSFT": "0000789019",
                "AMZN": "0001018724",
                "META": "0001326801",
                "PLTR": "0001321655"
            }
            return fallback_map.get(ticker.upper())
    
    async def _fetch_sec_filings(self, ticker: str) -> List[Dict]:
        """SEC EDGAR API로 공시 가져오기"""
        # 더미 데이터 사용 모드인 경우
        if self.use_mock_data:
            logger.info(f"🎭 더미 데이터 모드 활성화 - 모의 SEC 공시 반환")
            return self._get_mock_filings(ticker)
            
        try:
            # 동적 CIK 조회
            cik = await self._get_cik_for_ticker(ticker)
            if not cik:
                logger.warning(f"⚠️ {ticker}의 CIK를 찾을 수 없습니다")
                return []  # 빈 데이터 반환
                
            # SEC EDGAR API 호출
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    recent_filings = data.get("filings", {}).get("recent", {})
                    
                    # 최근 공시 포맷팅
                    formatted_filings = []
                    forms = recent_filings.get("form", [])[:self.max_filings]
                    dates = recent_filings.get("filingDate", [])[:self.max_filings]
                    accessions = recent_filings.get("accessionNumber", [])[:self.max_filings]
                    
                    # 모든 배열의 최소 길이 확인
                    max_items = min(len(forms), len(dates), len(accessions), self.max_filings)
                    
                    for i in range(max_items):
                        # 각 배열 요소가 존재하는지 확인
                        form_type = forms[i] if i < len(forms) else "Unknown"
                        filing_date = dates[i] if i < len(dates) else ""
                        accession_number = accessions[i] if i < len(accessions) else ""
                        
                        if not accession_number:
                            continue
                            
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_number.replace('-', '')}/{accession_number}.txt"
                        
                        # 폼 타입별 설명 추가
                        form_descriptions = {
                            "10-K": "연간 보고서 - 회사의 연간 실적 및 재무상태",
                            "10-Q": "분기 보고서 - 분기별 실적 및 경영 현황",
                            "8-K": "임시 보고서 - 주요 이벤트 및 경영상 중요 변경사항",
                            "4": "내부자 거래 - 임원진의 주식 매매 내역",
                            "DEF 14A": "주주총회 위임장 - 주주총회 안건 및 임원 보수",
                            "144": "제한 주식 매도 신고 - 내부자의 주식 매도 계획",
                            "S-8": "직원 주식 옵션 - 직원 대상 주식 발행 계획",
                            "S-3": "유가증권 신고서 - 신규 증권 발행 계획"
                        }
                        
                        form_desc = form_descriptions.get(form_type, "기타 공시")
                        
                        # SEC 공시 제목과 요약 생성
                        title = f"{ticker} {form_type} 공시 ({filing_date})"
                        content = f"{form_desc}. 이 공시는 {ticker}의 {form_type} 양식으로 제출된 공식 문서입니다."
                        
                        # 공시 문서에서 핵심 정보 추출 시도
                        extracted_info = await self._extract_filing_content(filing_url, form_type)
                        
                        # 추출된 정보를 content에 추가 (번역된 버전 우선 사용)
                        if extracted_info:
                            if extracted_info.get("key_metrics_translated"):
                                content += f" 주요 지표: {', '.join(extracted_info['key_metrics_translated'])}"
                            elif extracted_info.get("key_metrics"):
                                content += f" 주요 지표: {', '.join(extracted_info['key_metrics'])}"
                                
                            if extracted_info.get("quarterly_metrics"):
                                content += f" 분기 실적: {', '.join(extracted_info['quarterly_metrics'])}"
                                
                            if extracted_info.get("events"):
                                content += f" 주요 이벤트: {', '.join(extracted_info['events'])}"
                                
                            if extracted_info.get("risks_translated"):
                                content += f" 리스크 요인: {', '.join(extracted_info['risks_translated'])}"
                            elif extracted_info.get("risks"):
                                content += f" 리스크 요인: {', '.join(extracted_info['risks'])}"
                                
                            if extracted_info.get("md&a_summary_translated"):
                                content += f" 경영진 분석: {extracted_info['md&a_summary_translated'][:200]}..."
                        
                        formatted_filings.append({
                            "form_type": form_type,
                            "title": title,
                            "content": content,
                            "description": form_desc,
                            "filing_date": filing_date,
                            "url": filing_url,
                            "source": "sec",
                            "sentiment": None,  # 나중에 감정분석에서 채움
                            "extracted_info": extracted_info,  # 추출된 상세 정보
                            "timestamp": datetime.now().isoformat(),  # 수집 타임스탬프
                            "log_message": f"📄 공시: {form_type} - {filing_date}"
                        })
                        
                    return formatted_filings
                elif response.status_code == 429:
                    raise APIRateLimitError("SEC", 60)
                else:
                    logger.error(f"❌ SEC API 오류: {response.status_code}")
                    return []  # 빈 데이터 반환
                    
        except (APIRateLimitError, DataNotFoundError):
            raise  # 커스텀 에러는 다시 발생시킴
        except httpx.TimeoutException:
            raise APITimeoutError("SEC", self.timeout)
        except Exception as e:
            logger.error(f"❌ SEC API 호출 오류: {e}")
            return []  # 빈 데이터 반환
            
    def _get_mock_filings(self, ticker: str) -> List[Dict]:
        """모의 공시 데이터 생성 - 티커별로 다른 내용"""
        today = datetime.now()
        
        # 티커별 특화된 공시 데이터
        ticker_specific_filings = {
            "AAPL": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 회계연도 매출 4,000억 달러 돌파",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "애플 연간 매출 사상 최대 기록. 서비스 부문 성장이 견인",
                    "log_message": "📄 공시: 10-K - 연간 매출 최대 기록"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 아이폰 판매 둔화",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 아이폰 판매량 전년 대비 5% 감소. 중국 시장 부진",
                    "log_message": "📄 공시: 10-Q - 아이폰 판매 둔화"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 자사주 900억 달러 매입 발표",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-buyback",
                    "source": "sec",
                    "sentiment": None,
                    "content": "애플 이사회, 900억 달러 규모 자사주 매입 프로그램 승인",
                    "log_message": "📄 공시: 8-K - 대규모 자사주 매입"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - AI 연구개발 투자 확대",
                    "filing_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-ai",
                    "source": "sec",
                    "sentiment": None,
                    "content": "AI 및 머신러닝 연구개발에 50억 달러 추가 투자 계획",
                    "log_message": "📄 공시: 8-K - AI R&D 투자"
                },
                {
                    "form_type": "DEF 14A",
                    "title": "Proxy Statement - 임원 보수 15% 인상",
                    "filing_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/DEF14A",
                    "source": "sec",
                    "sentiment": None,
                    "content": "주주총회 안건: CEO 및 주요 임원 보수 인상안",
                    "log_message": "📄 공시: DEF 14A - 임원 보수"
                }
            ],
            "TSLA": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 차량 인도량 180만대 달성",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "테슬라 연간 차량 인도량 180만대로 전년 대비 35% 성장",
                    "log_message": "📄 공시: 10-K - 차량 인도량 신기록"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 영업이익률 9.6%",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 영업이익률 개선. 제조 효율성 향상 효과",
                    "log_message": "📄 공시: 10-Q - 수익성 개선"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 멕시코 기가팩토리 건설 착수",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-mexico",
                    "source": "sec",
                    "sentiment": None,
                    "content": "멕시코 기가팩토리 건설 공식 착수. 100억 달러 투자",
                    "log_message": "📄 공시: 8-K - 멕시코 공장"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - FSD v12 베타 출시",
                    "filing_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-fsd",
                    "source": "sec",
                    "sentiment": None,
                    "content": "완전자율주행(FSD) v12 베타 버전 북미 시장 출시",
                    "log_message": "📄 공시: 8-K - FSD 업데이트"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 에너지 사업부 분사 검토",
                    "filing_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-energy",
                    "source": "sec",
                    "sentiment": None,
                    "content": "에너지 저장장치 사업부 분사 가능성 검토 중",
                    "log_message": "📄 공시: 8-K - 사업부 분사"
                }
            ],
            "NVDA": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 데이터센터 매출 600% 성장",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "AI 붐으로 데이터센터 부문 매출 전년 대비 600% 급증",
                    "log_message": "📄 공시: 10-K - 데이터센터 매출 급증"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 매출 181억 달러",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 매출 시장 예상치 20% 상회. H100 수요 지속",
                    "log_message": "📄 공시: 10-Q - 실적 서프라이즈"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - H200 칩 대량 생산 시작",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-h200",
                    "source": "sec",
                    "sentiment": None,
                    "content": "차세대 AI 칩 H200 대량 생산 돌입. 성능 70% 향상",
                    "log_message": "📄 공시: 8-K - H200 생산"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 중국 수출 제한 대응 계획",
                    "filing_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-china",
                    "source": "sec",
                    "sentiment": None,
                    "content": "중국 시장용 규제 준수 칩 개발. 성능 제한 버전 출시",
                    "log_message": "📄 공시: 8-K - 중국 대응"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - ARM 인수 철회 후 파트너십",
                    "filing_date": (today - timedelta(days=25)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-arm",
                    "source": "sec",
                    "sentiment": None,
                    "content": "ARM과 20년 라이선스 계약 체결. CPU 설계 협력 강화",
                    "log_message": "📄 공시: 8-K - ARM 파트너십"
                }
            ]
        }
        
        # 기본 공시 템플릿
        default_filings = [
            {
                "form_type": "10-K",
                "title": "Annual Report",
                "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10K",
                "source": "sec",
                "sentiment": None,
                "content": "연간 보고서",
                "log_message": "📄 공시: 10-K - Annual Report"
            },
            {
                "form_type": "10-Q",
                "title": "Quarterly Report",
                "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10Q",
                "source": "sec",
                "sentiment": None,
                "content": "분기 보고서",
                "log_message": "📄 공시: 10-Q - Quarterly Report"
            },
            {
                "form_type": "8-K",
                "title": "Current Report",
                "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/8K",
                "source": "sec",
                "sentiment": None,
                "content": "임시 보고서",
                "log_message": "📄 공시: 8-K - Current Report"
            }
        ]
        
        # 티커에 맞는 공시 선택
        filings_template = ticker_specific_filings.get(ticker, default_filings)
        
        return filings_template[:self.max_filings]
    
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/collect_sec_data", dependencies=[Depends(verify_api_key)])
        async def collect_sec_data(request: SECRequest):
            """HTTP를 통한 SEC 공시 데이터 수집"""
            try:
                print(f"📄 HTTP 요청으로 SEC 공시 수집: {request.ticker}")
                
                # SEC 공시 데이터 수집
                filings_data = await self._fetch_sec_filings(request.ticker)
                
                result = {
                    "data": filings_data,
                    "count": len(filings_data),
                    "source": "sec",
                    "log_message": f"✅ {request.ticker} 공시 {len(filings_data)}개 수집 완료"
                }
                
                # 데이터 수집 완료 이벤트 브로드캐스트
                await self.broadcast_event(
                    event_type="data_collected",
                    event_data={
                        "source": "sec",
                        "ticker": request.ticker,
                        "count": len(filings_data)
                    }
                )
                
                return result
                
            except Exception as e:
                print(f"❌ HTTP SEC 공시 수집 오류: {e}")
                return {
                    "error": str(e),
                    "data": [],
                    "count": 0,
                    "source": "sec"
                }


# 모듈 레벨에서 에이전트와 app 생성
agent = SECAgentV2()
app = agent.app

@app.on_event("startup")
async def startup():
    await agent.start()

@app.on_event("shutdown")
async def shutdown():
    await agent.stop()

# 독립 실행용
if __name__ == "__main__":
    agent.run()