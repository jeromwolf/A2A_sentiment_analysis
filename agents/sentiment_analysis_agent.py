import uvicorn
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Tuple, Optional
import os
from dotenv import load_dotenv
import re
import json

load_dotenv()
app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


def extract_json_from_string(text: str) -> Optional[dict]:
    """Gemini 응답에 다른 텍스트가 포함되어 있어도 JSON 부분만 정확히 추출합니다."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


async def analyze_single_item(text: str, source: str) -> Tuple[str, Optional[float]]:
    """단일 텍스트의 감정을 분석하고 요약과 점수를 반환합니다."""
    # 데이터 소스에 따라 프롬프트 최적화
    if source in ["트위터", "기업 공시"]:
        prompt_instruction = (
            f"Analyze the sentiment of the following text from {source}."
        )
        summary_instruction = text  # 요약 없이 원본 텍스트 사용
    else:  # 뉴스
        prompt_instruction = "Please analyze the following news article. First, provide a one-sentence summary in Korean."
        summary_instruction = "[Your one-sentence summary in Korean]"

    prompt = f"""
    {prompt_instruction}
    Second, provide a sentiment score between -1.0 (very negative) and 1.0 (very positive).

    Your response MUST be ONLY a valid JSON object in the following format:
    {{
      "summary": "{summary_instruction}",
      "score": <sentiment_score_as_float>
    }}

    Text:
    ---
    {text[:4000]} 
    ---
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]

            result_json = extract_json_from_string(content)
            if not result_json:
                print(
                    f"❌ Gemini 응답에서 유효한 JSON을 파싱하지 못했습니다. 응답: {content}"
                )
                return "분석 실패 (응답 형식 오류)", None

            summary = result_json.get("summary", "요약 실패")

            # Gemini가 리스트나 다른 형식으로 점수를 줘도 처리 가능하도록 수정
            score_value = result_json.get("score")
            if isinstance(score_value, list) and len(score_value) > 0:
                score = float(score_value[0])
            elif isinstance(score_value, (int, float)):
                score = float(score_value)
            else:
                score = None  # 유효하지 않은 형식이면 None 처리

            return summary, score
        except Exception as e:
            print(f"❌ Gemini API 호출/파싱 오류: {e}")
            return "분석 중 오류가 발생했습니다.", None


class ItemToAnalyze(BaseModel):
    text: str
    source: str


@app.post("/analyze_sentiment")
async def analyze_sentiment(item: ItemToAnalyze):
    """단일 아이템을 받아 분석 결과를 반환하는 엔드포인트입니다."""
    print(f"😊 [{item.source}] 내용 분석 시작...")

    if not GEMINI_API_KEY:
        return {
            "summary": "API 키가 없어 분석할 수 없습니다.",
            "score": None,
            "log_message": "➡️ [분석] GEMINI_API_KEY가 설정되지 않았습니다.",
            "source": item.source,
        }

    failure_keywords = ["실패", "찾지 못했습니다", "설정되지 않았습니다", "오류"]
    is_failure_message = any(keyword in item.text for keyword in failure_keywords)

    if not item.text or is_failure_message:
        summary, score = item.text, None
        log_message = f"➡️ [{item.source}] 유효하지 않은 정보이므로 분석에서 제외합니다."
    else:
        summary, score = await analyze_single_item(item.text, item.source)
        if score is None:
            log_message = f'➡️ [{item.source}] 분석 실패: "{summary}" (계산에서 제외)'
        else:
            log_message = f"➡️ [{item.source}] '{summary[:30]}...' 분석 완료. (감성 점수: {score:.2f})"

    print(f"😊 [{item.source}] 분석 완료.")
    return {
        "summary": summary,
        "score": score,
        "log_message": log_message,
        "source": item.source,
    }
