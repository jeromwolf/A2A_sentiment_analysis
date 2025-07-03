"""
Twitter Agent V2 - 순수 A2A 구현

트위터 데이터를 수집하는 독립적인 V2 에이전트
V1 의존성 없이 직접 Twitter API 호출
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

load_dotenv()


class TwitterAgentV2(BaseAgent):
    """트위터 데이터 수집 V2 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="Twitter Agent V2",
            description="트위터 데이터를 수집하는 A2A 에이전트",
            port=8209,
            registry_url="http://localhost:8001"
        )
        
        # API 키 설정
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.max_tweets = 10
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "twitter_data_collection",
            "version": "2.0",
            "description": "트위터 데이터 수집",
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
        
        print("✅ Twitter Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 Twitter Agent V2 종료 중...")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                
                if action == "twitter_data_collection":
                    await self._handle_twitter_collection(message)
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
            
    async def _handle_twitter_collection(self, message: A2AMessage):
        """트위터 수집 요청 처리"""
        payload = message.body.get("payload", {})
        ticker = payload.get("ticker", "")
        
        print(f"🐦 트위터 수집 시작: {ticker}")
        
        try:
            # Twitter API로 트윗 수집
            tweets_data = await self._fetch_tweets(ticker)
            
            # 결과 포맷팅
            result = {
                "data": tweets_data,
                "count": len(tweets_data),
                "source": "twitter",
                "log_message": f"✅ {ticker} 트윗 {len(tweets_data)}개 수집 완료"
            }
            
            # 데이터 수집 완료 이벤트 브로드캐스트
            await self.broadcast_event(
                event_type="data_collected",
                event_data={
                    "source": "twitter",
                    "ticker": ticker,
                    "count": len(tweets_data)
                }
            )
            
            await self.reply_to_message(message, result=result, success=True)
            
        except Exception as e:
            print(f"❌ 트위터 수집 오류: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e), "data": [], "count": 0},
                success=False
            )
            
    async def _fetch_tweets(self, ticker: str) -> List[Dict]:
        """Twitter API v2로 트윗 가져오기"""
        if not self.bearer_token:
            print("⚠️ Twitter Bearer Token이 없습니다")
            # API 키가 없으면 빈 데이터 반환
            return []
            
        try:
            # Twitter API v2 검색
            query = f"${ticker} OR #{ticker} -is:retweet lang:en"
            url = "https://api.twitter.com/2/tweets/search/recent"
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "v2FilteredStreamPython"
            }
            
            params = {
                "query": query,
                "max_results": self.max_tweets,
                "tweet.fields": "created_at,author_id,public_metrics"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get("data", [])
                    
                    # 데이터 포맷팅
                    formatted_tweets = []
                    for tweet in tweets:
                        tweet_id = tweet.get("id", "")
                        author_id = tweet.get("author_id", "")
                        
                        formatted_tweets.append({
                            "text": tweet.get("text", ""),
                            "author": f"user_{author_id}",
                            "created_at": tweet.get("created_at", ""),
                            "url": f"https://twitter.com/user_{author_id}/status/{tweet_id}" if tweet_id else "",
                            "metrics": tweet.get("public_metrics", {}),
                            "source": "twitter",
                            "sentiment": None,  # 나중에 감정분석에서 채움
                            "log_message": f"🐦 트윗: {tweet.get('text', '')[:50]}..."
                        })
                        
                    return formatted_tweets
                elif response.status_code == 429:
                    print(f"⚠️ Twitter API Rate Limit 도달 - 건너뜁니다")
                    # Rate limit 시 빈 데이터 반환
                    return []
                else:
                    print(f"❌ Twitter API 오류: {response.status_code}")
                    # API 오류 시 빈 데이터 반환
                    return []
                    
        except Exception as e:
            print(f"❌ Twitter API 호출 오류: {e}")
            # 오류 시 빈 데이터 반환
            return []
            
    def _get_mock_tweets(self, ticker: str) -> List[Dict]:
        """모의 트윗 데이터 생성 - 티커별로 다른 내용"""
        # 티커별 특화된 트윗 템플릿
        ticker_specific_tweets = {
            "AAPL": [
                {
                    "text": f"${ticker} Vision Pro 2 출시 루머가 돌고 있다. AR/VR 시장 선점 기대 📱",
                    "author": "tech_analyst",
                    "sentiment": "positive"
                },
                {
                    "text": f"${ticker} 아이폰 15 판매 부진 우려. 중국 시장 점유율 하락 😟",
                    "author": "market_bear",
                    "sentiment": "negative"
                },
                {
                    "text": f"${ticker} 서비스 부문 매출 지속 성장 중. 구독 경제 강화 💪",
                    "author": "apple_investor",
                    "sentiment": "positive"
                }
            ],
            "TSLA": [
                {
                    "text": f"${ticker} 사이버트럭 생산량 증가! 예약 주문 100만대 돌파 🚗",
                    "author": "ev_enthusiast",
                    "sentiment": "positive"
                },
                {
                    "text": f"${ticker} 자율주행 규제 이슈로 주가 압박 받을 듯 ⚠️",
                    "author": "auto_analyst",
                    "sentiment": "negative"
                },
                {
                    "text": f"${ticker} 에너지 저장 사업 호조. 태양광 시장 확대 기대 ☀️",
                    "author": "clean_energy",
                    "sentiment": "positive"
                }
            ],
            "NVDA": [
                {
                    "text": f"${ticker} AI 칩 수요 폭발! H100 공급 부족 지속 🤖",
                    "author": "ai_investor",
                    "sentiment": "positive"
                },
                {
                    "text": f"${ticker} 중국 수출 규제로 매출 타격 우려 📉",
                    "author": "geopolitics_watch",
                    "sentiment": "negative"
                },
                {
                    "text": f"${ticker} 데이터센터 GPU 시장 독점적 지위 유지 💻",
                    "author": "semiconductor_pro",
                    "sentiment": "positive"
                }
            ]
        }
        
        # 기본 템플릿 (알려지지 않은 티커용)
        default_tweets = [
            {
                "text": f"${ticker} showing interesting price action today 📊",
                "author": "trader_daily",
                "sentiment": "neutral"
            },
            {
                "text": f"Watching ${ticker} closely for breakout opportunity 👀",
                "author": "swing_trader",
                "sentiment": "neutral"
            },
            {
                "text": f"${ticker} volume picking up. Something brewing? 🤔",
                "author": "volume_analyst",
                "sentiment": "neutral"
            }
        ]
        
        # 티커에 맞는 트윗 선택
        tweets_template = ticker_specific_tweets.get(ticker, default_tweets)
        
        # 트윗 포맷팅
        mock_tweets = []
        for i, template in enumerate(tweets_template[:self.max_tweets]):
            created_at = datetime.now() - timedelta(hours=i*2)
            mock_tweet_id = f"mock_{ticker}_{i}_{int(created_at.timestamp())}"
            
            mock_tweets.append({
                "text": template["text"],
                "author": template["author"],
                "created_at": created_at.isoformat(),
                "url": f"https://twitter.com/{template['author']}/status/{mock_tweet_id}",
                "metrics": {
                    "retweet_count": 20 + i*15,
                    "like_count": 50 + i*30
                },
                "source": "twitter",
                "sentiment": None,  # 감정분석에서 처리
                "log_message": f"🐦 트윗: {template['text'][:50]}..."
            })
        
        return mock_tweets


# 모듈 레벨에서 에이전트와 app 생성
agent = TwitterAgentV2()
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