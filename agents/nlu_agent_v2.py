"""
NLU Agent v2 - A2A 프로토콜 기반

사용자의 자연어 질문을 분석하여 티커를 추출하는 에이전트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_core.base.base_agent import BaseAgent
from utils.auth import verify_api_key
from utils.cache_manager import cache_manager
from a2a_core.protocols.message import A2AMessage, MessageType
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from pydantic import BaseModel
import httpx

load_dotenv()

class QueryRequest(BaseModel):
    query: str


class NLUAgentV2(BaseAgent):
    """자연어 이해 에이전트 V2"""
    
    def __init__(self):
        super().__init__(
            name="NLU Agent V2",
            description="자연어 질문을 분석하여 티커를 추출하는 A2A 에이전트",
            port=8108,  # V2 전용 포트 사용
            registry_url="http://localhost:8001"
        )
        
        # 미국 기업 매핑
        self.us_ticker_map = {
            "애플": "AAPL",
            "테슬라": "TSLA",
            "엔비디아": "NVDA",
            "구글": "GOOGL",
            "아마존": "AMZN",
            "마이크로소프트": "MSFT",
            "메타": "META",
            "넷플릭스": "NFLX",
            "팔란티어": "PLTR",
            "팔란티르": "PLTR",
            "페이스북": "META",
            "알파벳": "GOOGL",
            "버크셔": "BRK-B",
            "버크셔헤서웨이": "BRK-B",
            "jp모간": "JPM",
            "제이피모간": "JPM",
            "뱅크오브아메리카": "BAC",
            "인텔": "INTC",
            "amd": "AMD",
            "에이엠디": "AMD",
            "오라클": "ORCL",
            "시스코": "CSCO",
            "아도비": "ADBE",
            "세일즈포스": "CRM",
            "코카콜라": "KO",
            "월마트": "WMT",
            "디즈니": "DIS",
            "스타벅스": "SBUX",
            "맥도날드": "MCD",
            "나이키": "NKE",
            "비자": "V",
            "마스터카드": "MA",
            "페이팔": "PYPL",
            "스포티파이": "SPOT",
            "우버": "UBER",
            "에어비앤비": "ABNB"
        }
        
        # 한국 기업 매핑
        self.kr_ticker_map = {
            "삼성전자": "005930",
            "삼성": "005930",
            "samsung": "005930",
            "sk하이닉스": "000660",
            "하이닉스": "000660",
            "skhynix": "000660",
            "lg에너지솔루션": "373220",
            "lg에너지": "373220",
            "lges": "373220",
            "현대차": "005380",
            "현대자동차": "005380",
            "hyundai": "005380",
            "기아": "000270",
            "kia": "000270",
            "네이버": "035420",
            "naver": "035420",
            "카카오": "035720",
            "kakao": "035720",
            "셀트리온": "068270",
            "celltrion": "068270",
            "삼성바이오로직스": "207940",
            "삼성바이오": "207940",
            "lg화학": "051910",
            "lgchem": "051910",
            "포스코": "005490",
            "posco": "005490",
            "kb금융": "105560",
            "국민은행": "105560",
            "신한지주": "055550",
            "신한": "055550",
            "하나금융": "086790",
            "하나": "086790",
            "삼성sds": "018260",
            "lg전자": "066570",
            "lgelec": "066570",
            "sk텔레콤": "017670",
            "skt": "017670",
            "kt": "030200",
            "한국전력": "015760",
            "한전": "015760",
            "kepco": "015760"
        }
        
        # Gemini API 키
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/extract_ticker", dependencies=[Depends(verify_api_key)])
        async def extract_ticker(request: QueryRequest):
            """HTTP 엔드포인트로 티커 추출"""
            query = request.query
            print(f"🔍 HTTP 요청으로 티커 추출: {query}")
            
            # 캐시 확인
            cache_params = {"query": query.lower()}
            cached_result = await cache_manager.get_async("ticker_extraction", cache_params)
            
            if cached_result:
                print(f"💾 캐시에서 티커 반환: {cached_result.get('ticker')}")
                return cached_result
            
            # 간단한 키워드 매칭 먼저 시도
            ticker = None
            company_name = None
            exchange = None
            
            # 미국 기업 확인
            for company, symbol in self.us_ticker_map.items():
                if company in query.lower():
                    ticker = symbol
                    company_name = company
                    exchange = "US"  # NYSE/NASDAQ
                    break
            
            # 한국 기업 확인
            if not ticker:
                for company, symbol in self.kr_ticker_map.items():
                    if company in query.lower():
                        ticker = symbol
                        company_name = company
                        exchange = "KRX"  # 한국거래소
                        break
                    
            if not ticker and self.gemini_api_key:
                # Gemini API를 사용한 고급 분석
                try:
                    prompt = f"""
                    다음 질문에서 언급된 회사의 주식 티커 심볼을 추출해주세요.
                    질문: {query}
                    
                    JSON 형식으로 답변해주세요:
                    {{
                        "ticker": "티커 심볼",
                        "company_name": "회사명",
                        "exchange": "거래소 (US, KRX 등)",
                        "confidence": 0.0~1.0
                    }}
                    
                    티커를 찾을 수 없으면 null을 반환하세요.
                    """
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}",
                            json={
                                "contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {
                                    "temperature": 0.1,
                                    "topK": 1,
                                    "topP": 1,
                                    "maxOutputTokens": 100,
                                }
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            text = result["candidates"][0]["content"]["parts"][0]["text"]
                            
                            # JSON 파싱 시도
                            try:
                                import json
                                parsed = json.loads(text)
                                ticker = parsed.get("ticker")
                                company_name = parsed.get("company_name")
                                exchange = parsed.get("exchange", "US")
                            except:
                                pass
                                
                except Exception as e:
                    print(f"⚠️ Gemini API 오류: {e}")
                    
            # 응답 반환
            if ticker:
                result = {
                    "ticker": ticker,
                    "company_name": company_name or ticker,
                    "exchange": exchange or "US",  # 기본값은 미국
                    "confidence": 0.95,
                    "log_message": f"'{query}'에서 '{ticker}' 종목 분석을 요청한 것으로 이해했습니다."
                }
                # 캐시에 저장
                await cache_manager.set_async("ticker_extraction", cache_params, result)
                return result
            else:
                result = {
                    "ticker": None,
                    "error": "티커를 찾을 수 없습니다",
                    "log_message": "❌ 질문에서 회사명이나 티커를 찾을 수 없습니다."
                }
                # 실패한 결과도 짧은 시간 캐싱 (5분)
                await cache_manager.set_async("ticker_extraction", cache_params, result)
                return result
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "extract_ticker",
            "version": "2.0",
            "description": "자연어 질문에서 주식 티커 추출",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "사용자 질문"}
                },
                "required": ["query"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "company_name": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        })
        
        print("✅ NLU Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 NLU Agent V2 종료 중...")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            print(f"📩 NLU Agent V2 메시지 수신:")
            print(f"   - Type: {message.header.message_type}")
            print(f"   - From: {message.header.sender_id}")
            print(f"   - Message ID: {message.header.message_id}")
            print(f"   - Body: {message.body}")
            
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                print(f"📋 요청된 액션: {action}")
                
                if action == "extract_ticker":
                    print("🔍 티커 추출 요청 처리 시작")
                    await self._handle_extract_ticker(message)
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
            
    async def _handle_extract_ticker(self, message: A2AMessage):
        """티커 추출 요청 처리"""
        payload = message.body.get("payload", {})
        query = payload.get("query", "")
        
        print(f"🔍 질문 분석: {query}")
        print(f"📊 받은 payload: {payload}")
        
        # 간단한 키워드 매칭 먼저 시도
        ticker = None
        company_name = None
        exchange = None
        
        # 미국 기업 확인
        for company, symbol in self.us_ticker_map.items():
            if company in query.lower():
                ticker = symbol
                company_name = company
                exchange = "US"
                break
        
        # 한국 기업 확인
        if not ticker:
            for company, symbol in self.kr_ticker_map.items():
                if company in query.lower():
                    ticker = symbol
                    company_name = company
                    exchange = "KRX"
                    break
                
        if not ticker and self.gemini_api_key:
            # Gemini API를 사용한 고급 분석
            try:
                import httpx
                import json
                
                prompt = f"""
                다음 질문에서 언급된 회사의 주식 티커 심볼을 추출해주세요.
                질문: {query}
                
                JSON 형식으로 답변해주세요:
                {{
                    "ticker": "티커 심볼",
                    "company_name": "회사명",
                    "confidence": 0.0~1.0
                }}
                
                티커를 찾을 수 없으면 null을 반환하세요.
                """
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}",
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "temperature": 0.1,
                                "topK": 1,
                                "topP": 1,
                                "maxOutputTokens": 100,
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # JSON 파싱 시도
                        try:
                            parsed = json.loads(text)
                            ticker = parsed.get("ticker")
                            company_name = parsed.get("company_name")
                        except:
                            pass
                            
            except Exception as e:
                print(f"⚠️ Gemini API 오류: {e}")
                
        # 응답 전송
        if ticker:
            result = {
                "ticker": ticker,
                "company_name": company_name or ticker,
                "exchange": exchange or "US",
                "confidence": 0.95,
                "log_message": f"✅ '{company_name or ticker}' 회사의 티커 '{ticker}'를 추출했습니다."
            }
            print(f"✅ 티커 추출 성공: {ticker}")
            
            # 티커 추출 성공 이벤트 브로드캐스트
            print("📢 티커 추출 이벤트 브로드캐스트 중...")
            await self.broadcast_event(
                event_type="ticker_extracted",
                event_data={
                    "ticker": ticker,
                    "query": query,
                    "extractor": self.agent_id
                }
            )
        else:
            result = {
                "ticker": None,
                "error": "티커를 찾을 수 없습니다",
                "log_message": "❌ 질문에서 회사명이나 티커를 찾을 수 없습니다."
            }
            print("❌ 티커를 찾을 수 없음")
            
        print(f"📤 응답 전송 중: {result}")
        await self.reply_to_message(message, result=result, success=bool(ticker))
        print("✅ 응답 전송 완료")


# 모듈 레벨에서 에이전트와 app 생성
agent = NLUAgentV2()
app = agent.app  # uvicorn이 찾을 수 있도록 app 객체 노출


@app.on_event("startup")
async def startup():
    await agent.start()


@app.on_event("shutdown")
async def shutdown():
    await agent.stop()


# 독립 실행용
if __name__ == "__main__":
    agent.run()