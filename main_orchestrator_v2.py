"""
Main Orchestrator V2 - A2A 프로토콜 기반

에이전트 간 직접 통신을 지원하는 새로운 오케스트레이터
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType, Priority


class OrchestratorV2(BaseAgent):
    """A2A 오케스트레이터 V2"""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator V2",
            description="A2A 기반 투자 분석 시스템 오케스트레이터",
            port=8100,  # 새로운 포트
            registry_url="http://localhost:8001"
        )
        
        # WebSocket 연결 관리
        self.active_websockets: List[WebSocket] = []
        
        # 분석 세션 관리
        self.analysis_sessions: Dict[str, Dict] = {}
        
        # CORS 설정
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 웹 라우트 추가
        self._setup_web_routes()
        
    def _setup_web_routes(self):
        """웹 인터페이스 라우트 설정"""
        
        @self.app.get("/")
        async def read_index():
            return FileResponse("index.html")
            
        @self.app.websocket("/ws/v2")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                # 초기 데이터 수신
                init_data = await websocket.receive_json()
                user_query = init_data.get("query")
                
                # 분석 세션 시작
                session_id = await self.start_analysis_session(user_query, websocket)
                
                # 연결 유지
                while True:
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.active_websockets.remove(websocket)
                print("WebSocket 연결 종료")
                
    async def on_start(self):
        """오케스트레이터 시작"""
        # 능력 등록
        await self.register_capability({
            "name": "orchestrate_analysis",
            "version": "2.0",
            "description": "투자 분석 워크플로우 조율",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "사용자 질문"}
                },
                "required": ["query"]
            }
        })
        
        print("✅ Orchestrator V2 초기화 완료")
        
    async def on_stop(self):
        """오케스트레이터 종료"""
        # 모든 WebSocket 연결 종료
        for ws in self.active_websockets:
            await ws.close()
            
        print("🛑 Orchestrator V2 종료")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            if message.header.message_type == MessageType.RESPONSE:
                # 응답 메시지 처리
                correlation_id = message.header.correlation_id
                if correlation_id in self.analysis_sessions:
                    session = self.analysis_sessions[correlation_id]
                    await self._handle_agent_response(session, message)
                    
            elif message.header.message_type == MessageType.EVENT:
                # 이벤트 처리
                event_type = message.body.get("event_type")
                await self._handle_event(event_type, message)
                
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            
    async def start_analysis_session(self, query: str, websocket: WebSocket) -> str:
        """분석 세션 시작"""
        import uuid
        session_id = str(uuid.uuid4())
        
        # 세션 정보 저장
        self.analysis_sessions[session_id] = {
            "query": query,
            "websocket": websocket,
            "state": "started",
            "results": {}
        }
        
        # UI 상태 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "orchestrator"})
        await self._send_to_ui(websocket, "log", {"message": f"🚀 A2A 분석 시작: {query}"})
        
        # Step 1: NLU 에이전트 찾기 및 호출
        nlu_agents = await self.discover_agents("extract_ticker")
        
        if not nlu_agents:
            await self._send_to_ui(websocket, "log", {"message": "❌ NLU 에이전트를 찾을 수 없습니다"})
            return session_id
            
        # 첫 번째 NLU 에이전트에게 요청
        nlu_agent = nlu_agents[0]
        
        await self._send_to_ui(websocket, "status", {"agentId": "nlu-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"🔍 질문 분석 중: {nlu_agent.name}"})
        
        # 메시지 전송
        request_message = await self.send_message(
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": query},
            priority=Priority.HIGH,
            require_ack=True
        )
        
        if request_message:
            # 세션에 요청 정보 저장
            self.analysis_sessions[session_id]["nlu_request_id"] = request_message.header.message_id
            self.analysis_sessions[session_id]["state"] = "waiting_nlu"
            
        return session_id
        
    async def _handle_agent_response(self, session: Dict, message: A2AMessage):
        """에이전트 응답 처리"""
        websocket = session["websocket"]
        state = session["state"]
        
        if state == "waiting_nlu":
            # NLU 응답 처리
            result = message.body.get("result", {})
            ticker = result.get("ticker")
            
            await self._send_to_ui(websocket, "log", {"message": result.get("log_message", "")})
            
            if ticker:
                session["ticker"] = ticker
                session["state"] = "collecting_data"
                
                # 데이터 수집 에이전트들 찾기
                await self._start_data_collection(session)
            else:
                await self._send_to_ui(websocket, "log", {"message": "❌ 티커를 찾을 수 없습니다"})
                
        elif state == "collecting_data":
            # 데이터 수집 응답 처리
            sender_id = message.header.sender_id
            result = message.body.get("result", {})
            
            # 결과 저장
            if "collected_data" not in session:
                session["collected_data"] = []
                
            session["collected_data"].extend(result.get("data", []))
            
            # 로그 출력
            for item in result.get("data", []):
                await self._send_to_ui(websocket, "log", {"message": item.get("log_message", "")})
                
            # 모든 데이터 수집 완료 확인
            # TODO: 실제로는 모든 에이전트의 응답을 기다려야 함
            
        # 추가 상태 처리...
        
    async def _start_data_collection(self, session: Dict):
        """데이터 수집 시작"""
        ticker = session["ticker"]
        websocket = session["websocket"]
        
        await self._send_to_ui(websocket, "status", {"agentId": "data-collection"})
        await self._send_to_ui(websocket, "log", {"message": "📊 데이터 수집 시작..."})
        
        # 각 데이터 수집 에이전트 찾기
        data_agents = {
            "news": await self.discover_agents("collect_news"),
            "twitter": await self.discover_agents("collect_tweets"),
            "sec": await self.discover_agents("collect_filings")
        }
        
        # 병렬로 데이터 수집 요청
        tasks = []
        for agent_type, agents in data_agents.items():
            if agents:
                agent = agents[0]
                task = self.send_message(
                    receiver_id=agent.agent_id,
                    action=f"collect_{agent_type}",
                    payload={"ticker": ticker},
                    priority=Priority.HIGH
                )
                tasks.append(task)
                
        # 모든 요청 동시 전송
        await asyncio.gather(*tasks)
        
    async def _handle_event(self, event_type: str, message: A2AMessage):
        """이벤트 처리"""
        event_data = message.body.get("event_data", {})
        
        if event_type == "ticker_extracted":
            # 티커 추출 이벤트
            ticker = event_data.get("ticker")
            print(f"📢 티커 추출 이벤트: {ticker}")
            
        elif event_type == "data_collected":
            # 데이터 수집 완료 이벤트
            source = event_data.get("source")
            count = event_data.get("count")
            print(f"📢 데이터 수집 완료: {source} ({count}개)")
            
        # 추가 이벤트 처리...
        
    async def _send_to_ui(self, websocket: WebSocket, msg_type: str, payload: Dict[str, Any]):
        """UI로 메시지 전송"""
        try:
            await websocket.send_json({"type": msg_type, "payload": payload})
        except:
            print("UI 전송 실패")
            

# 독립 실행용
if __name__ == "__main__":
    orchestrator = OrchestratorV2()
    
    @orchestrator.app.on_event("startup")
    async def startup():
        await orchestrator.start()
        
    @orchestrator.app.on_event("shutdown")
    async def shutdown():
        await orchestrator.stop()
        
    orchestrator.run()