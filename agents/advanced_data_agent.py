#!/usr/bin/env python3
"""Advanced Data Agent - 뉴스 데이터를 수집하는 고급 에이전트"""

import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Advanced News Data Agent", version="1.0.0")

# API 키 설정
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# 회사명 - 티커 매핑
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "GOOGL": "Google",
    "MSFT": "Microsoft", 
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "INTC": "Intel",
    "NFLX": "Netflix"
}

@app.get("/health")
async def health_check():
    """상태 확인 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_keys_configured": {
            "finnhub": bool(FINNHUB_API_KEY),
            "news_api": bool(NEWS_API_KEY),
            "alpha_vantage": bool(ALPHA_VANTAGE_API_KEY)
        }
    }

@app.post("/collect_news/{ticker}")
async def collect_news(ticker: str) -> Dict:
    """뉴스 데이터 수집"""
    logger.info(f"📰 뉴스 수집 시작: {ticker}")
    
    try:
        company_name = TICKER_TO_COMPANY.get(ticker.upper(), ticker)
        all_news = []
        
        # Finnhub API를 사용한 뉴스 수집
        if FINNHUB_API_KEY:
            finnhub_news = await collect_finnhub_news(ticker)
            all_news.extend(finnhub_news)
        
        # NewsAPI를 사용한 뉴스 수집 (백업)
        if NEWS_API_KEY and len(all_news) < 5:
            newsapi_news = await collect_newsapi_news(company_name, ticker)
            all_news.extend(newsapi_news)
        
        # 모의 데이터 (API 키가 없거나 데이터가 부족한 경우)
        if len(all_news) < 3:
            logger.warning(f"실제 뉴스 데이터가 부족합니다. 모의 데이터를 추가합니다.")
            mock_news = generate_mock_news(ticker, company_name)
            all_news.extend(mock_news)
        
        # 중복 제거 및 정렬
        unique_news = remove_duplicates(all_news)
        sorted_news = sorted(unique_news, key=lambda x: x.get("published_date", ""), reverse=True)
        
        # 최대 10개까지만 반환
        final_news = sorted_news[:10]
        
        logger.info(f"✅ 뉴스 수집 완료: {len(final_news)}개 항목")
        
        return {
            "ticker": ticker,
            "count": len(final_news),
            "news": final_news,
            "sources": list(set(item.get("source", "Unknown") for item in final_news))
        }
        
    except Exception as e:
        logger.error(f"❌ 뉴스 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def collect_finnhub_news(ticker: str) -> List[Dict]:
    """Finnhub API를 사용한 뉴스 수집"""
    news_items = []
    
    try:
        async with httpx.AsyncClient() as client:
            # 날짜 범위 설정 (최근 7일)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=7)
            
            response = await client.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": ticker,
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "token": FINNHUB_API_KEY
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data[:5]:  # 최대 5개
                    news_items.append({
                        "title": item.get("headline", ""),
                        "content": item.get("summary", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", "Finnhub"),
                        "published_date": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                        "sentiment": "neutral",  # Finnhub은 감정 분석 제공 안함
                        "api_source": "finnhub"
                    })
                    
                logger.info(f"📈 Finnhub에서 {len(news_items)}개 뉴스 수집")
                
    except Exception as e:
        logger.error(f"Finnhub API 오류: {e}")
    
    return news_items

async def collect_newsapi_news(company_name: str, ticker: str) -> List[Dict]:
    """NewsAPI를 사용한 뉴스 수집"""
    news_items = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": f"{company_name} OR {ticker}",
                    "apiKey": NEWS_API_KEY,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get("articles", []):
                    news_items.append({
                        "title": article.get("title", ""),
                        "content": article.get("description", "") or article.get("content", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "published_date": article.get("publishedAt", ""),
                        "sentiment": "neutral",
                        "api_source": "newsapi"
                    })
                    
                logger.info(f"📰 NewsAPI에서 {len(news_items)}개 뉴스 수집")
                
    except Exception as e:
        logger.error(f"NewsAPI 오류: {e}")
    
    return news_items

def generate_mock_news(ticker: str, company_name: str) -> List[Dict]:
    """모의 뉴스 데이터 생성"""
    now = datetime.now()
    
    mock_templates = [
        {
            "title": f"{company_name} Reports Strong Q4 Earnings, Beats Analyst Expectations",
            "content": f"{company_name} ({ticker}) announced fourth-quarter earnings that exceeded Wall Street expectations, driven by strong product sales and expanding market share. Revenue grew 15% year-over-year.",
            "sentiment": "positive"
        },
        {
            "title": f"{company_name} Announces Major AI Investment Initiative",
            "content": f"{company_name} unveiled plans to invest $10 billion in artificial intelligence infrastructure over the next three years, positioning itself at the forefront of the AI revolution.",
            "sentiment": "positive"
        },
        {
            "title": f"Analysts Remain Cautious on {company_name} Stock Amid Market Volatility",
            "content": f"Several Wall Street analysts have maintained their 'hold' ratings on {ticker}, citing concerns about global economic conditions and increasing competition in key markets.",
            "sentiment": "neutral"
        }
    ]
    
    news_items = []
    for i, template in enumerate(mock_templates):
        news_items.append({
            "title": template["title"],
            "content": template["content"],
            "url": f"https://example.com/news/{ticker}-{i}",
            "source": "Market Analysis",
            "published_date": (now - timedelta(hours=i*8)).isoformat(),
            "sentiment": template["sentiment"],
            "api_source": "mock"
        })
    
    return news_items

def remove_duplicates(news_list: List[Dict]) -> List[Dict]:
    """중복 뉴스 제거"""
    seen_titles = set()
    unique_news = []
    
    for item in news_list:
        title = item.get("title", "").lower().strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(item)
    
    return unique_news

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)