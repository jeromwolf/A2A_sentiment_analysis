"""
Main Orchestrator V2 - A2A 프로토콜 실제 사용 버전
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import uuid

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType, Priority
from utils.websocket_manager import manage_websocket, broadcast_message
from utils.cache_manager import cache_manager
from dotenv import load_dotenv

load_dotenv()


class OrchestratorV2A2A(BaseAgent):
    """A2A 프로토콜을 실제로 사용하는 오케스트레이터"""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator V2 A2A",
            description="A2A 프로토콜 기반 투자 분석 시스템 오케스트레이터",
            port=8100,
            registry_url="http://localhost:8001"
        )
        
        # WebSocket 연결 관리
        self.active_websockets: List[WebSocket] = []
        
        # 분석 세션 관리
        self.analysis_sessions: Dict[str, Dict] = {}
        
        # 에이전트 응답 대기를 위한 딕셔너리
        self.pending_responses: Dict[str, Dict] = {}
        
        # API Key 설정
        self.api_key = os.getenv("A2A_API_KEY", "default-api-key-change-me")
        
        # CORS 설정
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 능력 등록
        self.add_capability("orchestration", "분석 프로세스 조정")
        self.add_capability("session_management", "세션 및 상태 관리")
        
        # 루트 엔드포인트
        @self.app.get("/")
        async def root():
            return FileResponse("index_v2.html")
        
        # WebSocket 엔드포인트
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            print(f"🔌 WebSocket 연결 시도: {client_id}")
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                await self._handle_websocket(websocket, client_id)
            except WebSocketDisconnect:
                print(f"🔌 WebSocket 연결 종료: {client_id}")
            finally:
                if websocket in self.active_websockets:
                    self.active_websockets.remove(websocket)
                # 세션 정리
                for session_id, session in list(self.analysis_sessions.items()):
                    if session.get("client_id") == client_id:
                        del self.analysis_sessions[session_id]

    async def on_start(self):
        """에이전트 시작 시 초기화"""
        print(f"✅ {self.name} 시작됨")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print(f"🛑 {self.name} 종료됨")

    async def handle_message(self, message: A2AMessage):
        """A2A 메시지 처리"""
        print(f"📨 A2A 메시지 수신: {message.header.action} from {message.header.sender_id}")
        
        # 응답 메시지인 경우
        if message.header.message_type == MessageType.RESPONSE:
            correlation_id = message.header.correlation_id
            if correlation_id in self.pending_responses:
                # 대기 중인 응답 처리
                self.pending_responses[correlation_id] = {
                    "message": message,
                    "received": True
                }
                print(f"✅ 응답 저장됨: {correlation_id}")
            
            # 세션 업데이트도 처리
            session_id = correlation_id.split("-")[0] if "-" in correlation_id else None
            if session_id and session_id in self.analysis_sessions:
                session = self.analysis_sessions[session_id]
                await self._process_agent_response(session, message)

    async def _collect_data_via_a2a(self, session: Dict):
        """A2A 프로토콜을 사용한 데이터 수집"""
        ticker = session["ticker"]
        session_id = session.get("session_id")
        exchange = session.get("exchange", "US")
        
        print(f"🔄 A2A 데이터 수집 시작 - Ticker: {ticker}")
        
        # UI 업데이트
        await self._send_to_ui(session.get("client_id"), "status", {"agentId": "data-collection"})
        await self._send_to_ui(session.get("client_id"), "log", {"message": "📊 A2A 프로토콜로 데이터 수집 시작..."})
        
        # 에이전트 선택
        if exchange == "KRX":
            agents = {
                "news": "news-agent",
                "twitter": "twitter-agent", 
                "dart": "dart-agent",
                "mcp": "mcp-agent"
            }
        else:
            agents = {
                "news": "news-agent",
                "twitter": "twitter-agent",
                "sec": "sec-agent",
                "mcp": "mcp-agent"
            }
        
        # 병렬 A2A 메시지 전송
        tasks = []
        session["pending_data_agents"] = []
        session["collected_data"] = {}
        
        for data_type, agent_id in agents.items():
            correlation_id = f"{session_id}-{agent_id}"
            
            # 응답 대기 설정
            self.pending_responses[correlation_id] = {
                "received": False,
                "data_type": data_type
            }
            
            # A2A 메시지 전송
            task = self.send_message(
                receiver_id=agent_id,
                action="collect_data",
                payload={"ticker": ticker},
                priority=Priority.HIGH
            )
            tasks.append(task)
            session["pending_data_agents"].append(data_type)
            
            # UI 업데이트
            await self._send_to_ui(session.get("client_id"), "log", {
                "message": f"📡 {data_type.upper()} 에이전트에 A2A 메시지 전송..."
            })
        
        # 모든 메시지 전송
        messages = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 응답 대기 (최대 60초)
        timeout = 60
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            all_received = True
            
            for correlation_id, response_info in self.pending_responses.items():
                if correlation_id.startswith(session_id) and not response_info.get("received"):
                    all_received = False
                    break
            
            if all_received:
                break
                
            await asyncio.sleep(0.5)
        
        # 수집된 데이터 처리
        for correlation_id, response_info in list(self.pending_responses.items()):
            if correlation_id.startswith(session_id):
                if response_info.get("received"):
                    message = response_info.get("message")
                    data_type = response_info.get("data_type")
                    
                    if message and message.body.get("success"):
                        data = message.body.get("result", {}).get("data", [])
                        session["collected_data"][data_type] = data
                        
                        await self._send_to_ui(session.get("client_id"), "log", {
                            "message": f"✅ {data_type.upper()} 데이터 수집 완료: {len(data)}건"
                        })
                    else:
                        session["collected_data"][data_type] = []
                        await self._send_to_ui(session.get("client_id"), "log", {
                            "message": f"⚠️ {data_type.upper()} 데이터 수집 실패"
                        })
                else:
                    # 타임아웃
                    data_type = response_info.get("data_type")
                    session["collected_data"][data_type] = []
                    await self._send_to_ui(session.get("client_id"), "log", {
                        "message": f"⏱️ {data_type.upper()} 데이터 수집 시간 초과"
                    })
                
                # 대기 목록에서 제거
                del self.pending_responses[correlation_id]
        
        # 데이터 수집 완료
        print(f"✅ A2A 데이터 수집 완료")
        for data_type, data in session["collected_data"].items():
            print(f"   - {data_type}: {len(data)}건")
        
        # 다음 단계로 진행
        session["state"] = "analyzing_sentiment"
        await self._start_sentiment_analysis_a2a(session)

    async def _start_sentiment_analysis_a2a(self, session: Dict):
        """A2A 프로토콜을 사용한 감성 분석"""
        print(f"🧠 A2A 감성 분석 시작")
        
        # UI 업데이트
        await self._send_to_ui(session.get("client_id"), "status", {"agentId": "sentiment-analysis"})
        await self._send_to_ui(session.get("client_id"), "log", {"message": "🧠 A2A 프로토콜로 감성 분석 시작..."})
        
        # A2A 메시지 전송
        session_id = session.get("session_id")
        correlation_id = f"{session_id}-sentiment-agent"
        
        self.pending_responses[correlation_id] = {"received": False}
        
        message = await self.send_message(
            receiver_id="sentiment-agent",
            action="analyze_sentiment",
            payload={
                "ticker": session.get("ticker"),
                "data": session.get("collected_data", {})
            },
            priority=Priority.HIGH
        )
        
        if message:
            await self._send_to_ui(session.get("client_id"), "log", {
                "message": "✅ 감성 분석 에이전트에 A2A 메시지 전송 완료"
            })

    async def _handle_websocket(self, websocket: WebSocket, client_id: str):
        """WebSocket 메시지 처리"""
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                
                if action == "analyze":
                    query = data.get("query", "")
                    session_id = str(uuid.uuid4())
                    
                    # 세션 생성
                    self.analysis_sessions[session_id] = {
                        "session_id": session_id,
                        "client_id": client_id,
                        "query": query,
                        "state": "initializing"
                    }
                    
                    # NLU 처리
                    await self._start_nlu_processing_a2a(self.analysis_sessions[session_id])
                
        except WebSocketDisconnect:
            print(f"WebSocket 연결 종료: {client_id}")

    async def _start_nlu_processing_a2a(self, session: Dict):
        """A2A 프로토콜을 사용한 NLU 처리"""
        query = session["query"]
        session_id = session["session_id"]
        
        # UI 업데이트
        await self._send_to_ui(session.get("client_id"), "status", {"agentId": "nlu"})
        await self._send_to_ui(session.get("client_id"), "log", {"message": f"🔍 쿼리 분석 중: {query}"})
        
        # A2A 메시지로 NLU 요청
        correlation_id = f"{session_id}-nlu-agent"
        self.pending_responses[correlation_id] = {"received": False}
        
        message = await self.send_message(
            receiver_id="nlu-agent",
            action="extract_ticker",
            payload={"query": query},
            priority=Priority.HIGH
        )
        
        if message:
            # 응답 대기
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                if self.pending_responses[correlation_id].get("received"):
                    response_msg = self.pending_responses[correlation_id].get("message")
                    if response_msg and response_msg.body.get("success"):
                        result = response_msg.body.get("result", {})
                        session["ticker"] = result.get("ticker")
                        session["exchange"] = result.get("exchange", "US")
                        
                        await self._send_to_ui(session.get("client_id"), "log", {
                            "message": f"✅ 티커 추출: {session['ticker']} ({session['exchange']})"
                        })
                        
                        # 데이터 수집 시작
                        session["state"] = "collecting_data"
                        await self._collect_data_via_a2a(session)
                    else:
                        await self._send_to_ui(session.get("client_id"), "error", {
                            "message": "티커 추출 실패"
                        })
                    
                    del self.pending_responses[correlation_id]
                    break
                    
                await asyncio.sleep(0.1)

    async def _send_to_ui(self, client_id: str, event_type: str, data: Dict[str, Any]):
        """UI로 메시지 전송"""
        for ws in self.active_websockets:
            try:
                await ws.send_json({
                    "type": event_type,
                    "data": data,
                    "client_id": client_id
                })
            except:
                pass

    async def _process_agent_response(self, session: Dict, message: A2AMessage):
        """에이전트 응답 처리"""
        state = session.get("state")
        sender_id = message.header.sender_id
        
        print(f"📥 에이전트 응답 처리: {sender_id} (state: {state})")
        
        # 상태별 처리 로직...
        # (기존 로직 유지)


# 모듈 레벨에서 오케스트레이터와 app 생성
orchestrator = OrchestratorV2A2A()
app = orchestrator.app
print(f"✅ {orchestrator.name} 초기화 완료 (A2A 프로토콜 사용)")


@app.on_event("startup")
async def startup():
    await orchestrator.start()


@app.on_event("shutdown") 
async def shutdown():
    await orchestrator.stop()


if __name__ == "__main__":
    orchestrator.run()