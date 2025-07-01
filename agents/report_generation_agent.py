import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv
import httpx

load_dotenv()
app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# 점수 계산에 사용되는 가중치 정보 (디버깅 및 리포트용)
SOURCE_WEIGHTS = {
    "뉴스": 1.0,
    "트위터": 0.7,
    "기업 공시": 1.5,
}


class ReportRequest(BaseModel):
    ticker: str
    final_score: int
    analyzed_results: List[Dict]


async def generate_professional_report(
    ticker: str, final_score: int, analyzed_results: List[Dict]
):
    """Gemini AI를 호출하여 수집된 모든 정보를 바탕으로 종합 리포트를 생성합니다."""

    if not GEMINI_API_KEY:
        return "Gemini API 키가 설정되지 않아 상세 리포트를 생성할 수 없습니다."

    # [NEW] 점수 산출 근거를 생성하는 로직 추가
    source_data = {}
    valid_results = [item for item in analyzed_results if item.get("score") is not None]

    for item in valid_results:
        source = item.get("source", "기타")
        if source not in source_data:
            source_data[source] = []
        source_data[source].append(item.get("score"))

    calculation_breakdown = "#### 점수 산출 방식 (가중 평균)\n"
    if not valid_results:
        calculation_breakdown += "분석에 사용된 유효한 정보가 없습니다.\n"
    else:
        for source, scores in source_data.items():
            weight = SOURCE_WEIGHTS.get(source, 1.0)
            avg_score = sum(scores) / len(scores)
            calculation_breakdown += f"- **{source}** ({len(scores)}건, 가중치 {weight}): {avg_score:.2f} (평균 점수)\n"

    calculation_breakdown += f"\n> _위 점수들을 가중 평균하여 최종 점수 **{final_score}**이 산출되었습니다._\n\n---"

    data_summary = ""
    for item in valid_results:
        source = item.get("source", "기타")
        summary = item.get("summary", "요약 없음")
        score = item.get("score")
        data_summary += f"- **[{source}]** {summary}\n  - `감성 점수: {score:.2f}`\n"

    # [IMPROVEMENT] Gemini에게 전달하는 프롬프트에 분석 기반 정보 추가
    prompt = f"""
    당신은 전문 금융 애널리스트입니다. 아래 분석 기반 정보와 데이터를 바탕으로 '{ticker}' 종목에 대한 투자 심리 분석 리포트를 작성해주세요.

    리포트는 반드시 아래의 마크다운 형식을 따라야 하며, 각 항목에 대해 전문적이고 중립적인 톤으로 서술해주세요.

    ### 종합 의견 (Overall Opinion)
    (종합 점수와 데이터를 바탕으로 현재 시장의 투자 심리에 대한 최종 결론을 2~3문장으로 작성합니다.)

    ### 긍정적 요인 (Positive Factors)
    (데이터에서 발견된 긍정적인 요인들을 1~2개의 항목으로 요약합니다. 없다면 "특별한 긍정적 요인을 찾지 못했습니다."라고 작성합니다.)

    ### 부정적 또는 중립적 요인 (Negative/Neutral Factors)
    (데이터에서 발견된 부정적이거나 중립적인 요인들을 1~2개의 항목으로 요약합니다. 없다면 "특별한 부정적/중립적 요인을 찾지 못했습니다."라고 작성합니다.)

    ---
    {calculation_breakdown}
    
    #### 세부 분석 데이터
    {data_summary}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            report_text = response.json()["candidates"][0]["content"]["parts"][0][
                "text"
            ]
            return report_text
        except Exception as e:
            print(f"❌ 리포트 생성 에이전트 오류: {e}")
            return "상세 리포트를 생성하는 데 실패했습니다."


@app.post("/generate_report")
async def generate_report(data: ReportRequest):
    print("📝 [리포트 생성 에이전트] 전문가 수준 리포트 생성 시작...")

    report = await generate_professional_report(
        ticker=data.ticker,
        final_score=data.final_score,
        analyzed_results=data.analyzed_results,
    )

    print("📝 [리포트 생성 에이전트] 완료")
    return {"report": report}
