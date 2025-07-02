#!/usr/bin/env python3
"""
Sentiment Analysis Agent V2 - A2A 프로토콜 기반 감정 분석 에이전트
직접 Gemini AI를 사용하여 감정 분석을 수행합니다.
"""

import os
import sys
import asyncio
import httpx
import json
import re
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from fastapi import FastAPI
import uvicorn

# 환경 변수 로드
load_dotenv()

class SentimentAnalysisAgentV2(BaseAgent):
    """감정 분석 A2A 에이전트"""
    
    def __init__(self, name: str = "Sentiment Analysis Agent V2", port: int = 8202):
        super().__init__(
            name=name,
            port=port,
            description="감정 분석을 수행하는 A2A 에이전트"
        )
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        await self.register_capability({
            "name": "sentiment_analysis",
            "version": "2.0",
            "description": "여러 소스의 데이터를 감정 분석",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "data": {"type": "object"}
                },
                "required": ["ticker", "data"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "analyzed_results": {"type": "array"},
                    "success_count": {"type": "number"},
                    "failure_count": {"type": "number"}
                }
            }
        })
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        pass
        
    async def handle_message(self, message: A2AMessage) -> None:
        """A2A 메시지 처리"""
        print(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action')}")
        
        if message.header.message_type != MessageType.REQUEST:
            return
            
        body = message.body
        action = body.get("action")
        
        if action == "analyze_sentiment":
            payload = body.get("payload", {})
            ticker = payload.get("ticker")
            data = payload.get("data", {})
            
            print(f"📊 감정 분석 시작 - 티커: {ticker}")
            print(f"📊 분석할 데이터 소스: {list(data.keys())}")
            
            try:
                # 직접 감정 분석 수행
                result = await self._perform_sentiment_analysis(ticker, data)
                
                # 성공 응답
                print(f"📤 응답 전송 시도 - Sender ID: {message.header.sender_id}")
                await self.reply_to_message(message, result, success=True)
                print(f"✅ 감정 분석 완료 및 응답 전송: {result.get('success_count', 0)}개 성공")
                        
            except Exception as e:
                print(f"❌ 감정 분석 오류: {e}")
                import traceback
                traceback.print_exc()
                
                await self.reply_to_message(
                    message, 
                    {"error": f"분석 중 오류: {str(e)}"}, 
                    success=False
                )
        else:
            await self.reply_to_message(
                message, 
                {"error": f"알 수 없는 액션: {action}"}, 
                success=False
            )
            
    async def _perform_sentiment_analysis(self, ticker: str, data: dict) -> dict:
        """감정 분석 직접 수행"""
        print(f"🔍 감정 분석 시작 - Ticker: {ticker}")
        print(f"📊 받은 데이터 구조: {list(data.keys())}")
        
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않음")
            return {
                "analyzed_results": [],
                "success_count": 0,
                "failure_count": 1,
                "error": "GEMINI_API_KEY not configured"
            }
            
        analyzed_results = []
        
        # 각 소스별 데이터 처리
        for source, items in data.items():
            print(f"🔍 소스 '{source}' 처리 중...")
            print(f"   - 타입: {type(items)}")
            print(f"   - 내용: {items if not isinstance(items, list) else f'{len(items)}개 항목'}")
            
            if not isinstance(items, list):
                print(f"   ⚠️ 리스트가 아님, 건너뜀")
                continue
                
            print(f"📊 {source} 소스 분석 중: {len(items)}개 항목")
                
            for idx, item in enumerate(items):
                print(f"   📝 항목 {idx+1} 처리 중...")
                if isinstance(item, dict):
                    print(f"      - 항목 키: {list(item.keys())}")
                    # 텍스트 내용 추출
                    text_content = ""
                    if "title" in item and item["title"]:
                        text_content += item["title"]
                        print(f"      - title 추가: {item['title'][:30]}...")
                    if "content" in item and item["content"]:
                        text_content += " " + item["content"]
                        print(f"      - content 추가: {item['content'][:30]}...")
                    if "text" in item and item["text"]:
                        text_content += " " + item["text"]
                        print(f"      - text 추가: {item['text'][:30]}...")
                    
                    print(f"      - 최종 텍스트 길이: {len(text_content)}")
                    
                    if not text_content.strip():
                        print("      ⚠️ 텍스트가 비어있음, 건너뜀")
                        continue
                        
                    try:
                        print("      🚀 Gemini API 호출 시작...")
                        # Gemini API 호출
                        sentiment_result = await self._analyze_with_gemini(text_content, source)
                        analyzed_results.append(sentiment_result)
                        print(f"      ✅ 분석 완료: {sentiment_result.get('summary', '')[:50]}...")
                        print(f"      📊 점수: {sentiment_result.get('score', 'N/A')}")
                    except Exception as e:
                        print(f"      ❌ 항목 분석 실패: {e}")
                        import traceback
                        traceback.print_exc()
                        analyzed_results.append({
                            "text": text_content[:100] + "..." if len(text_content) > 100 else text_content,
                            "source": source,
                            "summary": f"분석 실패: {str(e)}",
                            "score": None,
                            "error": str(e)
                        })
        
        success_count = sum(1 for r in analyzed_results if r.get("score") is not None)
        failure_count = len(analyzed_results) - success_count
        
        return {
            "analyzed_results": analyzed_results,
            "success_count": success_count,
            "failure_count": failure_count,
            "log_message": f"✅ {success_count}개 항목 감정 분석 완료"
        }
        
    async def _analyze_with_gemini(self, text: str, source: str) -> dict:
        """Gemini를 사용한 감정 분석"""
        print(f"         🔮 Gemini 분석 시작 - Source: {source}")
        print(f"         📝 텍스트 길이: {len(text)}")
        
        prompt = f"""
다음 {source} 텍스트를 분석해주세요:
"{text}"

다음 JSON 형식으로만 응답하세요:
{{
    "summary": "한줄 요약 (한국어)",
    "score": -1과 1 사이의 감정 점수 (음수: 부정, 양수: 긍정, 0: 중립)
}}
"""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        print(f"         🌐 API URL: {self.gemini_api_url[:50]}...")
        print(f"         📤 요청 전송 중...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.gemini_api_url, json=payload)
                print(f"         📥 응답 수신 - Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"         📄 응답 내용: {str(result)[:200]}...")
                    
                    if 'candidates' in result and result['candidates']:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        
                        # JSON 추출
                        match = re.search(r'\{.*\}', content, re.DOTALL)
                        if match:
                            try:
                                sentiment_data = json.loads(match.group(0))
                                return {
                                    "text": text[:200] + "..." if len(text) > 200 else text,
                                    "source": source,
                                    "summary": sentiment_data.get("summary", "요약 없음"),
                                    "score": float(sentiment_data.get("score", 0))
                                }
                            except json.JSONDecodeError as e:
                                print(f"         ❌ JSON 파싱 오류: {e}")
                                print(f"         📄 원본 내용: {content[:200]}...")
                else:
                    print(f"         ❌ API 오류 - Status: {response.status_code}")
                    print(f"         📄 오류 응답: {response.text[:200]}...")
                    
        except httpx.TimeoutException:
            print("         ⏱️ API 타임아웃 (30초)")
        except Exception as e:
            print(f"         ❌ 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()
            
        # 실패 시 기본값 반환
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "source": source,
            "summary": "분석 실패",
            "score": 0.0
        }

# 에이전트 인스턴스 생성
agent = SentimentAnalysisAgentV2()

# BaseAgent의 app을 사용
app = agent.app

# 추가 엔드포인트
@app.get("/agent/status")
async def agent_status():
    """에이전트 상태"""
    return {
        "name": agent.name,
        "agent_id": agent.agent_id,
        "status": "active",
        "capabilities": agent.capabilities,
        "gemini_configured": bool(agent.gemini_api_key)
    }

# 앱 시작 시 에이전트 시작
@app.on_event("startup")
async def startup():
    print("🚀 Sentiment Analysis Agent V2 시작 중...")
    await agent.start()

# 앱 종료 시 에이전트 정리
@app.on_event("shutdown")
async def shutdown():
    await agent.stop()

if __name__ == "__main__":
    # uvicorn으로 직접 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8202)