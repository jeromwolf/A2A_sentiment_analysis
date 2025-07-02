#!/usr/bin/env python3
"""
Sentiment Analysis Agent V2 - 간단한 버전
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
                print(f"📤 응답 전송 시도 - 분석 완료: {result.get('success_count', 0)}개")
                await self.reply_to_message(message, result, success=True)
                print(f"✅ 감정 분석 완료 및 응답 전송")
                        
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
        """감정 분석 직접 수행 - 간단한 버전"""
        print(f"🔍 감정 분석 시작 - Ticker: {ticker}")
        
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않음")
            # API 키가 없어도 모의 데이터로 처리
            return self._generate_mock_analysis(ticker, data)
            
        analyzed_results = []
        
        # 각 소스별 데이터 처리
        for source, items in data.items():
            if not isinstance(items, list):
                continue
                
            print(f"📊 {source} 소스 분석 중: {len(items)}개 항목")
                
            for idx, item in enumerate(items):
                if isinstance(item, dict):
                    # 텍스트 내용 추출
                    text_content = ""
                    if "title" in item and item["title"]:
                        text_content += item["title"]
                    if "content" in item and item["content"]:
                        text_content += " " + item["content"]
                    if "text" in item and item["text"]:
                        text_content += " " + item["text"]
                    
                    if not text_content.strip():
                        continue
                        
                    # 간단한 감정 분석 (Gemini API 호출 대신 간단한 규칙 기반)
                    sentiment_result = self._simple_sentiment_analysis(text_content, source)
                    analyzed_results.append(sentiment_result)
                    print(f"   ✅ 항목 {idx+1} 분석 완료")
        
        success_count = len(analyzed_results)
        failure_count = 0
        
        print(f"📊 분석 완료 - 성공: {success_count}, 실패: {failure_count}")
        
        return {
            "analyzed_results": analyzed_results,
            "success_count": success_count,
            "failure_count": failure_count,
            "log_message": f"✅ {success_count}개 항목 감정 분석 완료"
        }
        
    def _simple_sentiment_analysis(self, text: str, source: str) -> dict:
        """간단한 규칙 기반 감정 분석"""
        # 긍정/부정 키워드
        positive_words = ['strong', 'beat', 'exceed', 'positive', 'up', 'gain', 'profit', 'bullish', '상승', '증가', '호재']
        negative_words = ['weak', 'miss', 'down', 'loss', 'negative', 'bearish', 'concern', '하락', '감소', '악재']
        
        text_lower = text.lower()
        
        # 점수 계산
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            score = min(0.8, 0.2 + pos_count * 0.1)
            summary = "긍정적인 내용입니다."
        elif neg_count > pos_count:
            score = max(-0.8, -0.2 - neg_count * 0.1)
            summary = "부정적인 내용입니다."
        else:
            score = 0.0
            summary = "중립적인 내용입니다."
            
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "source": source,
            "summary": summary,
            "score": score
        }
        
    def _generate_mock_analysis(self, ticker: str, data: dict) -> dict:
        """모의 분석 결과 생성"""
        analyzed_results = []
        
        for source, items in data.items():
            if isinstance(items, list):
                for item in items[:3]:  # 최대 3개만 처리
                    if isinstance(item, dict):
                        text = item.get('text', '') or item.get('title', '') or item.get('content', '')
                        if text:
                            analyzed_results.append({
                                "text": text[:100] + "...",
                                "source": source,
                                "summary": f"{source} 데이터 분석됨",
                                "score": 0.5
                            })
                            
        return {
            "analyzed_results": analyzed_results,
            "success_count": len(analyzed_results),
            "failure_count": 0,
            "log_message": f"✅ {len(analyzed_results)}개 항목 분석 완료 (모의)"
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
    print("🚀 Sentiment Analysis Agent V2 (Simple) 시작 중...")
    await agent.start()

# 앱 종료 시 에이전트 정리
@app.on_event("shutdown")
async def shutdown():
    await agent.stop()

if __name__ == "__main__":
    # uvicorn으로 직접 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8202)