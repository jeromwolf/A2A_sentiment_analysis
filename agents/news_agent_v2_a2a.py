import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
import json
from dotenv import load_dotenv

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

load_dotenv()

class NewsAgentV2(BaseAgent):
    """뉴스 데이터 수집 에이전트 V2 - A2A Protocol"""
    
    def __init__(self):
        super().__init__(
            name="News Agent V2",
            description="뉴스 데이터를 수집하는 V2 에이전트",
            port=8207,
            registry_url="http://localhost:8001"
        )
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        self.finnhub_url = "https://finnhub.io/api/v1/company-news"
        self.max_articles = int(os.getenv("MAX_ARTICLES_TO_SCRAPE", "3"))
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "news_collection",
            "description": "뉴스 데이터 수집",
            "version": "2.0"
        })
        print("✅ News Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 News Agent V2 종료")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        print(f"📰 뉴스 수집 요청 받음: {message.payload}")
        
        if message.payload.get("action") == "collect_news":
            ticker = message.payload.get("ticker")
            if not ticker:
                await self.reply_to_message(
                    message, 
                    {"error": "Ticker not provided"}, 
                    success=False
                )
                return
                
            # 뉴스 수집
            news_items = await self._fetch_finnhub_news(ticker)
            
            # 응답 전송
            await self.reply_to_message(
                message,
                {
                    "ticker": ticker,
                    "news_items": news_items,
                    "count": len(news_items),
                    "source": "news"
                },
                success=True
            )
            print(f"📰 뉴스 수집 완료: {ticker} - {len(news_items)}건")
            
    async def _fetch_finnhub_news(self, ticker: str) -> List[Dict]:
        """Finnhub API를 사용하여 뉴스 수집"""
        if not self.finnhub_api_key:
            print("[V2 뉴스수집] Finnhub API 키가 없습니다. 목 데이터 반환")
            return self._get_mock_news(ticker)
            
        # 날짜 범위 설정 (최근 7일)
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "symbol": ticker.upper(),
            "from": from_date,
            "to": to_date,
            "token": self.finnhub_api_key
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.finnhub_url, params=params)
                response.raise_for_status()
                articles = response.json()
                
                if not articles:
                    print(f"[V2 뉴스수집] {ticker}에 대한 뉴스가 없습니다")
                    return []
                    
                # 최신 기사부터 max_articles개만 선택
                selected_articles = articles[:self.max_articles]
                
                news_items = []
                for article in selected_articles:
                    news_items.append({
                        "title": article.get("headline", ""),
                        "summary": article.get("summary", ""),
                        "url": article.get("url", ""),
                        "published_at": datetime.fromtimestamp(
                            article.get("datetime", 0)
                        ).isoformat() if article.get("datetime") else None,
                        "source": article.get("source", "Unknown")
                    })
                    
                return news_items
                
            except Exception as e:
                print(f"[V2 뉴스수집] Finnhub API 오류: {e}")
                return self._get_mock_news(ticker)
                
    def _get_mock_news(self, ticker: str) -> List[Dict]:
        """목 뉴스 데이터 반환"""
        mock_data = {
            "AAPL": [
                {
                    "title": "애플, 새로운 AI 기능으로 아이폰 혁신 예고",
                    "summary": "애플이 차세대 아이폰에 혁신적인 AI 기능을 탑재할 예정이라고 발표했다. 이는 시장에서 긍정적인 반응을 얻고 있다.",
                    "url": "https://example.com/apple-ai",
                    "published_at": datetime.now().isoformat(),
                    "source": "TechNews"
                },
                {
                    "title": "애플 주가, 역대 최고치 경신 임박",
                    "summary": "애플의 강력한 실적과 신제품 출시 기대감으로 주가가 상승세를 보이고 있다.",
                    "url": "https://example.com/apple-stock",
                    "published_at": datetime.now().isoformat(),
                    "source": "FinanceDaily"
                }
            ],
            "GOOGL": [
                {
                    "title": "구글, 클라우드 사업 확장으로 실적 개선",
                    "summary": "구글의 클라우드 부문이 급성장하며 전체 실적을 견인하고 있다.",
                    "url": "https://example.com/google-cloud",
                    "published_at": datetime.now().isoformat(),
                    "source": "CloudTech"
                }
            ]
        }
        
        return mock_data.get(ticker.upper(), [
            {
                "title": f"{ticker} 관련 최신 뉴스",
                "summary": f"{ticker} 종목에 대한 시장 전망이 긍정적입니다.",
                "url": "https://example.com/news",
                "published_at": datetime.now().isoformat(),
                "source": "MockNews"
            }
        ])


# 메인 실행
if __name__ == "__main__":
    from datetime import timedelta
    
    agent = NewsAgentV2()
    
    async def startup():
        await agent.start()
        
    asyncio.create_task(startup())
    agent.run()