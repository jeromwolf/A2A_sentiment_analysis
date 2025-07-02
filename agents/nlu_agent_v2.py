"""
NLU Agent v2 - A2A 프로토콜 기반

사용자의 자연어 질문을 분석하여 티커를 추출하는 에이전트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class NLUAgentV2(BaseAgent):
    """자연어 이해 에이전트 V2"""
    
    def __init__(self):
        super().__init__(
            name="NLU Agent V2",
            description="자연어 질문을 분석하여 티커를 추출하는 A2A 에이전트",
            port=8108,  # 새로운 포트
            registry_url="http://localhost:8001"
        )
        
        # 기본 티커 매핑
        self.ticker_map = {
            "애플": "AAPL",
            "삼성": "005930.KS",
            "테슬라": "TSLA",
            "엔비디아": "NVDA",
            "구글": "GOOGL",
            "아마존": "AMZN",
            "마이크로소프트": "MSFT",
            "메타": "META",
            "넷플릭스": "NFLX"
        }
        
        # Gemini API 키
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
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
        
        for company, symbol in self.ticker_map.items():
            if company in query.lower():
                ticker = symbol
                company_name = company
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