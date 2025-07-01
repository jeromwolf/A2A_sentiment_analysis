import uvicorn
import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
API_URL = "https://api.twitter.com/2/tweets/search/recent"
MAX_TWEETS_TO_ANALYZE = int(os.getenv("MAX_ARTICLES_TO_SCRAPE", 3))


@app.post("/search_tweets/{ticker}")
async def search_twitter(ticker: str):
    if not TWITTER_BEARER_TOKEN:
        return [
            {
                "source": "트위터",
                "text": "TWITTER_BEARER_TOKEN이 설정되지 않았습니다.",
                "log_message": "❌ [트위터] TWITTER_BEARER_TOKEN이 설정되지 않았습니다.",
            }
        ]

    query = f"#{ticker} lang:en -is:retweet"
    params = {"query": query, "max_results": 10, "tweet.fields": "id"}
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}

    async with httpx.AsyncClient() as client:
        try:
            print(f"   [트위터 에이전트 로그] Twitter API 호출 시작 (쿼리: {query})")
            response = await client.get(API_URL, params=params, headers=headers)
            if response.status_code != 200:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(
                    f"❌ [트위터 에이전트] Twitter API 오류. 상태 코드: {response.status_code}, 내용: {error_detail}"
                )
                if response.status_code == 429:
                    return [
                        {
                            "source": "트위터",
                            "text": "트위터 API 호출량 제한에 도달했습니다.",
                            "log_message": "⚠️ [트위터] API 호출량 제한 도달.",
                        }
                    ]
                response.raise_for_status()

            tweets = response.json().get("data", [])
            if not tweets:
                return [
                    {
                        "source": "트위터",
                        "text": f"#{ticker} 관련 최신 트윗을 찾지 못했습니다.",
                        "log_message": f"➡️ [트위터] #{ticker} 관련 트윗 없음.",
                    }
                ]

            formatted_tweets = []
            for tweet in tweets[:MAX_TWEETS_TO_ANALYZE]:
                tweet_text = tweet.get("text")
                link = f"https://twitter.com/anyuser/status/{tweet.get('id')}"
                log_text = f"➡️ [트위터] '{tweet_text[:30]}...' 정보 수집 완료."
                formatted_tweets.append(
                    {
                        "source": "트위터",
                        "text": f"{tweet_text} (출처: {link})",
                        "log_message": log_text,
                    }
                )
            return formatted_tweets
        except Exception as e:
            return [
                {
                    "source": "트위터",
                    "text": "트위터 데이터 수집 중 예상치 못한 오류가 발생했습니다.",
                    "log_message": f"❌ [트위터] API 호출 중 예외 발생: {e}",
                }
            ]
