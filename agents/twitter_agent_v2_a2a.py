import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from dotenv import load_dotenv

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

load_dotenv()

class TwitterAgentV2(BaseAgent):
    """트위터 데이터 수집 에이전트 V2 - A2A Protocol"""
    
    def __init__(self):
        super().__init__(
            name="Twitter Agent V2",
            description="트위터 데이터를 수집하는 V2 에이전트",
            port=8209,
            registry_url="http://localhost:8001"
        )
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.twitter_api_url = "https://api.twitter.com/2/tweets/search/recent"
        self.max_tweets = 10
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        await self.register_capability({
            "name": "twitter_collection",
            "description": "트위터 데이터 수집",
            "version": "2.0"
        })
        print("✅ Twitter Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 Twitter Agent V2 종료")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        print(f"🐦 트위터 수집 요청 받음: {message.payload}")
        
        if message.payload.get("action") == "collect_twitter":
            ticker = message.payload.get("ticker")
            if not ticker:
                await self.reply_to_message(
                    message, 
                    {"error": "Ticker not provided"}, 
                    success=False
                )
                return
                
            # 트윗 수집
            tweets = await self._fetch_tweets(ticker)
            
            # 응답 전송
            await self.reply_to_message(
                message,
                {
                    "ticker": ticker,
                    "tweets": tweets,
                    "count": len(tweets),
                    "source": "twitter"
                },
                success=True
            )
            print(f"🐦 트위터 수집 완료: {ticker} - {len(tweets)}건")
            
    async def _fetch_tweets(self, ticker: str) -> List[Dict]:
        """Twitter API v2를 사용하여 트윗 수집"""
        if not self.bearer_token:
            print("[V2 트위터수집] Twitter API 토큰이 없습니다. 목 데이터 반환")
            return self._get_mock_tweets(ticker)
            
        # 검색 쿼리 구성
        query = f"${ticker.upper()} -is:retweet lang:ko OR lang:en"
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "v2RecentSearchPython"
        }
        
        params = {
            "query": query,
            "max_results": self.max_tweets,
            "tweet.fields": "created_at,author_id,public_metrics"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.twitter_api_url, 
                    headers=headers, 
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "data" not in data:
                    print(f"[V2 트위터수집] {ticker}에 대한 트윗이 없습니다")
                    return []
                    
                tweets = []
                for tweet in data["data"]:
                    tweets.append({
                        "text": tweet.get("text", ""),
                        "created_at": tweet.get("created_at", ""),
                        "metrics": tweet.get("public_metrics", {}),
                        "author_id": tweet.get("author_id", "")
                    })
                    
                return tweets
                
            except Exception as e:
                print(f"[V2 트위터수집] Twitter API 오류: {e}")
                return self._get_mock_tweets(ticker)
                
    def _get_mock_tweets(self, ticker: str) -> List[Dict]:
        """목 트윗 데이터 반환"""
        mock_data = {
            "AAPL": [
                {
                    "text": f"${ticker} 애플 신제품 발표 기대! 주가 상승 예상 📈",
                    "created_at": datetime.now().isoformat(),
                    "metrics": {"like_count": 150, "retweet_count": 30},
                    "author_id": "user123"
                },
                {
                    "text": f"${ticker} 실적 발표 앞두고 긍정적 전망. 매수 추천!",
                    "created_at": datetime.now().isoformat(),
                    "metrics": {"like_count": 200, "retweet_count": 45},
                    "author_id": "user456"
                }
            ],
            "GOOGL": [
                {
                    "text": f"${ticker} 구글 AI 기술 발전으로 주가 상승세",
                    "created_at": datetime.now().isoformat(),
                    "metrics": {"like_count": 100, "retweet_count": 20},
                    "author_id": "user789"
                }
            ]
        }
        
        return mock_data.get(ticker.upper(), [
            {
                "text": f"${ticker} 종목 전망 긍정적",
                "created_at": datetime.now().isoformat(),
                "metrics": {"like_count": 50, "retweet_count": 10},
                "author_id": "mock_user"
            }
        ])


# 메인 실행
if __name__ == "__main__":
    agent = TwitterAgentV2()
    
    async def startup():
        await agent.start()
        
    asyncio.create_task(startup())
    agent.run()