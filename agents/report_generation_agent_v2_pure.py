import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import httpx
from datetime import datetime

load_dotenv()
app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# 점수별 투자 권고 매핑
SCORE_RECOMMENDATIONS = {
    "매우 긍정적": (60, 100),
    "긍정적": (20, 59),
    "중립적": (-19, 19),
    "부정적": (-59, -20),
    "매우 부정적": (-100, -60)
}


def get_recommendation_level(score: int) -> str:
    """점수에 따른 투자 권고 수준을 반환합니다."""
    for level, (min_score, max_score) in SCORE_RECOMMENDATIONS.items():
        if min_score <= score <= max_score:
            return level
    return "중립적"


async def generate_professional_report(
    ticker: str, 
    final_score: int, 
    analyzed_results: List[Dict],
    score_breakdown: Optional[Dict] = None
) -> str:
    """Gemini AI를 사용하여 전문적인 투자 리포트를 생성합니다."""
    
    if not GEMINI_API_KEY:
        return """
## 투자 심리 분석 리포트

**종목:** {ticker}  
**최종 점수:** {final_score}/100  
**투자 권고:** {recommendation}  
**생성 시간:** {timestamp}

### 요약
Gemini API 키가 설정되지 않아 AI 기반 상세 분석을 제공할 수 없습니다.

### 데이터 요약
수집된 {total}개 데이터 중 {valid}개가 성공적으로 분석되었습니다.
""".format(
            ticker=ticker,
            final_score=final_score,
            recommendation=get_recommendation_level(final_score),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=len(analyzed_results),
            valid=sum(1 for r in analyzed_results if r.get("score") is not None)
        )
    
    # 유효한 결과만 필터링
    valid_results = [r for r in analyzed_results if r.get("score") is not None]
    
    # 소스별 데이터 정리
    source_summaries = {}
    for result in valid_results:
        source = result.get("source", "기타")
        if source not in source_summaries:
            source_summaries[source] = []
        source_summaries[source].append({
            "summary": result.get("summary", "요약 없음"),
            "score": result.get("score", 0)
        })
    
    # 점수 분석 섹션 생성
    score_analysis = ""
    if score_breakdown:
        score_analysis = "\n#### 소스별 점수 분석\n"
        for source, stats in score_breakdown.items():
            score_analysis += f"- **{source}** ({stats['count']}건, 가중치 {stats['weight']}): 평균 {stats['average']:.2f}, 범위 [{stats['min']:.2f} ~ {stats['max']:.2f}]\n"
    
    # 데이터 요약 섹션 생성
    data_summary = ""
    for source, items in source_summaries.items():
        data_summary += f"\n**{source} ({len(items)}건)**\n"
        for item in items[:3]:  # 소스당 최대 3개만 표시
            data_summary += f"- {item['summary'][:100]}... (점수: {item['score']:.2f})\n"
    
    # Gemini 프롬프트 생성
    recommendation_level = get_recommendation_level(final_score)
    
    prompt = f"""
당신은 한국의 전문 투자 애널리스트입니다. 아래의 데이터를 바탕으로 '{ticker}' 종목에 대한 전문적인 투자 심리 분석 리포트를 작성해주세요.

**분석 데이터:**
- 최종 투자 심리 점수: {final_score}/100 ({recommendation_level})
- 분석된 데이터: {len(valid_results)}개
- 수집 소스: {', '.join(source_summaries.keys())}

{score_analysis}

**주요 데이터:**
{data_summary}

**리포트 작성 지침:**
1. 한국어로 작성하되, 전문적이고 객관적인 톤을 유지하세요.
2. 아래의 마크다운 형식을 정확히 따라주세요.
3. 각 섹션은 2-3개의 구체적인 문장으로 작성하세요.
4. 데이터에 기반한 사실적인 분석을 제공하세요.

반드시 아래 형식으로 작성하세요:

## 투자 심리 분석 리포트

**종목:** {ticker}  
**최종 점수:** {final_score}/100  
**투자 권고:** {recommendation_level}  
**생성 시간:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### 종합 의견
(최종 점수와 데이터를 바탕으로 현재 시장의 투자 심리에 대한 종합적인 평가를 2-3문장으로 작성)

### 긍정적 요인
(데이터에서 발견된 긍정적 신호들을 2-3개 bullet point로 정리)

### 부정적/중립적 요인  
(데이터에서 발견된 부정적이거나 주의가 필요한 요인들을 2-3개 bullet point로 정리)

### 투자자 유의사항
(투자 결정 시 고려해야 할 추가 사항이나 리스크 요인을 1-2문장으로 작성)

---
_본 리포트는 AI 기반 감정 분석 결과이며, 실제 투자 결정은 추가적인 재무 분석과 전문가 상담을 권장합니다._
"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            report_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return report_text
        except Exception as e:
            print(f"[V2 리포트생성] Gemini API 오류: {e}")
            # 폴백 리포트 반환
            return f"""
## 투자 심리 분석 리포트

**종목:** {ticker}  
**최종 점수:** {final_score}/100  
**투자 권고:** {recommendation_level}  
**생성 시간:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### 종합 의견
AI 리포트 생성 중 오류가 발생했습니다. 수집된 {len(valid_results)}개의 데이터를 기반으로 계산된 최종 점수는 {final_score}점으로, 현재 시장 심리는 '{recommendation_level}' 수준으로 평가됩니다.

### 분석 요약
- 총 {len(analyzed_results)}개 데이터 중 {len(valid_results)}개 성공적으로 분석
- 주요 데이터 소스: {', '.join(source_summaries.keys())}

### 투자자 유의사항
본 분석은 자동화된 감정 분석 결과이며, 실제 투자 결정 시에는 추가적인 검토가 필요합니다.
"""


class ReportGenerationRequest(BaseModel):
    ticker: str
    final_score: int
    analyzed_results: List[Dict]
    score_breakdown: Optional[Dict] = None


class ReportGenerationResponse(BaseModel):
    report: str
    metadata: Dict


@app.post("/generate_investment_report", response_model=ReportGenerationResponse)
async def generate_investment_report(request: ReportGenerationRequest):
    """투자 심리 분석 리포트를 생성합니다."""
    print(f"[V2 리포트생성] {request.ticker} 종목 리포트 생성 시작...")
    
    if not request.ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    
    report = await generate_professional_report(
        ticker=request.ticker,
        final_score=request.final_score,
        analyzed_results=request.analyzed_results,
        score_breakdown=request.score_breakdown
    )
    
    # 메타데이터 생성
    valid_count = sum(1 for r in request.analyzed_results if r.get("score") is not None)
    metadata = {
        "ticker": request.ticker,
        "final_score": request.final_score,
        "recommendation": get_recommendation_level(request.final_score),
        "total_items": len(request.analyzed_results),
        "valid_items": valid_count,
        "generated_at": datetime.now().isoformat(),
        "gemini_used": bool(GEMINI_API_KEY)
    }
    
    print(f"[V2 리포트생성] 완료 - {request.ticker} ({request.final_score}점)")
    
    return ReportGenerationResponse(
        report=report,
        metadata=metadata
    )


@app.post("/generate_report")
async def generate_report_v1_compatible(request: ReportGenerationRequest):
    """V1 호환성을 위한 리포트 생성 엔드포인트"""
    result = await generate_investment_report(request)
    return {"report": result.report}


@app.get("/health")
async def health_check():
    """서비스 상태를 확인합니다."""
    return {
        "status": "healthy",
        "service": "report_generation_agent_v2",
        "gemini_configured": bool(GEMINI_API_KEY)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8204)