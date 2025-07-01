import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# [NEW] 데이터 소스별 중요도 가중치 정의
SOURCE_WEIGHTS = {"뉴스": 1.0, "트위터": 0.7, "기업 공시": 1.5, "Default": 1.0}


class SentimentsToScore(BaseModel):
    analyzed_results: List[Dict]


@app.post("/calculate_score")
async def calculate_score(data: SentimentsToScore):
    print("🧮 [점수 계산] 가중치 기반 최종 점수 계산 시작...")

    total_weighted_score = 0
    total_weight = 0
    valid_item_count = 0

    for item in data.analyzed_results:
        score = item.get("score")
        source = item.get("source", "Default")

        # 유효한 점수가 있는 항목만 계산에 포함
        if isinstance(score, (int, float)):
            weight = SOURCE_WEIGHTS.get(source, 1.0)
            total_weighted_score += score * weight
            total_weight += weight
            valid_item_count += 1

    if total_weight == 0:
        final_score = 0
        log_message = "   ➡️ 유효하게 분석된 정보가 없어 최종 점수는 0점입니다."
    else:
        # 가중 평균 계산
        average_weighted_score = total_weighted_score / total_weight
        # 최종 점수 스케일 변환 (-100 ~ 100)
        final_score = round(average_weighted_score * 100)
        log_message = f"   ➡️ 성공적으로 분석된 {valid_item_count}개 정보의 가중 평균 점수({average_weighted_score:.2f})를 변환하여 최종 점수 '{final_score}'점 산출 완료."

    print("🧮 [점수 계산] 완료")
    return {"final_score": final_score, "log_message": log_message}
