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
import pandas as pd
from io import StringIO

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
        self.filing_cache = {}  # 공시 비교를 위한 캐시
        
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
                
                if action == "sec_data_collection" or action == "collect_data":
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
                elif form_type == "13F-HR" or form_type == "13F":
                    # 기관투자자 보유 주식 현황
                    extracted_info.update(await self._extract_13f_info_enhanced(text_content, filing_url))
                elif form_type == "4":
                    # Form 4 내부자 거래 보고서
                    extracted_info.update(await self._extract_form4_info_enhanced(text_content))
                
                # 10-K, 10-Q에 대해 재무 테이블 파싱 시도
                if form_type in ["10-K", "10-Q"]:
                    financial_table_info = await self._extract_financial_tables(content, form_type)
                    extracted_info.update(financial_table_info)
                    
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
    
    async def _extract_13f_info_enhanced(self, text: str, filing_url: str) -> Dict[str, Any]:
        """13F-HR 기관투자자 보유 현황에서 상세 정보 추출 및 번역"""
        info = {
            "institution_name": "",
            "institution_name_translated": "",
            "total_value": 0,
            "total_value_translated": "",
            "top_holdings": [],
            "top_holdings_translated": [],
            "position_changes": [],
            "position_changes_translated": [],
            "portfolio_insights": "",
            "portfolio_insights_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        
        # 1. 기관 이름 추출
        institution_pattern = re.search(
            r"(?:filed by|reporting person|manager).*?(?:name|entity).*?([A-Z][A-Za-z\s&,.\-]+(?:LLC|LP|Inc|Corp|Company|Partners|Capital|Management|Advisors))",
            text[:2000], re.IGNORECASE
        )
        if institution_pattern:
            info["institution_name"] = institution_pattern.group(1).strip()
            info["institution_name_translated"] = await translate_text(info["institution_name"], "ko")
        
        # 2. 총 포트폴리오 가치 추출
        value_pattern = re.search(
            r"(?:total value|aggregate value|market value).*?\$?([\d,]+(?:\.\d+)?)\s*(?:thousand|million|billion)?",
            text, re.IGNORECASE
        )
        if value_pattern:
            value_str = value_pattern.group(1).replace(',', '')
            multiplier = 1
            if "billion" in value_pattern.group(0).lower():
                multiplier = 1000000000
            elif "million" in value_pattern.group(0).lower():
                multiplier = 1000000
            elif "thousand" in value_pattern.group(0).lower():
                multiplier = 1000
            
            info["total_value"] = float(value_str) * multiplier
            info["total_value_translated"] = f"총 운용자산: ${info['total_value']:,.0f}"
        
        # 3. 주요 보유 종목 추출 (상위 10개)
        # 13F는 주로 테이블 형식이므로 간단한 패턴 매칭
        holdings_pattern = re.findall(
            r"([A-Z]{2,5})\s+(?:COM|COMMON|ORD).*?([\d,]+)\s+(?:SH|SHARES).*?\$?([\d,]+(?:\.\d+)?)",
            text[:20000], re.IGNORECASE
        )
        
        for i, (ticker, shares, value) in enumerate(holdings_pattern[:10]):
            shares_num = int(shares.replace(',', ''))
            value_num = float(value.replace(',', ''))
            
            holding_en = f"{ticker}: {shares_num:,} shares (${value_num:,.0f})"
            holding_ko = f"{ticker}: {shares_num:,}주 (${value_num:,.0f})"
            
            info["top_holdings"].append(holding_en)
            info["top_holdings_translated"].append(holding_ko)
        
        # 4. 포지션 변경사항 분석
        # NEW, INCREASED, DECREASED, SOLD OUT 키워드 찾기
        new_positions = re.findall(r"NEW\s+POSITION.*?([A-Z]{2,5})", text, re.IGNORECASE)
        increased = re.findall(r"INCREASED.*?([A-Z]{2,5})", text, re.IGNORECASE)
        decreased = re.findall(r"DECREASED.*?([A-Z]{2,5})", text, re.IGNORECASE)
        sold_out = re.findall(r"SOLD\s+OUT.*?([A-Z]{2,5})", text, re.IGNORECASE)
        
        if new_positions:
            change_en = f"New positions: {', '.join(new_positions[:5])}"
            change_ko = f"신규 매수: {', '.join(new_positions[:5])}"
            info["position_changes"].append(change_en)
            info["position_changes_translated"].append(change_ko)
            
        if increased:
            change_en = f"Increased positions: {', '.join(increased[:5])}"
            change_ko = f"비중 확대: {', '.join(increased[:5])}"
            info["position_changes"].append(change_en)
            info["position_changes_translated"].append(change_ko)
            
        if decreased:
            change_en = f"Reduced positions: {', '.join(decreased[:5])}"
            change_ko = f"비중 축소: {', '.join(decreased[:5])}"
            info["position_changes"].append(change_en)
            info["position_changes_translated"].append(change_ko)
            
        if sold_out:
            change_en = f"Sold out: {', '.join(sold_out[:5])}"
            change_ko = f"전량 매도: {', '.join(sold_out[:5])}"
            info["position_changes"].append(change_en)
            info["position_changes_translated"].append(change_ko)
        
        # 5. 포트폴리오 인사이트 생성
        if info["top_holdings"]:
            top_3_tickers = [h.split(':')[0] for h in info["top_holdings"][:3]]
            insight_en = f"Top holdings include {', '.join(top_3_tickers)}. "
            
            if new_positions:
                insight_en += f"Notable new positions in {', '.join(new_positions[:3])}. "
            
            sector_keywords = ["TECH", "FINANCE", "HEALTHCARE", "ENERGY", "CONSUMER"]
            dominant_sector = None
            for sector in sector_keywords:
                if text.count(sector) > 5:
                    dominant_sector = sector
                    break
            
            if dominant_sector:
                insight_en += f"Portfolio shows concentration in {dominant_sector} sector."
            
            info["portfolio_insights"] = insight_en
            info["portfolio_insights_translated"] = await translate_text(insight_en, "ko")
        
        return info
    
    async def _extract_form4_info_enhanced(self, text: str) -> Dict[str, Any]:
        """Form 4 내부자 거래 보고서에서 상세 정보 추출 및 번역"""
        info = {
            "reporting_person": "",
            "reporting_person_translated": "",
            "person_title": "",
            "person_title_translated": "",
            "transaction_date": "",
            "transactions": [],
            "transactions_translated": [],
            "total_shares_owned": 0,
            "total_value_owned": 0,
            "ownership_percentage": 0,
            "insider_sentiment": "",
            "insider_sentiment_translated": "",
            "transaction_summary": "",
            "transaction_summary_translated": ""
        }
        
        # 텍스트 정리
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        
        # 1. 보고자 정보 추출
        reporter_pattern = re.search(
            r"(?:reporting person|name).*?([A-Z][a-zA-Z\s,.']+)(?=\s+(?:title|director|officer|CEO|CFO|CTO|President|VP|Chief))",
            text[:3000], re.IGNORECASE
        )
        if reporter_pattern:
            info["reporting_person"] = reporter_pattern.group(1).strip()
            info["reporting_person_translated"] = await translate_text(info["reporting_person"], "ko")
        
        # 2. 직책 추출
        title_pattern = re.search(
            r"(?:title|relationship).*?((?:CEO|CFO|CTO|COO|President|Vice President|VP|Director|Chief [A-Za-z]+ Officer|Executive [A-Za-z]+|Senior [A-Za-z]+)[^,.\n]*)",
            text[:3000], re.IGNORECASE
        )
        if title_pattern:
            info["person_title"] = title_pattern.group(1).strip()
            info["person_title_translated"] = await translate_text(info["person_title"], "ko")
        
        # 3. 거래 날짜 추출
        date_pattern = re.search(
            r"(?:transaction date|date of transaction).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            text, re.IGNORECASE
        )
        if date_pattern:
            info["transaction_date"] = date_pattern.group(1)
        
        # 4. 거래 내역 추출
        # Table I - 비파생 증권 거래
        transaction_patterns = re.findall(
            r"(?:acquired|disposed|purchase|sale|grant|exercise).*?(\d+[\d,]*)\s*(?:shares?|stock).*?(?:price|@).*?\$?([\d.]+)",
            text[:10000], re.IGNORECASE
        )
        
        total_acquired = 0
        total_disposed = 0
        
        for i, match in enumerate(transaction_patterns[:10]):  # 최대 10개 거래
            shares_str = match[0].replace(',', '')
            shares = int(shares_str)
            price = float(match[1])
            
            # 거래 유형 판단
            context = text[max(0, text.find(match[0])-50):text.find(match[0])+100]
            
            if any(word in context.lower() for word in ['acquired', 'purchase', 'grant', 'exercise']):
                transaction_type = "매수"
                transaction_type_en = "Acquired"
                total_acquired += shares
            else:
                transaction_type = "매도"
                transaction_type_en = "Disposed"
                total_disposed += shares
            
            # 거래 코드 추출
            code_match = re.search(r"code[:\s]*([A-Z])", context, re.IGNORECASE)
            transaction_code = code_match.group(1) if code_match else ""
            
            # 거래 코드 설명
            code_descriptions = {
                "P": "공개시장 매수 (Open Market Purchase)",
                "S": "공개시장 매도 (Open Market Sale)",
                "A": "수여/보상 (Grant/Award)",
                "M": "옵션 행사 (Option Exercise)",
                "F": "세금 납부용 주식 처분 (Tax Withholding)",
                "D": "기타 처분 (Disposition)",
                "G": "증여 (Gift)"
            }
            
            code_desc = code_descriptions.get(transaction_code, "기타 거래")
            
            transaction_en = f"{transaction_type_en} {shares:,} shares at ${price:.2f} (Code: {transaction_code})"
            transaction_ko = f"{transaction_type} {shares:,}주 @ ${price:.2f} ({code_desc})"
            
            info["transactions"].append(transaction_en)
            info["transactions_translated"].append(transaction_ko)
        
        # 5. 거래 후 보유 주식 수 추출
        ownership_pattern = re.search(
            r"(?:owned following|shares beneficially owned|total).*?(\d+[\d,]*)\s*(?:shares?|stock)",
            text, re.IGNORECASE
        )
        if ownership_pattern:
            info["total_shares_owned"] = int(ownership_pattern.group(1).replace(',', ''))
            
            # 현재 주가로 보유 가치 추정 (실제로는 주가 데이터 필요)
            if transaction_patterns and len(transaction_patterns) > 0:
                last_price = float(transaction_patterns[-1][1])
                info["total_value_owned"] = info["total_shares_owned"] * last_price
        
        # 6. 소유 비율 추출
        percentage_pattern = re.search(
            r"(?:ownership|percent|%).*?([\d.]+)\s*%",
            text, re.IGNORECASE
        )
        if percentage_pattern:
            info["ownership_percentage"] = float(percentage_pattern.group(1))
        
        # 7. 내부자 센티먼트 분석
        if total_acquired > total_disposed:
            sentiment_ratio = (total_acquired - total_disposed) / (total_acquired + total_disposed) if (total_acquired + total_disposed) > 0 else 0
            if sentiment_ratio > 0.5:
                info["insider_sentiment"] = "Strong Buy Signal"
                info["insider_sentiment_translated"] = "강력한 매수 신호"
            else:
                info["insider_sentiment"] = "Moderate Buy Signal"
                info["insider_sentiment_translated"] = "보통 매수 신호"
        elif total_disposed > total_acquired:
            sentiment_ratio = (total_disposed - total_acquired) / (total_acquired + total_disposed) if (total_acquired + total_disposed) > 0 else 0
            if sentiment_ratio > 0.5:
                info["insider_sentiment"] = "Strong Sell Signal"
                info["insider_sentiment_translated"] = "강력한 매도 신호"
            else:
                info["insider_sentiment"] = "Moderate Sell Signal"
                info["insider_sentiment_translated"] = "보통 매도 신호"
        else:
            info["insider_sentiment"] = "Neutral"
            info["insider_sentiment_translated"] = "중립"
        
        # 8. 거래 요약 생성
        if info["reporting_person"] and info["transactions"]:
            summary_en = f"{info['reporting_person']} ({info['person_title']}) "
            
            if total_acquired > 0:
                summary_en += f"acquired {total_acquired:,} shares"
            if total_disposed > 0:
                if total_acquired > 0:
                    summary_en += " and "
                summary_en += f"disposed {total_disposed:,} shares"
            
            summary_en += f". Now owns {info['total_shares_owned']:,} shares"
            if info['ownership_percentage'] > 0:
                summary_en += f" ({info['ownership_percentage']:.2f}% ownership)"
            
            info["transaction_summary"] = summary_en
            info["transaction_summary_translated"] = await translate_text(summary_en, "ko")
        
        return info
    
    async def _extract_financial_tables(self, text: str, form_type: str) -> Dict[str, Any]:
        """재무제표 테이블 추출 및 구조화"""
        info = {
            "financial_statements": {},
            "financial_statements_translated": {},
            "key_ratios": {},
            "key_ratios_translated": {},
            "year_over_year_changes": {},
            "quarter_over_quarter_changes": {},
            "financial_highlights": "",
            "financial_highlights_translated": ""
        }
        
        # HTML 콘텐츠인지 확인
        soup = BeautifulSoup(text, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            # 텍스트 기반 재무 데이터 추출 시도
            return await self._extract_financial_data_from_text(text, form_type)
        
        # 재무제표 타입 식별 패턴
        statement_patterns = {
            "income_statement": [
                "income statement", "statement of income", "statement of operations",
                "statement of earnings", "consolidated statements of income"
            ],
            "balance_sheet": [
                "balance sheet", "statement of financial position",
                "consolidated balance sheets"
            ],
            "cash_flow": [
                "cash flow", "statement of cash flows", "cash flows statement"
            ]
        }
        
        for table in tables[:10]:  # 최대 10개 테이블 검사
            # 테이블 텍스트 추출
            table_text = table.get_text().lower()
            
            # 재무제표 타입 식별
            statement_type = None
            for stmt_type, patterns in statement_patterns.items():
                if any(pattern in table_text for pattern in patterns):
                    statement_type = stmt_type
                    break
            
            if not statement_type:
                continue
            
            try:
                # pandas로 테이블 파싱
                df = pd.read_html(StringIO(str(table)))[0]
                
                # 데이터 정리 및 숫자 변환
                df = self._clean_financial_dataframe(df)
                
                # 재무제표 저장
                info["financial_statements"][statement_type] = df.to_dict('records')
                
                # 주요 항목 추출 및 번역
                if statement_type == "income_statement":
                    await self._extract_income_statement_items(df, info)
                elif statement_type == "balance_sheet":
                    await self._extract_balance_sheet_items(df, info)
                elif statement_type == "cash_flow":
                    await self._extract_cash_flow_items(df, info)
                    
            except Exception as e:
                logger.warning(f"테이블 파싱 오류: {str(e)}")
                continue
        
        # 재무 비율 계산
        if info["financial_statements"]:
            self._calculate_financial_ratios(info)
        
        # 재무 하이라이트 생성
        if info["key_ratios"]:
            highlights = self._generate_financial_highlights(info)
            info["financial_highlights"] = highlights
            info["financial_highlights_translated"] = await translate_text(highlights, "ko")
        
        return info
    
    def _clean_financial_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """재무 데이터프레임 정리 및 숫자 변환"""
        # 열 이름 정리
        df.columns = [str(col).strip() for col in df.columns]
        
        # 숫자 변환 함수
        def convert_to_number(value):
            if pd.isna(value) or value == '-' or value == '—':
                return 0
            
            # 문자열로 변환
            val_str = str(value).strip()
            
            # 괄호 제거 (음수 표시)
            is_negative = False
            if val_str.startswith('(') and val_str.endswith(')'):
                is_negative = True
                val_str = val_str[1:-1]
            
            # 특수 문자 제거
            val_str = val_str.replace('$', '').replace(',', '').replace('%', '')
            
            try:
                number = float(val_str)
                return -number if is_negative else number
            except:
                return 0
        
        # 숫자 열 변환
        for col in df.columns[1:]:  # 첫 번째 열은 보통 항목명
            df[col] = df[col].apply(convert_to_number)
        
        return df
    
    async def _extract_income_statement_items(self, df: pd.DataFrame, info: Dict[str, Any]):
        """손익계산서 주요 항목 추출"""
        # 주요 항목 매핑
        key_items = {
            "revenue": ["revenue", "net revenue", "total revenue", "net sales"],
            "gross_profit": ["gross profit", "gross margin"],
            "operating_income": ["operating income", "income from operations"],
            "net_income": ["net income", "net earnings"],
            "eps": ["earnings per share", "eps", "diluted eps"]
        }
        
        extracted_items = {}
        
        for item_name, patterns in key_items.items():
            for idx, row in df.iterrows():
                row_text = str(row[0]).lower()
                if any(pattern in row_text for pattern in patterns):
                    # 최신 데이터 (보통 마지막 열)
                    if len(df.columns) > 1:
                        value = row[df.columns[-1]]
                        extracted_items[item_name] = value
                        
                        # 전년 대비 변화율 계산
                        if len(df.columns) > 2:
                            prev_value = row[df.columns[-2]]
                            if prev_value != 0:
                                change = ((value - prev_value) / abs(prev_value)) * 100
                                info["year_over_year_changes"][item_name] = f"{change:.1f}%"
        
        # 한국어 번역
        item_translations = {
            "revenue": "매출",
            "gross_profit": "매출총이익",
            "operating_income": "영업이익",
            "net_income": "순이익",
            "eps": "주당순이익"
        }
        
        for key, value in extracted_items.items():
            korean_name = item_translations.get(key, key)
            info["financial_statements_translated"][f"{korean_name}"] = f"${value:,.0f}"
        
        # 재무 비율 계산용 데이터 저장
        info["income_statement_data"] = extracted_items
    
    async def _extract_balance_sheet_items(self, df: pd.DataFrame, info: Dict[str, Any]):
        """대차대조표 주요 항목 추출"""
        key_items = {
            "total_assets": ["total assets"],
            "current_assets": ["current assets", "total current assets"],
            "total_liabilities": ["total liabilities"],
            "current_liabilities": ["current liabilities", "total current liabilities"],
            "shareholders_equity": ["shareholders' equity", "stockholders' equity", "total equity"]
        }
        
        extracted_items = {}
        
        for item_name, patterns in key_items.items():
            for idx, row in df.iterrows():
                row_text = str(row[0]).lower()
                if any(pattern in row_text for pattern in patterns):
                    if len(df.columns) > 1:
                        value = row[df.columns[-1]]
                        extracted_items[item_name] = value
        
        # 재무 비율용 데이터 저장
        info["balance_sheet_data"] = extracted_items
    
    async def _extract_cash_flow_items(self, df: pd.DataFrame, info: Dict[str, Any]):
        """현금흐름표 주요 항목 추출"""
        key_items = {
            "operating_cash_flow": ["cash from operating", "net cash provided by operating"],
            "investing_cash_flow": ["cash from investing", "net cash used in investing"],
            "financing_cash_flow": ["cash from financing", "net cash used in financing"],
            "free_cash_flow": ["free cash flow"]
        }
        
        extracted_items = {}
        
        for item_name, patterns in key_items.items():
            for idx, row in df.iterrows():
                row_text = str(row[0]).lower()
                if any(pattern in row_text for pattern in patterns):
                    if len(df.columns) > 1:
                        value = row[df.columns[-1]]
                        extracted_items[item_name] = value
        
        # 잉여현금흐름 계산 (영업현금흐름 - 투자현금흐름)
        if "operating_cash_flow" in extracted_items and "investing_cash_flow" not in extracted_items:
            # 투자현금흐름이 없으면 CAPEX 찾기
            for idx, row in df.iterrows():
                if "capital expenditure" in str(row[0]).lower() or "capex" in str(row[0]).lower():
                    if len(df.columns) > 1:
                        capex = abs(row[df.columns[-1]])
                        extracted_items["free_cash_flow"] = extracted_items["operating_cash_flow"] - capex
    
    def _calculate_financial_ratios(self, info: Dict[str, Any]):
        """주요 재무 비율 계산"""
        ratios = {}
        
        # 수익성 비율
        if "income_statement" in info["financial_statements"]:
            income_data = info.get("income_statement_data", {})
            if income_data.get("revenue") and income_data.get("net_income"):
                ratios["net_margin"] = (income_data["net_income"] / income_data["revenue"]) * 100
                info["key_ratios"]["net_margin"] = f"{ratios['net_margin']:.1f}%"
                info["key_ratios_translated"]["순이익률"] = f"{ratios['net_margin']:.1f}%"
        
        # 유동성 비율
        if "balance_sheet_data" in info:
            bs_data = info["balance_sheet_data"]
            if bs_data.get("current_assets") and bs_data.get("current_liabilities"):
                current_ratio = bs_data["current_assets"] / bs_data["current_liabilities"]
                info["key_ratios"]["current_ratio"] = f"{current_ratio:.2f}"
                info["key_ratios_translated"]["유동비율"] = f"{current_ratio:.2f}"
            
            # 부채비율
            if bs_data.get("total_liabilities") and bs_data.get("shareholders_equity"):
                debt_to_equity = bs_data["total_liabilities"] / bs_data["shareholders_equity"]
                info["key_ratios"]["debt_to_equity"] = f"{debt_to_equity:.2f}"
                info["key_ratios_translated"]["부채비율"] = f"{debt_to_equity:.2f}"
    
    def _generate_financial_highlights(self, info: Dict[str, Any]) -> str:
        """재무 하이라이트 생성"""
        highlights = []
        
        if info.get("year_over_year_changes"):
            for item, change in info["year_over_year_changes"].items():
                highlights.append(f"{item} YoY change: {change}")
        
        if info.get("key_ratios"):
            for ratio, value in info["key_ratios"].items():
                highlights.append(f"{ratio}: {value}")
        
        return ". ".join(highlights[:5])  # 상위 5개만
    
    async def _extract_financial_data_from_text(self, text: str, form_type: str) -> Dict[str, Any]:
        """텍스트에서 재무 데이터 추출 (테이블이 없는 경우)"""
        info = {
            "financial_data_text": [],
            "financial_data_text_translated": []
        }
        
        # 재무 데이터 패턴
        financial_patterns = [
            (r"revenue.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)", "Revenue"),
            (r"net income.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)", "Net Income"),
            (r"earnings per.*?\$?([\d.]+)", "EPS"),
            (r"total assets.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)", "Total Assets"),
            (r"cash and cash equivalents.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)", "Cash")
        ]
        
        for pattern, label in financial_patterns:
            match = re.search(pattern, text[:50000], re.IGNORECASE)
            if match:
                value = match.group(1)
                unit = "billion" if "billion" in match.group(0).lower() else "million"
                
                data_en = f"{label}: ${value} {unit}"
                data_ko = await translate_text(data_en, "ko")
                
                info["financial_data_text"].append(data_en)
                info["financial_data_text_translated"].append(data_ko)
        
        return info
    
    async def _compare_filings(self, ticker: str, current_filing: Dict[str, Any], 
                              filing_type: str) -> Dict[str, Any]:
        """이전 공시와 비교 분석"""
        comparison = {
            "comparison_available": False,
            "previous_filing_date": "",
            "key_changes": [],
            "key_changes_translated": [],
            "metric_changes": {},
            "metric_changes_translated": {},
            "new_risks": [],
            "removed_risks": [],
            "trend_analysis": "",
            "trend_analysis_translated": ""
        }
        
        try:
            # 캐시에서 이전 공시 찾기 (간단한 메모리 캐시)
            cache_key = f"{ticker}_{filing_type}_previous"
            if hasattr(self, 'filing_cache') and cache_key in self.filing_cache:
                previous_filing = self.filing_cache[cache_key]
                comparison["comparison_available"] = True
                comparison["previous_filing_date"] = previous_filing.get("filing_date", "")
                
                # 이전 current를 previous로 이동
                self.filing_cache[cache_key] = previous_filing
                
                # 현재 공시 캐시에 저장
                current_cache_key = f"{ticker}_{filing_type}_current"
                self.filing_cache[current_cache_key] = current_filing
                
                # 주요 지표 비교
                await self._compare_metrics(current_filing, previous_filing, comparison)
                
                # 리스크 요인 비교
                self._compare_risks(current_filing, previous_filing, comparison)
                
                # 트렌드 분석
                trend = await self._analyze_filing_trend(current_filing, previous_filing, filing_type)
                comparison["trend_analysis"] = trend
                comparison["trend_analysis_translated"] = await translate_text(trend, "ko")
                
            else:
                # 캐시가 없으면 초기화
                if not hasattr(self, 'filing_cache'):
                    self.filing_cache = {}
                
                # 현재 공시를 current로 저장 (다음에는 previous가 됨)
                current_key = f"{ticker}_{filing_type}_current"
                if current_key in self.filing_cache:
                    # 기존 current를 previous로 이동
                    self.filing_cache[cache_key] = self.filing_cache[current_key]
                
                # 현재 공시를 캐시에 저장
                self.filing_cache[current_key] = current_filing
                
        except Exception as e:
            logger.warning(f"공시 비교 분석 오류: {str(e)}")
        
        return comparison
    
    async def _compare_metrics(self, current: Dict[str, Any], previous: Dict[str, Any], 
                              comparison: Dict[str, Any]):
        """주요 지표 비교"""
        current_info = current.get("extracted_info", {})
        previous_info = previous.get("extracted_info", {})
        
        # 재무 데이터 비교
        current_financial = current_info.get("financial_data", {})
        previous_financial = previous_info.get("financial_data", {})
        
        metrics_to_compare = ["revenue", "net_income", "total_assets"]
        
        for metric in metrics_to_compare:
            if metric in current_financial and metric in previous_financial:
                current_val = current_financial[metric]
                previous_val = previous_financial[metric]
                
                if previous_val != 0:
                    change_pct = ((current_val - previous_val) / previous_val) * 100
                    
                    change_desc_en = f"{metric}: {change_pct:+.1f}% change"
                    change_desc_ko = await translate_text(change_desc_en, "ko")
                    
                    comparison["metric_changes"][metric] = {
                        "current": current_val,
                        "previous": previous_val,
                        "change_percent": change_pct
                    }
                    comparison["metric_changes_translated"][metric] = change_desc_ko
                    
                    # 중요한 변화 식별
                    if abs(change_pct) > 10:
                        significance = "significant increase" if change_pct > 0 else "significant decrease"
                        key_change_en = f"{metric} showed {significance} of {abs(change_pct):.1f}%"
                        key_change_ko = await translate_text(key_change_en, "ko")
                        
                        comparison["key_changes"].append(key_change_en)
                        comparison["key_changes_translated"].append(key_change_ko)
    
    def _compare_risks(self, current: Dict[str, Any], previous: Dict[str, Any], 
                      comparison: Dict[str, Any]):
        """리스크 요인 비교"""
        current_info = current.get("extracted_info", {})
        previous_info = previous.get("extracted_info", {})
        
        current_risks = set(current_info.get("risks", []))
        previous_risks = set(previous_info.get("risks", []))
        
        # 새로운 리스크
        new_risks = current_risks - previous_risks
        if new_risks:
            comparison["new_risks"] = list(new_risks)
        
        # 제거된 리스크
        removed_risks = previous_risks - current_risks
        if removed_risks:
            comparison["removed_risks"] = list(removed_risks)
    
    async def _analyze_filing_trend(self, current: Dict[str, Any], previous: Dict[str, Any], 
                                   filing_type: str) -> str:
        """공시 트렌드 분석"""
        trends = []
        
        # 매출 트렌드
        current_revenue = current.get("extracted_info", {}).get("financial_data", {}).get("revenue", 0)
        previous_revenue = previous.get("extracted_info", {}).get("financial_data", {}).get("revenue", 0)
        
        if current_revenue and previous_revenue:
            revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
            if revenue_growth > 5:
                trends.append("Revenue growth momentum continues")
            elif revenue_growth < -5:
                trends.append("Revenue decline needs attention")
            else:
                trends.append("Revenue remains stable")
        
        # 수익성 트렌드
        current_margin = current.get("extracted_info", {}).get("key_ratios", {}).get("net_margin")
        previous_margin = previous.get("extracted_info", {}).get("key_ratios", {}).get("net_margin")
        
        if current_margin and previous_margin:
            current_margin_val = float(current_margin.replace('%', ''))
            previous_margin_val = float(previous_margin.replace('%', ''))
            
            if current_margin_val > previous_margin_val:
                trends.append("Profitability improving")
            elif current_margin_val < previous_margin_val:
                trends.append("Margin pressure observed")
        
        # Form 4 내부자 거래 트렌드
        if filing_type == "4":
            current_sentiment = current.get("extracted_info", {}).get("insider_sentiment", "")
            if "Buy" in current_sentiment:
                trends.append("Insider confidence indicated by purchases")
            elif "Sell" in current_sentiment:
                trends.append("Insider selling activity noted")
        
        return ". ".join(trends) if trends else "No significant trends identified"
    
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
                                
                            # Form 4 내부자 거래 정보
                            if extracted_info.get("transaction_summary_translated"):
                                content += f" 내부자 거래: {extracted_info['transaction_summary_translated']}"
                                if extracted_info.get("insider_sentiment_translated"):
                                    content += f" ({extracted_info['insider_sentiment_translated']})"
                            
                            # 재무 테이블 정보
                            if extracted_info.get("financial_highlights_translated"):
                                content += f" 재무 하이라이트: {extracted_info['financial_highlights_translated']}"
                            elif extracted_info.get("financial_data_text_translated"):
                                content += f" 재무 데이터: {', '.join(extracted_info['financial_data_text_translated'][:3])}"
                        
                        filing_data = {
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
                        }
                        
                        # 비교 분석 수행 (10-K, 10-Q, 4 폼에 대해)
                        if form_type in ["10-K", "10-Q", "4"] and extracted_info:
                            comparison = await self._compare_filings(ticker, filing_data, form_type)
                            filing_data["comparison"] = comparison
                            
                            # 비교 정보를 content에 추가
                            if comparison.get("comparison_available") and comparison.get("key_changes_translated"):
                                content += f" 이전 대비 주요 변화: {', '.join(comparison['key_changes_translated'][:2])}"
                                filing_data["content"] = content
                        
                        formatted_filings.append(filing_data)
                        
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
                },
                {
                    "form_type": "4",
                    "title": "Form 4 - Tim Cook CEO 주식 50만주 매도",
                    "filing_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/Form4-cook",
                    "source": "sec",
                    "sentiment": None,
                    "content": "내부자 거래: Tim Cook (CEO) 50만주 매도 @ $195.50. 세금 납부 목적. 잔여 보유: 330만주 (보통 매도 신호)",
                    "log_message": "📄 공시: Form 4 - CEO 주식 매도"
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
                },
                {
                    "form_type": "4",
                    "title": "Form 4 - Elon Musk 주식 200만주 매수",
                    "filing_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/Form4-musk",
                    "source": "sec",
                    "sentiment": None,
                    "content": "내부자 거래: Elon Musk (CEO) 200만주 매수 @ $175.25. 공개시장 매수. 총 보유: 4억 1,200만주 (20.6%) (강력한 매수 신호)",
                    "log_message": "📄 공시: Form 4 - CEO 대량 매수"
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