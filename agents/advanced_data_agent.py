import uvicorn
import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
app = FastAPI()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
API_URL = "https://finnhub.io/api/v1/company-news"
MAX_ARTICLES_TO_ANALYZE = int(os.getenv("MAX_ARTICLES_TO_SCRAPE", 5))


@app.post("/collect_news/{ticker}")
async def collect_news_data(ticker: str):
    """[FINAL] Finnhub API를 호출하여 정제된 뉴스 헤드라인과 요약을 수집합니다."""
    print(f"🤖 [뉴스 에이전트] '{ticker}' 관련 Finnhub API 기반 뉴스 수집 시작...")
    if not FINNHUB_API_KEY:
        return [
            {
                "source": "뉴스",
                "text": "Finnhub API 키가 설정되지 않았습니다.",
                "log_message": "❌ [뉴스] Finnhub API 키가 설정되지 않았습니다.",
            }
        ]

    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    querystring = {
        "symbol": ticker,
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"   [뉴스 에이전트 로그] Finnhub API 호출 시작 (티커: {ticker})")
            response = await client.get(API_URL, params=querystring, timeout=30)
            response.raise_for_status()
            news_items = response.json()

            if not isinstance(news_items, list) or not news_items:
                return [
                    {
                        "source": "뉴스",
                        "text": f"'{ticker}' 관련 최신 뉴스를 찾지 못했습니다.",
                        "log_message": f"➡️ [뉴스] '{ticker}' 관련 뉴스가 없습니다.",
                    }
                ]

            response_data = []
            for item in news_items[:MAX_ARTICLES_TO_ANALYZE]:
                headline = item.get("headline")
                summary = item.get("summary")
                # 헤드라인과 요약이 모두 있는 유효한 뉴스만 사용
                if headline and summary:
                    # 헤드라인과 요약을 합쳐 분석할 텍스트를 생성
                    full_text = f"{headline}. {summary}"
                    log_message = f"➡️ [뉴스] '{headline[:30]}...' 뉴스 수집 완료."
                    response_data.append(
                        {
                            "source": "뉴스",
                            "text": full_text,
                            "log_message": log_message,
                        }
                    )

            if not response_data:
                return [
                    {
                        "source": "뉴스",
                        "text": f"'{ticker}' 관련 요약 정보를 포함한 유효한 뉴스를 찾지 못했습니다.",
                        "log_message": f"➡️ [뉴스] '{ticker}' 관련 유효한 뉴스가 없습니다.",
                    }
                ]

            print(
                f"🤖 [뉴스 에이전트] 완료. 총 {len(response_data)}개의 정제된 뉴스 수집."
            )
            return response_data

        except Exception as e:
            print(f"❌ [뉴스 에이전트] API 호출 중 오류 발생: {e}")
            return [
                {
                    "source": "뉴스",
                    "text": "뉴스 데이터 수집에 실패했습니다.",
                    "log_message": f"❌ [뉴스] API 호출 중 오류 발생: {e}",
                }
            ]
