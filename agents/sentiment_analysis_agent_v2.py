#!/usr/bin/env python3
"""
Sentiment Analysis Agent V2 - A2A 프로토콜 기반 감정 분석 에이전트
설정 가능한 LLM을 사용하여 감정 분석을 수행합니다.
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
from pydantic import BaseModel
import uvicorn
from utils.llm_manager import get_llm_manager

# 환경 변수 로드
load_dotenv(override=True)

class SentimentRequest(BaseModel):
    ticker: str
    data: Dict[str, List[Dict[str, Any]]]

class SentimentAnalysisAgentV2(BaseAgent):
    """감정 분석 A2A 에이전트"""
    
    def __init__(self, name: str = "Sentiment Analysis Agent V2", port: int = 8202):
        super().__init__(
            name=name,
            port=port,
            description="감정 분석을 수행하는 A2A 에이전트"
        )
        # LLM Manager 초기화
        self.llm_manager = get_llm_manager()
        llm_info = self.llm_manager.get_provider_info()
        print(f"🤖 LLM 제공자: {llm_info['provider']} (사용 가능: {llm_info['available']})")
        
        # Gemini API (레거시 - 직접 API 호출이 필요한 경우)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/analyze_sentiment")
        async def analyze_sentiment(request: SentimentRequest):
            """HTTP 엔드포인트로 감정 분석"""
            ticker = request.ticker
            data = request.data
            
            print(f"🎯 HTTP 요청으로 감정 분석: {ticker}")
            
            # 모든 데이터를 하나의 리스트로 합치기
            all_data = []
            for source, items in data.items():
                for item in items:
                    item["source"] = source
                    all_data.append(item)
            
            # 감정 분석 수행
            result = await self._perform_sentiment_analysis(ticker, data)
            
            return result
        
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
                        sentiment_result = await self._analyze_with_llm(text_content, source, item)
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
        
    async def _analyze_with_llm(self, text: str, source: str, original_item: dict = None) -> dict:
        """설정된 LLM을 사용한 고급 금융 감정 분석"""
        llm_info = self.llm_manager.get_provider_info()
        print(f"         🔮 {llm_info['provider'].upper()} 분석 시작 - Source: {source}")
        print(f"         📝 텍스트 길이: {len(text)}")
        
        # 소스별 전문적인 프롬프트 설정
        if source == "sec":
            context = "SEC 공시 자료를 금융 전문가 관점에서"
            focus = "재무 실적, 리스크 요인, 경영진 전망"
        elif source == "news":
            context = "뉴스 기사를 투자 분석가 관점에서"
            focus = "시장 반응, 업계 동향, 경쟁사 대비"
        elif source == "twitter":
            context = "소셜 미디어 여론을 시장 심리 관점에서"
            focus = "투자자 정서, 트렌드, 바이럴 요소"
        else:
            context = "투자 관련 텍스트를 전문가 관점에서"
            focus = "투자 가치, 성장성, 리스크"
        
        prompt = f"""
당신은 20년 경력의 금융 투자 전문가입니다. {context} 분석해주세요.
분석 시 {focus}에 특히 주목해주세요.

분석할 텍스트:
"{text}"

다음 JSON 형식으로 정확하게 응답하세요:
{{
    "summary": "핵심 투자 시사점 한줄 요약 (한국어)",
    "score": -1과 1 사이의 감정 점수 (매우 부정적: -1, 부정적: -0.5, 중립: 0, 긍정적: 0.5, 매우 긍정적: 1),
    "confidence": 0과 1 사이의 분석 신뢰도,
    "financial_impact": "high/medium/low - 재무적 영향도",
    "key_topics": ["주제1", "주제2", "주제3"] - 최대 3개의 핵심 주제,
    "risk_factors": ["리스크1", "리스크2"] - 식별된 리스크 요인들,
    "opportunities": ["기회1", "기회2"] - 식별된 투자 기회들,
    "time_horizon": "short/medium/long - 영향이 미치는 시간적 범위"
}}

주의사항:
1. 감정 점수는 단순 긍정/부정이 아닌 투자 관점에서의 매력도를 평가
2. 금융 전문 용어를 적절히 사용하되 요약은 명확하게
3. 추측이 아닌 텍스트에 근거한 분석만 수행
4. JSON 형식을 정확히 지켜서 응답
"""
        
        try:
            # LLM Manager를 통해 생성
            print(f"         📤 {llm_info['provider']} 요청 전송 중...")
            response = await self.llm_manager.generate(prompt)
            print(f"         📥 응답 수신")
            
            # JSON 추출
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    sentiment_data = json.loads(match.group(0))
                    # 원본 데이터의 모든 필드를 보존하면서 감정 분석 결과 추가
                    result = original_item.copy() if original_item else {"text": text}
                    result.update({
                        "source": source,
                        "summary": sentiment_data.get("summary", "요약 없음"),
                        "score": float(sentiment_data.get("score", 0)),
                        "confidence": float(sentiment_data.get("confidence", 0.5)),
                        "financial_impact": sentiment_data.get("financial_impact", "medium"),
                        "key_topics": sentiment_data.get("key_topics", []),
                        "risk_factors": sentiment_data.get("risk_factors", []),
                        "opportunities": sentiment_data.get("opportunities", []),
                        "time_horizon": sentiment_data.get("time_horizon", "medium")
                    })
                    return result
                except json.JSONDecodeError as e:
                    print(f"         ❌ JSON 파싱 오류: {e}")
                    print(f"         📄 원본 내용: {response[:200]}...")
                    
        except Exception as e:
            print(f"         ❌ LLM 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 실패 시 기존 Gemini API 사용 (폴백)
        if llm_info['provider'] != 'gemini' and self.gemini_api_key:
            print(f"         🔄 Gemini API로 폴백...")
            return await self._analyze_with_gemini(text, source, original_item)
            
        # 최종 실패 시 기본값 반환
        result = original_item.copy() if original_item else {}
        result.update({
            "text": text[:200] + "..." if len(text) > 200 else text,
            "source": source,
            "summary": "분석 실패",
            "score": 0.0
        })
        return result
        
    async def _analyze_with_gemini(self, text: str, source: str, original_item: dict = None) -> dict:
        """Gemini API를 직접 사용한 고급 금융 감정 분석 (레거시/폴백)"""
        print(f"         🔮 Gemini API 직접 호출 - Source: {source}")
        print(f"         📝 텍스트 길이: {len(text)}")
        
        # 소스별 전문적인 프롬프트 설정
        if source == "sec":
            context = "SEC 공시 자료를 금융 전문가 관점에서"
            focus = "재무 실적, 리스크 요인, 경영진 전망"
        elif source == "news":
            context = "뉴스 기사를 투자 분석가 관점에서"
            focus = "시장 반응, 업계 동향, 경쟁사 대비"
        elif source == "twitter":
            context = "소셜 미디어 여론을 시장 심리 관점에서"
            focus = "투자자 정서, 트렌드, 바이럴 요소"
        else:
            context = "투자 관련 텍스트를 전문가 관점에서"
            focus = "투자 가치, 성장성, 리스크"
        
        prompt = f"""
당신은 20년 경력의 금융 투자 전문가입니다. {context} 분석해주세요.
분석 시 {focus}에 특히 주목해주세요.

분석할 텍스트:
"{text}"

다음 JSON 형식으로 정확하게 응답하세요:
{{
    "summary": "핵심 투자 시사점 한줄 요약 (한국어)",
    "score": -1과 1 사이의 감정 점수 (매우 부정적: -1, 부정적: -0.5, 중립: 0, 긍정적: 0.5, 매우 긍정적: 1),
    "confidence": 0과 1 사이의 분석 신뢰도,
    "financial_impact": "high/medium/low - 재무적 영향도",
    "key_topics": ["주제1", "주제2", "주제3"] - 최대 3개의 핵심 주제,
    "risk_factors": ["리스크1", "리스크2"] - 식별된 리스크 요인들,
    "opportunities": ["기회1", "기회2"] - 식별된 투자 기회들,
    "time_horizon": "short/medium/long - 영향이 미치는 시간적 범위"
}}

주의사항:
1. 감정 점수는 단순 긍정/부정이 아닌 투자 관점에서의 매력도를 평가
2. 금융 전문 용어를 적절히 사용하되 요약은 명확하게
3. 추측이 아닌 텍스트에 근거한 분석만 수행
4. JSON 형식을 정확히 지켜서 응답
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
                                # 원본 데이터의 모든 필드를 보존하면서 감정 분석 결과 추가
                                result = original_item.copy() if original_item else {"text": text}
                                result.update({
                                    "source": source,
                                    "summary": sentiment_data.get("summary", "요약 없음"),
                                    "score": float(sentiment_data.get("score", 0)),
                                    "confidence": float(sentiment_data.get("confidence", 0.5)),
                                    "financial_impact": sentiment_data.get("financial_impact", "medium"),
                                    "key_topics": sentiment_data.get("key_topics", []),
                                    "risk_factors": sentiment_data.get("risk_factors", []),
                                    "opportunities": sentiment_data.get("opportunities", []),
                                    "time_horizon": sentiment_data.get("time_horizon", "medium")
                                })
                                return result
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
            
        # 실패 시 기본값 반환 (원본 데이터 보존)
        result = original_item.copy() if original_item else {}
        result.update({
            "text": text[:200] + "..." if len(text) > 200 else text,
            "source": source,
            "summary": "분석 실패",
            "score": 0.0
        })
        return result

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