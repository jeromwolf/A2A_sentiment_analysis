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
import logging
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Depends
import uvicorn
from utils.llm_manager import get_llm_manager

# 설정 관리자 및 커스텀 에러 임포트
from utils.config_manager import config
from utils.errors import LLMResponseError, LLMQuotaExceededError, SentimentAnalysisError
from utils.auth import verify_api_key
from utils.cache_manager import cache_manager

# 환경 변수 로드
load_dotenv(override=True)

# 로깅 설정
logger = logging.getLogger(__name__)

class SentimentRequest(BaseModel):
    ticker: str
    data: Dict[str, List[Dict[str, Any]]]

class SentimentAnalysisAgentV2(BaseAgent):
    """감정 분석 A2A 에이전트"""
    
    def __init__(self, name: str = None, port: int = None):
        # 설정에서 에이전트 정보 가져오기
        agent_config = config.get_agent_config("sentiment_analysis")
        
        super().__init__(
            name=name or agent_config.get("name", "Sentiment Analysis Agent V2"),
            port=port or agent_config.get("port", 8202),
            description="감정 분석을 수행하는 A2A 에이전트"
        )
        
        # 타임아웃 설정
        self.timeout = agent_config.get("timeout", 120)
        self.batch_size = agent_config.get("batch_size", 10)
        
        # LLM Manager 초기화
        self.llm_manager = get_llm_manager()
        available_providers = self.llm_manager.get_available_providers()
        logger.info(f"🤖 사용 가능한 LLM 제공자: {available_providers}")
        
        # 첫 번째 프로바이더 모델 정보 표시
        if available_providers:
            for provider in self.llm_manager.providers:
                if provider.is_available():
                    provider_name = provider.__class__.__name__
                    if hasattr(provider, 'model'):
                        logger.info(f"🚀 기본 LLM 모델: {provider_name} ({provider.model})")
                    else:
                        logger.info(f"🚀 기본 LLM 모델: {provider_name}")
                    break
        
        # Gemini API (레거시 - 직접 API 호출이 필요한 경우)
        self.gemini_api_key = config.get_env("GEMINI_API_KEY")
        self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/analyze_sentiment", dependencies=[Depends(verify_api_key)])
        async def analyze_sentiment(request: SentimentRequest):
            """HTTP 엔드포인트로 감정 분석"""
            ticker = request.ticker
            data = request.data
            
            print(f"🎯 HTTP 요청으로 감정 분석: {ticker}")
            
            # 캐시 키 생성을 위한 데이터 해시
            import hashlib
            data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
            cache_params = {"ticker": ticker, "data_hash": data_hash}
            
            # 캐시 확인
            cached_result = await cache_manager.get_async("sentiment_analysis", cache_params)
            if cached_result:
                print(f"💾 캐시에서 감정 분석 결과 반환")
                return cached_result
            
            # 모든 데이터를 하나의 리스트로 합치기
            all_data = []
            for source, items in data.items():
                for item in items:
                    item["source"] = source
                    all_data.append(item)
            
            # 감정 분석 수행
            result = await self._perform_sentiment_analysis(ticker, data)
            
            # 성공한 경우 캐시에 저장
            if result.get("success_count", 0) > 0:
                await cache_manager.set_async("sentiment_analysis", cache_params, result)
            
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
        # 현재 사용 가능한 프로바이더 확인
        available_providers = self.llm_manager.get_available_providers()
        current_provider = available_providers[0] if available_providers else "unknown"
        print(f"         🔮 {current_provider.upper()} 분석 시작 - Source: {source}")
        print(f"         📝 텍스트 길이: {len(text)}")
        
        # 텍스트가 너무 길면 잘라내기 (LLM 토큰 제한 고려)
        max_text_length = 3000  # 약 1000 토큰 정도
        if len(text) > max_text_length:
            text = text[:max_text_length] + "... (텍스트가 잘렸습니다)"
            print(f"         ✂️ 텍스트를 {max_text_length}자로 잘랐습니다")
        
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
        
        prompt = f"""금융 전문가로서 {source} 데이터를 분석하세요.

텍스트: "{text}"

JSON만 출력하세요:
{{
    "summary": "한줄 요약",
    "score": -1.0~1.0 사이 숫자,
    "confidence": 0.0~1.0 사이 숫자,
    "financial_impact": "high 또는 medium 또는 low",
    "key_topics": ["주제1", "주제2"],
    "risk_factors": ["리스크1"],
    "opportunities": ["기회1"],
    "time_horizon": "short 또는 medium 또는 long"
}}"""
        
        try:
            # LLM Manager를 통해 생성
            print(f"         📤 {current_provider} 요청 전송 중...")
            response = await self.llm_manager.generate(prompt)
            print(f"         📥 응답 수신")
            
            # JSON 추출
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    sentiment_data = json.loads(match.group(0))
                    # 원본 데이터의 모든 필드를 보존하면서 감정 분석 결과 추가
                    result = original_item.copy() if original_item else {"text": text}
                    # score와 confidence 안전하게 변환
                    score_value = sentiment_data.get("score", 0)
                    if score_value is None:
                        score_value = 0
                    confidence_value = sentiment_data.get("confidence", 0.5)
                    if confidence_value is None:
                        confidence_value = 0.5
                        
                    result.update({
                        "source": source,
                        "summary": sentiment_data.get("summary", "요약 없음"),
                        "score": float(score_value),
                        "confidence": float(confidence_value),
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
                    # JSON 파싱 실패 시 기본값 반환
                    logger.warning(f"JSON 파싱 실패, 기본값으로 처리: {source}")
                    
        except LLMQuotaExceededError:
            raise  # 할당량 초과는 다시 발생시킴
        except Exception as e:
            logger.error(f"         ❌ LLM 오류: {e}")
            raise LLMResponseError(current_provider, "JSON format")
        
        # 실패 시 기존 Gemini API 사용 (폴백)
        if current_provider != 'gemini' and self.gemini_api_key:
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
        
        # 텍스트가 너무 길면 잘라내기 (LLM 토큰 제한 고려)
        max_text_length = 3000  # 약 1000 토큰 정도
        if len(text) > max_text_length:
            text = text[:max_text_length] + "... (텍스트가 잘렸습니다)"
            print(f"         ✂️ 텍스트를 {max_text_length}자로 잘랐습니다")
        
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
        
        prompt = f"""금융 전문가로서 {source} 데이터를 분석하세요.

텍스트: "{text}"

JSON만 출력하세요:
{{
    "summary": "한줄 요약",
    "score": -1.0~1.0 사이 숫자,
    "confidence": 0.0~1.0 사이 숫자,
    "financial_impact": "high 또는 medium 또는 low",
    "key_topics": ["주제1", "주제2"],
    "risk_factors": ["리스크1"],
    "opportunities": ["기회1"],
    "time_horizon": "short 또는 medium 또는 long"
}}"""
        
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
                                # score와 confidence 안전하게 변환
                                score_value = sentiment_data.get("score", 0)
                                if score_value is None:
                                    score_value = 0
                                confidence_value = sentiment_data.get("confidence", 0.5)
                                if confidence_value is None:
                                    confidence_value = 0.5
                                    
                                result.update({
                                    "source": source,
                                    "summary": sentiment_data.get("summary", "요약 없음"),
                                    "score": float(score_value),
                                    "confidence": float(confidence_value),
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