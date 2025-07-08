"""
점수 계산 에이전트 V2 - A2A 프로토콜 기반
감정 분석 결과를 받아 가중치를 적용하여 최종 점수 계산
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI
from contextlib import asynccontextmanager

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from pydantic import BaseModel
from typing import Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoreRequest(BaseModel):
    ticker: str
    sentiments: List[Dict[str, Any]]

class ScoreCalculationAgentV2(BaseAgent):
    """점수 계산 A2A 에이전트"""
    
    # 소스별 가중치 설정
    SOURCE_WEIGHTS = {
        "sec": 1.5,      # 기업 공시 - 가장 신뢰도 높음
        "news": 1.0,     # 뉴스 - 기본 가중치
        "twitter": 0.7   # 트위터 - 상대적으로 낮은 신뢰도
    }
    
    def __init__(self):
        super().__init__(
            name="Score Calculation Agent V2",
            description="감정 분석 결과에 가중치를 적용하여 최종 점수를 계산하는 A2A 에이전트",
            port=8203
        )
        self.capabilities = [
            {
                "name": "score_calculation",
                "version": "2.0",
                "description": "감정 분석 결과에 가중치를 적용하여 최종 점수 계산",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"},
                        "sentiments": {"type": "array", "description": "감정 분석 결과"}
                    },
                    "required": ["ticker", "sentiments"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "final_score": {"type": "number"},
                        "sentiment": {"type": "string"},
                        "details": {"type": "object"}
                    }
                }
            }
        ]
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/calculate_score")
        async def calculate_score(request: ScoreRequest):
            """HTTP 엔드포인트로 점수 계산"""
            ticker = request.ticker
            sentiments = request.sentiments
            
            logger.info(f"📊 HTTP 요청으로 점수 계산: {ticker}")
            logger.info(f"📊 분석할 감정 결과: {len(sentiments)}개")
            
            # 점수 계산
            result = self._calculate_weighted_score(sentiments)
            
            # 최종 감정 결정
            final_sentiment = self._determine_sentiment(result["final_score"])
            
            response_data = {
                "ticker": ticker,
                "final_score": result["final_score"],
                "sentiment": final_sentiment,
                "details": result["details"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 점수 계산 완료 - 최종 점수: {result['final_score']:.2f} ({final_sentiment})")
            
            return response_data
    
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """메시지 처리"""
        logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action')}")
        
        if message.header.message_type == MessageType.REQUEST:
            action = message.body.get("action")
            
            if action == "score_calculation":
                return await self._handle_score_calculation(message)
        
        return None
    
    async def _handle_score_calculation(self, message: A2AMessage) -> A2AMessage:
        """점수 계산 요청 처리"""
        try:
            payload = message.body.get("payload", {})
            ticker = payload.get("ticker", "")
            sentiments = payload.get("sentiments", [])
            
            logger.info(f"📊 점수 계산 시작 - 티커: {ticker}")
            logger.info(f"📊 분석할 감정 결과: {len(sentiments)}개")
            
            # 점수 계산
            result = self._calculate_weighted_score(sentiments)
            
            # 최종 감정 결정
            final_sentiment = self._determine_sentiment(result["final_score"])
            
            response_data = {
                "ticker": ticker,
                "final_score": result["final_score"],
                "sentiment": final_sentiment,
                "details": result["details"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 점수 계산 완료 - 최종 점수: {result['final_score']:.2f} ({final_sentiment})")
            
            # 이벤트 브로드캐스트
            await self._broadcast_score_calculated(ticker, response_data)
            
            # 응답 전송
            await self.reply_to_message(
                original_message=message,
                result=response_data,
                success=True
            )
            
            return None  # reply_to_message가 직접 응답을 전송함
            
        except Exception as e:
            logger.error(f"❌ 점수 계산 실패: {str(e)}")
            await self.reply_to_message(
                original_message=message,
                result={"error": str(e)},
                success=False
            )
            return None
    
    def _calculate_weighted_score(self, sentiments: List[Dict]) -> Dict:
        """가중치를 적용한 점수 계산"""
        source_scores = {}
        source_counts = {}
        
        # 소스별 점수 집계
        for item in sentiments:
            source = item.get("source", "unknown")
            score = item.get("score", 0)
            
            if source not in source_scores:
                source_scores[source] = []
                source_counts[source] = 0
            
            source_scores[source].append(score)
            source_counts[source] += 1
        
        # 소스별 평균 점수 계산
        source_averages = {}
        for source, scores in source_scores.items():
            if scores:
                source_averages[source] = sum(scores) / len(scores)
            else:
                source_averages[source] = 0
        
        # 가중치 적용
        weighted_sum = 0
        weight_sum = 0
        
        for source, avg_score in source_averages.items():
            weight = self.SOURCE_WEIGHTS.get(source, 0.5)  # 기본 가중치 0.5
            weighted_sum += avg_score * weight * source_counts[source]
            weight_sum += weight * source_counts[source]
        
        # 최종 점수 계산
        final_score = weighted_sum / weight_sum if weight_sum > 0 else 0
        
        return {
            "final_score": final_score,
            "details": {
                "source_averages": source_averages,
                "source_counts": source_counts,
                "weights_applied": {source: self.SOURCE_WEIGHTS.get(source, 0.5) for source in source_averages},
                "total_items": len(sentiments)
            }
        }
    
    def _determine_sentiment(self, score: float) -> str:
        """점수에 따른 감정 결정"""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"
    
    async def _broadcast_score_calculated(self, ticker: str, result: Dict):
        """점수 계산 완료 이벤트 브로드캐스트"""
        event_data = {
            "ticker": ticker,
            "final_score": result["final_score"],
            "sentiment": result["sentiment"],
            "timestamp": result["timestamp"]
        }
        
        await self.broadcast_event("score_calculated", event_data)
        logger.info(f"📢 점수 계산 이벤트 브로드캐스트: {ticker} - {result['sentiment']}")
    
    async def on_start(self):
        """에이전트 시작 시 실행"""
        logger.info("✅ Score Calculation Agent V2 초기화 완료")
    
    async def on_stop(self):
        """에이전트 종료 시 실행"""
        logger.info("👋 Score Calculation Agent V2 종료 중...")

# 에이전트 인스턴스 생성
agent = ScoreCalculationAgentV2()

# BaseAgent의 app을 사용
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8203)