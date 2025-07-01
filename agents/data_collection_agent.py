import uvicorn
import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import asyncio
import re

load_dotenv()
app = FastAPI()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
API_URL = "https://finnhub.io/api/v1/company-news"
MAX_ARTICLES_TO_ANALYZE = int(os.getenv("MAX_ARTICLES_TO_SCRAPE", 3))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


async def scrape_article_content(url: str, client: httpx.AsyncClient):
    try:
        response = await client.get(url, timeout=15, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article_body = soup.find("article") or soup.find(
            class_=re.compile("article-body|post-content|content|caas-body")
        )
        if article_body:
            for s in article_body(["script", "style"]):
                s.decompose()
            paragraphs = article_body.find_all("p")
            content = " ".join([p.get_text(strip=True) for p in paragraphs])
            if len(content) > 300:
                print(f"   [뉴스 에이전트 로그] 본문 스크래핑 성공: {url}")
                return content
        return None
    except Exception as e:
        print(f"❌ [뉴스 에이전트] 본문 스크래핑 실패: {url} ({e})")
        return None


async def fetch_finnhub_news_and_scrape_bodies(ticker: str):
    if not FINNHUB_API_KEY:
        return [{"source": "Finnhub", "text": "Finnhub API 키가 설정되지 않았습니다."}]
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    querystring = {
        "symbol": ticker,
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_API_KEY,
    }

    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            print(f"   [뉴스 에이전트 로그] Finnhub API 호출 시작 (티커: {ticker})")
            response = await client.get(API_URL, params=querystring, timeout=30)
            response.raise_for_status()
            news_items = response.json()
            if not isinstance(news_items, list) or not news_items:
                return []

            news_urls = [item.get("url") for item in news_items if item.get("url")]
            print(
                f"   [뉴스 에이전트 로그] API로부터 {len(news_urls)}개의 뉴스 URL 수신 완료."
            )

            tasks = [
                scrape_article_content(url, client)
                for url in news_urls[: MAX_ARTICLES_TO_ANALYZE * 2]
            ]
            scraped_contents = await asyncio.gather(*tasks)
            valid_contents = [content for content in scraped_contents if content]

            return [
                {"source": "뉴스", "text": content}
                for content in valid_contents[:MAX_ARTICLES_TO_ANALYZE]
            ]

        except Exception as e:
            print(f"❌ [뉴스 에이전트] API 호출 중 오류 발생: {e}")
            return [{"source": "Finnhub", "text": "뉴스 데이터 수집에 실패했습니다."}]


@app.post("/collect/{ticker}")
async def collect_news_data(ticker: str):
    print(f"🤖 [뉴스 에이전트] '{ticker}' 관련 뉴스 본문 수집 시작...")
    collected_contents = await fetch_finnhub_news_and_scrape_bodies(ticker.upper())
    if not collected_contents:
        text = f"'{ticker.upper()}'에 대한 분석 가능한 최신 뉴스를 찾지 못했습니다."
        return [{"source": "뉴스", "text": text}]
    return collected_contents
