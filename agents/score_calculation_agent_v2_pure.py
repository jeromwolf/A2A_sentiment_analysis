import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import statistics

app = FastAPI()

# 데이터 소스별 중요도 가중치 정의
SOURCE_WEIGHTS = {
    "뉴스": 1.0,
    "News": 1.0,
    "트위터": 0.7,
    "Twitter": 0.7,
    "기업 공시": 1.5,
    "SEC": 1.5,
    "Default": 1.0
}


class ScoreCalculationRequest(BaseModel):
    analyzed_results: List[Dict]


class ScoreCalculationResponse(BaseModel):
    final_score: int
    weighted_average: float
    total_items: int
    valid_items: int
    score_breakdown: Dict[str, Dict]  # source별 점수 통계


@app.post("/calculate_weighted_score", response_model=ScoreCalculationResponse)
async def calculate_weighted_score(request: ScoreCalculationRequest):
    """가중치를 적용하여 최종 점수를 계산합니다."""
    print(f"[V2 점수계산] {len(request.analyzed_results)}개 항목에 대한 가중 점수 계산 시작...")
    
    if not request.analyzed_results:
        raise HTTPException(status_code=400, detail="No results to calculate")
    
    # 소스별 점수 그룹화
    source_scores = {}
    total_weighted_score = 0
    total_weight = 0
    valid_item_count = 0
    
    for item in request.analyzed_results:
        score = item.get("score")
        source = item.get("source", "Default")
        
        # 유효한 점수만 처리
        if score is not None and isinstance(score, (int, float)):
            # 소스별 통계를 위한 그룹화
            if source not in source_scores:
                source_scores[source] = []
            source_scores[source].append(float(score))
            
            # 가중치 적용
            weight = SOURCE_WEIGHTS.get(source, SOURCE_WEIGHTS["Default"])
            total_weighted_score += float(score) * weight
            total_weight += weight
            valid_item_count += 1
    
    # 최종 점수 계산
    if total_weight == 0:
        final_score = 0
        weighted_average = 0.0
    else:
        # 가중 평균 계산
        weighted_average = total_weighted_score / total_weight
        # -100 ~ 100 스케일로 변환
        final_score = round(weighted_average * 100)
        # 범위 제한
        final_score = max(-100, min(100, final_score))
    
    # 소스별 점수 분석
    score_breakdown = {}
    for source, scores in source_scores.items():
        if scores:
            score_breakdown[source] = {
                "count": len(scores),
                "average": statistics.mean(scores),
                "min": min(scores),
                "max": max(scores),
                "weight": SOURCE_WEIGHTS.get(source, SOURCE_WEIGHTS["Default"])
            }
    
    print(f"[V2 점수계산] 완료 - 최종점수: {final_score}, 유효항목: {valid_item_count}/{len(request.analyzed_results)}")
    
    return ScoreCalculationResponse(
        final_score=final_score,
        weighted_average=weighted_average,
        total_items=len(request.analyzed_results),
        valid_items=valid_item_count,
        score_breakdown=score_breakdown
    )


@app.post("/calculate_simple_score")
async def calculate_simple_score(request: ScoreCalculationRequest):
    """V1 호환성을 위한 단순 점수 계산 엔드포인트"""
    result = await calculate_weighted_score(request)
    
    log_message = f"성공적으로 분석된 {result.valid_items}개 정보의 가중 평균 점수({result.weighted_average:.2f})를 변환하여 최종 점수 '{result.final_score}'점 산출 완료."
    
    return {
        "final_score": result.final_score,
        "log_message": log_message
    }


@app.get("/health")
async def health_check():
    """서비스 상태를 확인합니다."""
    return {
        "status": "healthy",
        "service": "score_calculation_agent_v2",
        "weights": SOURCE_WEIGHTS
    }


@app.get("/weights")
async def get_weights():
    """현재 설정된 가중치 정보를 반환합니다."""
    return {
        "source_weights": SOURCE_WEIGHTS,
        "description": "데이터 소스별 신뢰도 가중치"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8203)