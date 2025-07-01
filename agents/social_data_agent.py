import uvicorn
import httpx
from fastapi import FastAPI
import random
import html  # HTML 엔티티(&amp;) 처리를 위해 추가

app = FastAPI()

REDDIT_URL = "https://www.reddit.com/r/stocks/search.json"


@app.post("/collect/{ticker}")
async def collect_social_data(ticker: str):
    """Reddit의 주식 포럼에서 특정 종목 관련 최신 게시글 제목을 가져옵니다."""
    print(f"💬 [소셜 데이터 에이전트] '{ticker}' 관련 Reddit 게시물 수집 시작...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    # [IMPROVED] 회사 토론(flair)으로 범위를 좁히고 검색어 정확도 향상
    params = {
        "q": f'flair:"Company Discussion" "{ticker}"',
        "sort": "new",
        "limit": 20,  # 충분한 게시물을 가져와 필터링
        "restrict_sr": "on",
        "t": "month",  # 검색 기간을 최근 한 달로 제한
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(REDDIT_URL, params=params, headers=headers)
            response.raise_for_status()
            posts = response.json()["data"]["children"]

            # [IMPROVED] 의미 없는 토론 스레드 필터링
            filtered_posts = [
                p
                for p in posts
                if "daily discussion" not in p["data"].get("title", "").lower()
            ]

            if not filtered_posts:
                collected_text = (
                    f"'{ticker}'에 대한 유의미한 소셜 미디어 언급을 찾지 못했습니다."
                )
            else:
                post = random.choice(filtered_posts)["data"]
                # [FIXED] HTML 엔티티를 일반 문자로 변환
                collected_text = html.unescape(post.get("title", "제목 없음"))

            log_message = f'💬 [소셜] "{collected_text}"'
            print("💬 [소셜 데이터 에이전트] 완료")
            return {
                "source": "소셜",
                "text": collected_text,
                "log_message": log_message,
            }

        except Exception as e:
            print(f"❌ [소셜 데이터 에이전트] Reddit 스크래핑 중 오류 발생: {e}")
            collected_text = f"'{ticker}' 관련 소셜 데이터 수집에 실패했습니다. (시뮬레이션 데이터 사용)"
            log_message = f'❌ [소셜] 스크래핑 오류. "{collected_text}"'
            return {
                "source": "소셜",
                "text": collected_text,
                "log_message": log_message,
            }
