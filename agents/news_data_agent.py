import uvicorn
import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta  # 시간 계산을 위해 추가

# .env 파일에서 환경변수 로드
load_dotenv()

app = FastAPI()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"


@app.post("/collect/{ticker}")
async def collect_news_data(ticker: str):
    """NewsAPI를 호출하여 특정 종목의 최신 뉴스 기사 제목을 가져옵니다."""
    if not NEWS_API_KEY:
        print(
            "❌ [뉴스 데이터 에이전트] NEWS_API_KEY가 .env 파일에 설정되지 않았습니다."
        )
        return {
            "source": "뉴스",
            "text": "NEWS_API_KEY가 없어 뉴스를 가져올 수 없습니다.",
            "log_message": "❌ [뉴스] NEWS_API_KEY가 설정되지 않았습니다.",
        }

    print(f"📰 [뉴스 데이터 에이전트] '{ticker}' 관련 실제 뉴스 수집 시작...")

    # [IMPROVED] 더 구체적인 검색어와 날짜 제한 추가
    query = f'"{ticker}" AND (stock OR 주가 OR 실적 OR 전망 OR 주식)'
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "ko",
        "sortBy": "relevancy",  # 관련성 높은 순으로 정렬
        "from": from_date,
        "pageSize": 1,
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. 한국어 뉴스를 먼저 검색
            print(f"   [로그] 한국어 뉴스 검색 시작. (쿼리: {query})")
            response = await client.get(NEWS_API_URL, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            print(f"   [로그] 한국어 뉴스 검색 결과: {len(articles)}개 기사 수신")

            # 2. 한국어 뉴스가 없으면 영어 뉴스를 검색
            if not articles:
                print(f"   [로그] 한국어 뉴스가 없어 영어 뉴스를 검색합니다.")
                params["language"] = "en"
                response = await client.get(NEWS_API_URL, params=params)
                response.raise_for_status()
                articles = response.json().get("articles", [])
                print(f"   [로그] 영어 뉴스 검색 결과: {len(articles)}개 기사 수신")

            if not articles:
                print(
                    f"📰 [뉴스 데이터 에이전트] '{ticker}' 관련 뉴스를 찾지 못했습니다."
                )
                return {
                    "source": "뉴스",
                    "text": "관련 뉴스가 없습니다.",
                    "log_message": f"📰 [뉴스] '{ticker}' 관련 뉴스를 찾지 못했습니다.",
                }

            collected_text = articles[0].get("title", "제목 없음")
            log_message = f'📰 [뉴스] "{collected_text}"'
            print("📰 [뉴스 데이터 에이전트] 완료")
            return {
                "source": "뉴스",
                "text": collected_text,
                "log_message": log_message,
            }

        except Exception as e:
            print(f"❌ [뉴스 데이터 에이전트] 뉴스 API 호출 중 오류 발생: {e}")
            return {
                "source": "뉴스",
                "text": "뉴스 API 호출 중 오류가 발생했습니다.",
                "log_message": f"❌ [뉴스] API 호출 오류: {e}",
            }
