"""
DART Agent V2 - 한국 기업 공시 수집

한국 금융감독원 DART 시스템에서 공시 데이터를 수집하는 독립적인 V2 에이전트
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
from deep_translator import GoogleTranslator

# 설정 관리자 및 커스텀 에러 임포트
from utils.config_manager import config
from utils.errors import APIRateLimitError, APITimeoutError, DataNotFoundError
from utils.auth import verify_api_key

load_dotenv(override=True)

# 로깅 설정
logger = logging.getLogger(__name__)

# httpx 로그 레벨을 WARNING으로 설정하여 하트비트 로그 숨기기
logging.getLogger("httpx").setLevel(logging.WARNING)


class DARTRequest(BaseModel):
    ticker: str


class DARTAgentV2(BaseAgent):
    """DART 공시 수집 V2 에이전트"""
    
    def __init__(self):
        # 설정에서 에이전트 정보 가져오기
        agent_config = config.get_agent_config("dart")
        
        super().__init__(
            name=agent_config.get("name", "DART Agent V2"),
            description="한국 기업 공시 데이터를 수집하는 A2A 에이전트",
            port=agent_config.get("port", 8213),
            registry_url="http://localhost:8001"
        )
        
        # API 설정
        self.max_filings = int(config.get_env("MAX_DART_FILINGS", "10"))
        self.dart_api_key = config.get_env("DART_API_KEY", "")
        
        if not self.dart_api_key:
            logger.warning("⚠️ DART API 키가 설정되지 않았습니다. RSS 피드만 사용합니다.")
        else:
            logger.info("✅ DART API 키가 설정되었습니다.")
        
        # 타임아웃 설정
        self.timeout = agent_config.get("timeout", 60)
        
        # 더미 데이터 사용 여부
        self.use_mock_data = config.is_mock_data_enabled()
        
        # 한국 기업 매핑 (티커 -> 종목코드)
        self.ticker_mapping = {
            # 주요 한국 기업
            "삼성전자": "005930",
            "SAMSUNG": "005930",
            "005930": "005930",
            "SK하이닉스": "000660",
            "SKHYNIX": "000660",
            "000660": "000660",
            "LG에너지솔루션": "373220",
            "LGES": "373220",
            "373220": "373220",
            "현대차": "005380",
            "현대자동차": "005380",
            "HYUNDAI": "005380",
            "005380": "005380",
            "네이버": "035420",
            "NAVER": "035420",
            "035420": "035420",
            "카카오": "035720",
            "KAKAO": "035720",
            "035720": "035720",
            "셀트리온": "068270",
            "CELLTRION": "068270",
            "068270": "068270",
            "삼성바이오로직스": "207940",
            "207940": "207940",
            "LG화학": "051910",
            "LGCHEM": "051910",
            "051910": "051910",
            "기아": "000270",
            "KIA": "000270",
            "000270": "000270"
        }
        
        # DART 기업 고유번호 매핑 (API 사용시 필요)
        self.corp_code_mapping = {
            "005930": "00126380",  # 삼성전자
            "000660": "00164779",  # SK하이닉스
            "373220": "01459484",  # LG에너지솔루션
            "005380": "00164742",  # 현대차
            "035420": "00813828",  # 네이버
            "035720": "00918012",  # 카카오
            "068270": "00821243",  # 셀트리온
            "051910": "00434003",  # LG화학
            "006400": "00126186",  # 삼성SDI
            "000270": "00164609"   # 기아
        }
        
        # 번역기 설정
        self.translator = GoogleTranslator(source='ko', target='en')
        
        # HTTP 엔드포인트 설정
        self._setup_http_endpoints()
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "dart_data_collection",
            "version": "2.0",
            "description": "한국 기업 DART 공시 데이터 수집",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "종목 코드 또는 회사명"}
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
        
        print("✅ DART Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 DART Agent V2 종료 중...")
        
    def _setup_http_endpoints(self):
        """HTTP API 엔드포인트 설정"""
        @self.app.post("/collect_dart_data", dependencies=[Depends(verify_api_key)])
        async def collect_dart_data(request: DARTRequest):
            """DART 공시 수집 엔드포인트"""
            try:
                logger.info(f"📥 DART 공시 수집 요청: {request.ticker}")
                
                result = await self._collect_dart_data(request.ticker)
                
                logger.info(f"✅ DART 공시 수집 완료: {result['count']}건")
                return result
                
            except Exception as e:
                logger.error(f"❌ DART 공시 수집 오류: {str(e)}")
                return {
                    "data": [],
                    "count": 0,
                    "source": "dart",
                    "error": str(e)
                }
    
    def _get_corp_code(self, ticker: str) -> Optional[str]:
        """티커/회사명으로 종목코드 반환"""
        # 대소문자 구분 없이 매핑
        ticker_upper = ticker.upper()
        
        # 직접 매핑 확인
        if ticker in self.ticker_mapping:
            return self.ticker_mapping[ticker]
        elif ticker_upper in self.ticker_mapping:
            return self.ticker_mapping[ticker_upper]
        
        # 숫자로만 이루어진 경우 (이미 종목코드인 경우)
        if ticker.isdigit() and len(ticker) == 6:
            return ticker
            
        return None
    
    async def _collect_dart_data(self, ticker: str) -> Dict[str, Any]:
        """DART 공시 데이터 수집"""
        
        # 더미 데이터 모드
        if self.use_mock_data:
            logger.info(f"🎭 더미 데이터 모드 활성화 - 모의 DART 공시 반환")
            return self._get_mock_filings(ticker)
        
        try:
            # 종목코드 가져오기
            corp_code = self._get_corp_code(ticker)
            if not corp_code:
                logger.warning(f"⚠️ {ticker}의 종목코드를 찾을 수 없습니다")
                return {
                    "data": [],
                    "count": 0,
                    "source": "dart",
                    "error": f"종목코드를 찾을 수 없습니다: {ticker}"
                }
            
            # DART RSS 피드에서 공시 수집
            filings = await self._fetch_dart_filings(corp_code, ticker)
            
            # 한글 데이터 번역
            translated_filings = await self._translate_filings(filings)
            
            return {
                "data": translated_filings,
                "count": len(translated_filings),
                "source": "dart"
            }
            
        except Exception as e:
            logger.error(f"❌ DART 데이터 수집 오류: {str(e)}")
            return {
                "data": [],
                "count": 0,
                "source": "dart",
                "error": str(e)
            }
    
    async def _fetch_dart_filings(self, corp_code: str, company_name: str) -> List[Dict]:
        """DART API를 사용하여 공시 가져오기"""
        # API 키가 있으면 API 사용, 없으면 RSS 사용
        if self.dart_api_key and corp_code in self.corp_code_mapping:
            return await self._fetch_dart_api_filings(corp_code)
        else:
            return await self._fetch_dart_rss_filings(corp_code, company_name)
    
    async def _fetch_dart_api_filings(self, corp_code: str) -> List[Dict]:
        """DART API를 통해 공시 가져오기"""
        try:
            # 기업 고유번호 가져오기
            dart_corp_code = self.corp_code_mapping.get(corp_code)
            if not dart_corp_code:
                logger.warning(f"종목코드 {corp_code}에 대한 DART 고유번호를 찾을 수 없습니다")
                return []
            
            # DART API URL
            api_url = "https://opendart.fss.or.kr/api/list.json"
            
            # 최근 3개월 데이터 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            params = {
                "crtfc_key": self.dart_api_key,
                "corp_code": dart_corp_code,
                "bgn_de": start_date.strftime("%Y%m%d"),
                "end_de": end_date.strftime("%Y%m%d"),
                "page_no": 1,
                "page_count": self.max_filings
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    api_url,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"DART API 조회 실패: {response.status_code}")
                    return []
                
                data = response.json()
                
                if data.get("status") != "000":
                    logger.error(f"DART API 오류: {data.get('message', 'Unknown error')}")
                    return []
                
                # 공시 목록 파싱
                filings = []
                for item in data.get("list", [])[:self.max_filings]:
                    filing = {
                        "title": f"[{item.get('report_nm', '')}] {item.get('corp_name', '')}",
                        "link": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}",
                        "pubDate": item.get('rcept_dt', ''),
                        "description": item.get('report_nm', ''),
                        "filing_type": item.get('report_nm', ''),
                        "corp_name": item.get('corp_name', ''),
                        "rcept_no": item.get('rcept_no', ''),
                        "sentiment": 0
                    }
                    filings.append(filing)
                
                logger.info(f"✅ DART API에서 {len(filings)}개 공시 수집 완료")
                return filings
                
        except Exception as e:
            logger.error(f"DART API 조회 오류: {e}")
            return []
    
    async def _fetch_dart_rss_filings(self, corp_code: str, company_name: str) -> List[Dict]:
        """DART RSS에서 공시 가져오기 (폴백)"""
        try:
            # DART RSS URL
            rss_url = "https://dart.fss.or.kr/api/todayRSS.xml"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    rss_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"DART RSS 조회 실패: {response.status_code}")
                    return []
                
                # XML 파싱
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                filings = []
                for item in items[:self.max_filings]:  # 최대 개수 제한
                    # 회사명이 포함된 공시만 필터링
                    title = item.find('title').text if item.find('title') else ""
                    
                    # 종목코드 또는 회사명으로 필터링
                    if corp_code in title or company_name in title:
                        filing = {
                            "title": title,
                            "link": item.find('link').text if item.find('link') else "",
                            "pubDate": item.find('pubDate').text if item.find('pubDate') else "",
                            "description": item.find('description').text if item.find('description') else "",
                            "filing_type": self._extract_filing_type(title),
                            "sentiment": 0  # 기본값
                        }
                        filings.append(filing)
                
                # 공시가 없으면 전체 RSS에서 최근 공시 일부 반환
                if not filings:
                    logger.info(f"특정 기업 공시가 없어 전체 최근 공시 반환")
                    for item in items[:5]:  # 최근 5개
                        title = item.find('title').text if item.find('title') else ""
                        filing = {
                            "title": title,
                            "link": item.find('link').text if item.find('link') else "",
                            "pubDate": item.find('pubDate').text if item.find('pubDate') else "",
                            "description": item.find('description').text if item.find('description') else "",
                            "filing_type": self._extract_filing_type(title),
                            "sentiment": 0
                        }
                        filings.append(filing)
                
                return filings
                
        except Exception as e:
            logger.error(f"DART RSS 조회 오류: {str(e)}")
            return []
    
    def _extract_filing_type(self, title: str) -> str:
        """공시 제목에서 공시 유형 추출"""
        if "사업보고서" in title:
            return "사업보고서"
        elif "분기보고서" in title:
            return "분기보고서"
        elif "반기보고서" in title:
            return "반기보고서"
        elif "증권발행" in title:
            return "증권발행"
        elif "주요사항" in title:
            return "주요사항보고서"
        elif "공정공시" in title:
            return "공정공시"
        else:
            return "기타공시"
    
    async def _translate_filings(self, filings: List[Dict]) -> List[Dict]:
        """한글 공시를 영어로 번역"""
        translated = []
        
        for filing in filings:
            try:
                # 제목 번역
                title_en = self.translator.translate(filing['title'])
                
                # 설명 번역 (있는 경우)
                desc_en = ""
                if filing.get('description'):
                    desc_en = self.translator.translate(filing['description'][:200])  # 200자 제한
                
                translated_filing = {
                    "title": filing['title'],
                    "title_en": title_en,
                    "link": filing['link'],
                    "date": filing['pubDate'],
                    "description": filing.get('description', ''),
                    "description_en": desc_en,
                    "filing_type": filing['filing_type'],
                    "sentiment": filing.get('sentiment', 0),
                    "source": "DART"
                }
                
                translated.append(translated_filing)
                
            except Exception as e:
                logger.error(f"번역 오류: {str(e)}")
                # 번역 실패 시 원본 사용
                translated.append({
                    **filing,
                    "title_en": filing['title'],
                    "description_en": filing.get('description', ''),
                    "source": "DART"
                })
        
        return translated
    
    def _get_mock_filings(self, ticker: str) -> Dict[str, Any]:
        """더미 DART 공시 데이터 생성"""
        
        # 회사별 더미 공시
        mock_data = {
            "삼성전자": [
                {
                    "title": "삼성전자 2024년 3분기 실적발표",
                    "title_en": "Samsung Electronics Q3 2024 Earnings Release",
                    "link": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240101000001",
                    "date": datetime.now().isoformat(),
                    "description": "매출 79조원, 영업이익 10.1조원 달성",
                    "description_en": "Revenue 79 trillion won, operating profit 10.1 trillion won",
                    "filing_type": "분기보고서",
                    "sentiment": 0.8,
                    "source": "DART"
                },
                {
                    "title": "삼성전자 AI 반도체 신제품 출시 공시",
                    "title_en": "Samsung Electronics AI Chip New Product Launch Disclosure",
                    "link": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240101000002",
                    "date": datetime.now().isoformat(),
                    "description": "차세대 AI 가속기 HBM4 양산 시작",
                    "description_en": "Next-generation AI accelerator HBM4 mass production begins",
                    "filing_type": "주요사항보고서",
                    "sentiment": 0.9,
                    "source": "DART"
                },
                {
                    "title": "삼성전자 자사주 매입 결정",
                    "title_en": "Samsung Electronics Treasury Stock Purchase Decision",
                    "link": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240101000003",
                    "date": datetime.now().isoformat(),
                    "description": "3조원 규모 자사주 매입 결정",
                    "description_en": "Decision to purchase 3 trillion won worth of treasury stock",
                    "filing_type": "주요사항보고서",
                    "sentiment": 0.7,
                    "source": "DART"
                }
            ],
            "SK하이닉스": [
                {
                    "title": "SK하이닉스 HBM3E 공급계약 체결",
                    "title_en": "SK Hynix HBM3E Supply Contract Signed",
                    "link": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240102000001",
                    "date": datetime.now().isoformat(),
                    "description": "엔비디아와 HBM3E 대량 공급 계약",
                    "description_en": "Large-scale HBM3E supply contract with NVIDIA",
                    "filing_type": "주요사항보고서",
                    "sentiment": 0.9,
                    "source": "DART"
                }
            ]
        }
        
        # 기본값
        company_name = ticker
        for name, code in self.ticker_mapping.items():
            if code == self._get_corp_code(ticker) or name == ticker:
                company_name = name
                break
        
        filings = mock_data.get(company_name, [
            {
                "title": f"{ticker} 정기 공시",
                "title_en": f"{ticker} Regular Disclosure",
                "link": "https://dart.fss.or.kr/dsaf001/main.do",
                "date": datetime.now().isoformat(),
                "description": "정기 공시 내용",
                "description_en": "Regular disclosure content",
                "filing_type": "기타공시",
                "sentiment": 0,
                "source": "DART"
            }
        ])
        
        return {
            "data": filings,
            "count": len(filings),
            "source": "dart"
        }
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            print(f"📩 DART Agent V2 메시지 수신:")
            print(f"   - Type: {message.header.message_type}")
            print(f"   - From: {message.header.sender_id}")
            print(f"   - Message ID: {message.header.message_id}")
            print(f"   - Body: {message.body}")
            
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                print(f"📋 요청된 액션: {action}")
                
                if action == "collect_dart":
                    print("🔍 DART 데이터 수집 요청 처리 시작")
                    payload = message.body.get("payload", {})
                    ticker = payload.get("ticker")
                    
                    if ticker:
                        result = await self._collect_dart_data(ticker)
                        await self.reply_to_message(message, result=result, success=True)
                    else:
                        await self.reply_to_message(
                            message,
                            result={"error": "No ticker provided"},
                            success=False
                        )
                else:
                    # 지원하지 않는 액션
                    print(f"❌ 지원하지 않는 액션: {action}")
                    await self.reply_to_message(
                        message,
                        result={"error": f"Unsupported action: {action}"},
                        success=False
                    )
                    
            elif message.header.message_type == MessageType.EVENT:
                # 이벤트 처리
                event_type = message.body.get("event_type")
                print(f"📨 이벤트 수신: {event_type}")
                
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )


# FastAPI 앱 생성
agent = DARTAgentV2()
app = agent.app


@app.on_event("startup")
async def startup():
    print("🚀 DART Agent V2 시작 중...")
    await agent.start()
    print("✅ DART Agent V2 시작 완료")


@app.on_event("shutdown")
async def shutdown():
    await agent.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=agent.port)