import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import re
import json
import asyncio

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


async def analyze_single_item(text: str, source: str) -> Dict:
    """단일 텍스트의 감정을 분석하고 결과를 반환합니다."""
    if not GEMINI_API_KEY:
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "source": source,
            "summary": "API 키가 없어 분석할 수 없습니다.",
            "score": None,
            "error": "GEMINI_API_KEY not configured"
        }
    
    # 데이터 소스에 따라 프롬프트 최적화
    if source in ["트위터", "Twitter", "기업 공시", "SEC"]:
        prompt_instruction = (
            f"Analyze the sentiment of the following text from {source}."
        )
        summary_instruction = "Provide the original text or a very brief summary"
    else:  # 뉴스
        prompt_instruction = "Please analyze the following news article. First, provide a one-sentence summary in Korean."
        summary_instruction = "Your one-sentence summary in Korean"

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
                return {
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "source": source,
                    "summary": "분석 실패 (응답 형식 오류)",
                    "score": None,
                    "error": "Invalid JSON response from Gemini"
                }

            summary = result_json.get("summary", "요약 실패")
            
            # 점수 처리
            score_value = result_json.get("score")
            if isinstance(score_value, list) and len(score_value) > 0:
                score = float(score_value[0])
            elif isinstance(score_value, (int, float)):
                score = float(score_value)
            else:
                score = None

            return {
                "text": text[:200] + "..." if len(text) > 200 else text,
                "source": source,
                "summary": summary,
                "score": score,
                "error": None
            }
        except Exception as e:
            return {
                "text": text[:200] + "..." if len(text) > 200 else text,
                "source": source,
                "summary": "분석 중 오류가 발생했습니다.",
                "score": None,
                "error": str(e)
            }


class SentimentAnalysisRequest(BaseModel):
    items: List[Dict[str, str]]  # [{"text": "...", "source": "..."}, ...]


class SentimentAnalysisResponse(BaseModel):
    analyzed_results: List[Dict]
    success_count: int
    failure_count: int


@app.post("/analyze_sentiments", response_model=SentimentAnalysisResponse)
async def analyze_sentiments(request: SentimentAnalysisRequest):
    """여러 텍스트를 병렬로 분석하여 감정 분석 결과를 반환합니다."""
    print(f"[V2 감정분석] {len(request.items)}개 항목 분석 시작...")
    
    if not request.items:
        raise HTTPException(status_code=400, detail="No items to analyze")
    
    # 병렬로 모든 항목 분석
    tasks = []
    for item in request.items:
        text = item.get("text", "")
        source = item.get("source", "Unknown")
        
        # 유효성 검사
        if not text or len(text.strip()) == 0:
            continue
            
        # 실패 메시지인지 확인
        failure_keywords = ["실패", "찾지 못했습니다", "설정되지 않았습니다", "오류", "API 키가 없"]
        is_failure_message = any(keyword in text for keyword in failure_keywords)
        
        if is_failure_message:
            # 실패 메시지는 분석하지 않고 바로 결과에 포함
            tasks.append(asyncio.create_task(asyncio.sleep(0).then(
                lambda: {
                    "text": text,
                    "source": source,
                    "summary": text,
                    "score": None,
                    "error": "Invalid or failure message"
                }
            )))
        else:
            tasks.append(analyze_single_item(text, source))
    
    # 모든 분석 완료 대기
    if tasks:
        analyzed_results = await asyncio.gather(*tasks)
    else:
        analyzed_results = []
    
    # 성공/실패 카운트
    success_count = sum(1 for r in analyzed_results if r.get("score") is not None)
    failure_count = len(analyzed_results) - success_count
    
    print(f"[V2 감정분석] 완료 - 성공: {success_count}, 실패: {failure_count}")
    
    return SentimentAnalysisResponse(
        analyzed_results=analyzed_results,
        success_count=success_count,
        failure_count=failure_count
    )


@app.get("/health")
async def health_check():
    """서비스 상태를 확인합니다."""
    return {
        "status": "healthy",
        "service": "sentiment_analysis_agent_v2",
        "gemini_configured": bool(GEMINI_API_KEY)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8202)