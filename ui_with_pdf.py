#!/usr/bin/env python3
"""
UI 서버 - PDF 내보내기 기능 포함
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import json
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2A UI Server with PDF Export")

# HTML 파일 서빙
@app.get("/")
async def get_index():
    """메인 UI 페이지 제공"""
    return FileResponse("index_with_pdf.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 처리 - Orchestrator로 중계"""
    await websocket.accept()
    logger.info("✅ UI 클라이언트 연결됨")
    
    # Orchestrator WebSocket 연결
    import websockets
    orchestrator_ws = None
    
    try:
        # Orchestrator에 연결
        orchestrator_ws = await websockets.connect("ws://localhost:8000/ws")
        logger.info("✅ Orchestrator 연결 성공")
        
        # 양방향 메시지 중계 태스크
        async def ui_to_orchestrator():
            """UI -> Orchestrator 메시지 중계"""
            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    
                    # analyze 메시지에 PDF 생성 옵션 추가
                    if msg.get("type") == "analyze":
                        # generate_pdf 옵션이 있으면 그대로 전달
                        if "generate_pdf" not in msg:
                            msg["generate_pdf"] = True  # 기본값 True
                        
                        logger.info(f"📤 분석 요청: {msg.get('query')} (PDF: {msg.get('generate_pdf')})")
                    
                    await orchestrator_ws.send(json.dumps(msg))
                    
            except WebSocketDisconnect:
                logger.info("UI 연결 종료")
            except Exception as e:
                logger.error(f"UI->Orchestrator 오류: {e}")
        
        async def orchestrator_to_ui():
            """Orchestrator -> UI 메시지 중계"""
            try:
                async for message in orchestrator_ws:
                    data = json.loads(message)
                    
                    # PDF 경로가 포함된 결과 메시지 로깅
                    if data.get("type") == "result" and "pdf_path" in data:
                        logger.info(f"📄 PDF 생성됨: {data['pdf_path']}")
                    
                    await websocket.send_text(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("Orchestrator 연결 종료")
            except Exception as e:
                logger.error(f"Orchestrator->UI 오류: {e}")
        
        # 두 태스크를 동시에 실행
        await asyncio.gather(
            ui_to_orchestrator(),
            orchestrator_to_ui()
        )
        
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"연결 오류: {str(e)}"
        })
    finally:
        # 정리
        if orchestrator_ws:
            await orchestrator_ws.close()
        await websocket.close()
        logger.info("🔌 연결 종료")

# PDF 다운로드 엔드포인트 (선택적)
@app.get("/download/pdf/{filename}")
async def download_pdf(filename: str):
    """생성된 PDF 다운로드"""
    import os
    pdf_path = f"reports/pdf/{filename}"
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=filename
        )
    return {"error": "File not found"}

if __name__ == "__main__":
    print("=" * 60)
    print("A2A UI Server with PDF Export")
    print("=" * 60)
    print("📍 UI 주소: http://localhost:8100")
    print("📍 Orchestrator 연결: ws://localhost:8000/ws")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8100)