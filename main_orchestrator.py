import uvicorn
import httpx
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

app = FastAPI()

# CORS 설정
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모든 에이전트 URL 등록
AGENT_URLS = {
    "nlu": "http://127.0.0.1:8008/extract_ticker",
    "news": "http://127.0.0.1:8007/collect_news",
    "twitter": "http://127.0.0.1:8009/search_tweets",
    "sec": "http://127.0.0.1:8010/get_filings",
    "analyze": "http://127.0.0.1:8002/analyze_sentiment",
    "calculate": "http://127.0.0.1:8003/calculate_score",
    "generate": "http://127.0.0.1:8004/generate_report",
}


@app.get("/api/agents")
async def get_agents():
    with open("agents.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
async def read_index():
    return FileResponse("index.html")


async def send_to_ui(websocket: WebSocket, msg_type: str, payload: Dict[str, Any]):
    try:
        await websocket.send_json({"type": msg_type, "payload": payload})
    except WebSocketDisconnect:
        print("UI client disconnected.")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        init_data = await websocket.receive_json()
        user_query = init_data.get("query")

        async with httpx.AsyncClient(timeout=120.0) as client:

            # Step 1: NLU Agent
            await send_to_ui(websocket, "status", {"agentId": "nlu-agent"})
            await send_to_ui(
                websocket, "log", {"message": f'질문 분석 시작: "{user_query}"'}
            )
            nlu_response = await client.post(
                AGENT_URLS["nlu"], json={"query": user_query}
            )
            nlu_result = nlu_response.json()
            await send_to_ui(websocket, "log", {"message": nlu_result["log_message"]})
            ticker = nlu_result.get("ticker")
            if not ticker:
                return

            # Step 2: 다중 데이터 소스 병렬 수집
            await send_to_ui(websocket, "status", {"agentId": "data-collection"})
            await send_to_ui(
                websocket,
                "log",
                {"message": "\n뉴스, 트위터, 공시 자료 병렬 수집 시작..."},
            )

            tasks = [
                client.post(f"{AGENT_URLS['news']}/{ticker}"),
                client.post(f"{AGENT_URLS['twitter']}/{ticker}"),
                client.post(f"{AGENT_URLS['sec']}/{ticker}"),
            ]

            all_collected_data = []
            for future in asyncio.as_completed(tasks):
                try:
                    resp = await future
                    resp.raise_for_status()
                    result_list = resp.json()
                    all_collected_data.extend(result_list)
                    for item in result_list:
                        await send_to_ui(
                            websocket, "log", {"message": item.get("log_message")}
                        )
                except Exception as e:
                    await send_to_ui(
                        websocket,
                        "log",
                        {"message": f"⚠️ 일부 데이터 소스 수집 실패: {e}"},
                    )

            # Step 3: 감정 분석 스트리밍
            await send_to_ui(websocket, "status", {"agentId": "sentiment-analysis"})
            await send_to_ui(
                websocket,
                "log",
                {
                    "message": f"\n총 {len(all_collected_data)}개의 정보를 종합하여 순차적으로 분석을 시작합니다."
                },
            )

            analyzed_results = []
            analysis_tasks = [
                client.post(AGENT_URLS["analyze"], json=item)
                for item in all_collected_data
            ]
            for future in asyncio.as_completed(analysis_tasks):
                try:
                    resp = await future
                    resp.raise_for_status()
                    analysis_result = resp.json()
                    analyzed_results.append(analysis_result)
                    await send_to_ui(
                        websocket,
                        "log",
                        {
                            "message": analysis_result.get(
                                "log_message", "분석 로그 없음"
                            )
                        },
                    )
                except Exception as e:
                    await send_to_ui(
                        websocket, "log", {"message": f"⚠️ 일부 항목 분석 실패: {e}"}
                    )

            # Step 4: 점수 계산
            await send_to_ui(websocket, "status", {"agentId": "score-calculation"})
            score_response = await client.post(
                AGENT_URLS["calculate"], json={"analyzed_results": analyzed_results}
            )
            score_result = score_response.json()
            await send_to_ui(
                websocket,
                "log",
                {
                    "message": "\n"
                    + score_result.get("log_message", "점수 계산 로그 없음")
                },
            )

            # Step 5: 리포트 생성
            await send_to_ui(websocket, "status", {"agentId": "report-generation"})
            report_request_data = {
                "ticker": ticker,
                "final_score": score_result.get("final_score", 0),
                "analyzed_results": analyzed_results,
            }
            report_response = await client.post(
                AGENT_URLS["generate"], json=report_request_data
            )
            report_result = report_response.json()

            await send_to_ui(
                websocket,
                "final_report_canvas",
                {"report_markdown": report_result.get("report", "리포트 생성 실패")},
            )

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        print("Connection closed.")
