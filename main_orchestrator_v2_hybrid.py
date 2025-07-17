"""
Main Orchestrator V2 - Hybrid (A2A + HTTP)
점진적으로 A2A 프로토콜을 적용하는 하이브리드 버전
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


class OrchestratorV2Hybrid(BaseAgent):
    """하이브리드 오케스트레이터 - A2A와 HTTP를 함께 사용"""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator V2 Hybrid",
            description="A2A와 HTTP를 함께 사용하는 투자 분석 시스템 오케스트레이터",
            port=8100,
            registry_url="http://localhost:8001"
        )
        
        # WebSocket 연결 관리
        self.active_websockets: List[WebSocket] = []
        
        # 분석 세션 관리
        self.analysis_sessions: Dict[str, Dict] = {}
        
        # API Key 설정
        self.api_key = os.getenv("A2A_API_KEY", "default-api-key-change-me")
        
        # A2A 지원 에이전트 목록
        self.a2a_enabled_agents = ["nlu-agent", "sentiment-agent", "report-agent"]
        
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
            print(f"🔌 WebSocket 연결: {client_id}")
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                await self._handle_websocket(websocket, client_id)
            except WebSocketDisconnect:
                print(f"🔌 WebSocket 연결 종료: {client_id}")
            finally:
                if websocket in self.active_websockets:
                    self.active_websockets.remove(websocket)

    async def on_start(self):
        """에이전트 시작 시 초기화"""
        print(f"✅ {self.name} 시작됨 (하이브리드 모드)")
        print(f"📡 A2A 지원 에이전트: {', '.join(self.a2a_enabled_agents)}")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print(f"🛑 {self.name} 종료됨")

    async def handle_message(self, message: A2AMessage):
        """A2A 메시지 처리"""
        print(f"📨 A2A 메시지 수신: {message.header.action} from {message.header.sender_id}")
        
        # NLU 응답 처리
        if message.header.sender_id == "nlu-agent" and message.header.message_type == MessageType.RESPONSE:
            session_id = message.header.correlation_id.split("-")[0]
            if session_id in self.analysis_sessions:
                session = self.analysis_sessions[session_id]
                
                if message.body.get("success"):
                    result = message.body.get("result", {})
                    session["ticker"] = result.get("ticker")
                    session["exchange"] = result.get("exchange", "US")
                    
                    await self._send_to_ui(session.get("client_id"), "log", {
                        "message": f"✅ 티커 추출 (A2A): {session['ticker']} ({session['exchange']})"
                    })
                    
                    # 데이터 수집은 HTTP로 진행
                    session["state"] = "collecting_data"
                    await self._start_data_collection_http(session)

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
                        "state": "initializing",
                        "websocket": websocket
                    }
                    
                    # NLU는 A2A로 처리
                    await self._start_nlu_processing_a2a(self.analysis_sessions[session_id])
                
        except WebSocketDisconnect:
            print(f"WebSocket 연결 종료: {client_id}")

    async def _start_nlu_processing_a2a(self, session: Dict):
        """A2A 프로토콜을 사용한 NLU 처리"""
        query = session["query"]
        session_id = session["session_id"]
        
        # UI 업데이트
        await self._send_to_ui(session.get("client_id"), "status", {"agentId": "nlu"})
        await self._send_to_ui(session.get("client_id"), "log", {"message": f"🔍 쿼리 분석 중 (A2A): {query}"})
        
        # A2A 메시지로 NLU 요청
        message = await self.send_message(
            receiver_id="nlu-agent",
            action="extract_ticker",
            payload={"query": query},
            priority=Priority.HIGH
        )
        
        if message:
            # correlation_id 저장
            message.header.correlation_id = f"{session_id}-nlu"
            print(f"✅ NLU 에이전트에 A2A 메시지 전송 완료")
        else:
            # 실패 시 HTTP로 폴백
            print(f"⚠️ A2A 실패, HTTP로 폴백")
            await self._start_nlu_processing_http(session)

    async def _start_nlu_processing_http(self, session: Dict):
        """HTTP를 사용한 NLU 처리 (폴백)"""
        query = session["query"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8108/extract_ticker",
                    json={"query": query},
                    headers={"X-API-Key": self.api_key}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    session["ticker"] = result.get("ticker")
                    session["exchange"] = result.get("exchange", "US")
                    
                    await self._send_to_ui(session.get("client_id"), "log", {
                        "message": f"✅ 티커 추출 (HTTP): {session['ticker']} ({session['exchange']})"
                    })
                    
                    # 데이터 수집 시작
                    session["state"] = "collecting_data"
                    await self._start_data_collection_http(session)
                    
        except Exception as e:
            print(f"❌ NLU 처리 실패: {e}")

    async def _start_data_collection_http(self, session: Dict):
        """HTTP를 사용한 데이터 수집"""
        ticker = session["ticker"]
        exchange = session.get("exchange", "US")
        
        # UI 업데이트
        await self._send_to_ui(session.get("client_id"), "status", {"agentId": "data-collection"})
        await self._send_to_ui(session.get("client_id"), "log", {"message": "📊 데이터 수집 시작 (HTTP)..."})
        
        # 에이전트 선택
        if exchange == "KRX":
            agent_ports = {
                "news": 8307,
                "twitter": 8209,
                "dart": 8213,
                "mcp": 8215
            }
        else:
            agent_ports = {
                "news": 8307,
                "twitter": 8209,
                "sec": 8210,
                "mcp": 8215
            }
        
        # 병렬 데이터 수집
        tasks = []
        for agent_type, port in agent_ports.items():
            task = self._collect_data_from_agent(ticker, agent_type, port)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 저장
        session["collected_data"] = {}
        for i, (agent_type, _) in enumerate(agent_ports.items()):
            if isinstance(results[i], Exception):
                session["collected_data"][agent_type] = []
                await self._send_to_ui(session.get("client_id"), "log", {
                    "message": f"⚠️ {agent_type.upper()} 데이터 수집 실패"
                })
            else:
                session["collected_data"][agent_type] = results[i]
                await self._send_to_ui(session.get("client_id"), "log", {
                    "message": f"✅ {agent_type.upper()} 데이터 수집 완료: {len(results[i])}건"
                })
        
        # 감성 분석으로 진행
        session["state"] = "analyzing_sentiment"
        await self._start_sentiment_analysis(session)

    async def _collect_data_from_agent(self, ticker: str, agent_type: str, port: int):
        """개별 에이전트로부터 데이터 수집"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if agent_type == "dart":
                    endpoint = f"http://localhost:{port}/collect_dart"
                else:
                    endpoint = f"http://localhost:{port}/collect_{agent_type}_data"
                
                response = await client.post(
                    endpoint,
                    json={"ticker": ticker},
                    headers={"X-API-Key": self.api_key}
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            print(f"❌ {agent_type} 데이터 수집 실패: {e}")
            return []

    async def _start_sentiment_analysis(self, session: Dict):
        """감성 분석 시작"""
        # A2A 지원 에이전트면 A2A로, 아니면 HTTP로
        if "sentiment-agent" in self.a2a_enabled_agents:
            await self._send_to_ui(session.get("client_id"), "log", {"message": "🧠 감성 분석 시작 (A2A)..."})
            # A2A 구현...
        else:
            await self._send_to_ui(session.get("client_id"), "log", {"message": "🧠 감성 분석 시작 (HTTP)..."})
            # 기존 HTTP 방식 사용
            
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


# 모듈 레벨에서 오케스트레이터와 app 생성
orchestrator = OrchestratorV2Hybrid()
app = orchestrator.app
print(f"✅ {orchestrator.name} 초기화 완료 (하이브리드 모드)")


@app.on_event("startup")
async def startup():
    await orchestrator.start()


@app.on_event("shutdown") 
async def shutdown():
    await orchestrator.stop()


if __name__ == "__main__":
    orchestrator.run()