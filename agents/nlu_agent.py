import uvicorn
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# [NEW] API 호출을 줄이기 위한 자체 지식(내장 맵) 추가
COMPANY_NAME_TO_TICKER = {
    "애플": "AAPL",
    "APPLE": "AAPL",
    "마이크로소프트": "MSFT",
    "MICROSOFT": "MSFT",
    "구글": "GOOGL",
    "GOOGLE": "GOOGL",
    "아마존": "AMZN",
    "AMAZON": "AMZN",
    "엔비디아": "NVDA",
    "NVIDIA": "NVDA",
    "테슬라": "TSLA",
    "TESLA": "TSLA",
    "메타": "META",
    "META PLATFORMS": "META",
}


class QueryRequest(BaseModel):
    query: str


async def call_gemini_for_ticker(query: str):
    """Gemini API를 호출하여 티커를 추출합니다."""
    prompt = f"""
    From the following sentence, extract the official stock ticker symbol (e.g., AAPL, NVDA, GOOGL).
    If a company name is mentioned, convert it to its ticker symbol.
    Your response MUST be only the ticker symbol. If you cannot find a valid ticker, respond with "None".
    Sentence: "{query}"
    Ticker: 
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            ticker = (
                result["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
            )
            return ticker if ticker != "NONE" and len(ticker) < 10 else None
        except Exception as e:
            print(f"❌ [NLU 에이전트] Gemini API 호출 오류: {e}")
            return None


@app.post("/extract_ticker")
async def extract_ticker_from_query(request: QueryRequest):
    """[IMPROVED] 사용자의 질문을 분석하여 티커를 추출합니다. 내장 맵을 먼저 확인합니다."""
    print(f'🧠 [NLU 에이전트] 질문 분석 시작: "{request.query}"')
    query_upper = request.query.upper()

    # 1. 내장된 지식(맵)에서 먼저 찾아봅니다.
    for name, ticker in COMPANY_NAME_TO_TICKER.items():
        if name in query_upper:
            print(f"   [NLU 로그] 내장 지식에서 '{ticker}' 티커를 즉시 발견했습니다.")
            return {
                "ticker": ticker,
                "log_message": f"'{request.query}'에서 '{ticker}' 종목 분석을 요청한 것으로 이해했습니다.",
            }

    # 2. 내장 지식에 없으면, Gemini 전문가에게 물어봅니다.
    print(f"   [NLU 로그] 내장 지식에 없어 Gemini API 호출을 시도합니다.")
    if not GEMINI_API_KEY:
        return {
            "ticker": None,
            "log_message": "❌ [NLU] Gemini API 키가 설정되지 않았습니다.",
        }

    ticker = await call_gemini_for_ticker(request.query)

    if ticker:
        print(f"🧠 [NLU 에이전트] Gemini 분석을 통해 티커 추출 완료: {ticker}")
        return {
            "ticker": ticker,
            "log_message": f"'{request.query}'에서 '{ticker}' 종목 분석을 요청한 것으로 이해했습니다.",
        }
    else:
        print(f"🧠 [NLU 에이전트] 질문에서 유효한 티커를 찾지 못했습니다.")
        return {
            "ticker": None,
            "log_message": f"'{request.query}'에서 분석할 종목을 찾지 못했습니다.",
        }
