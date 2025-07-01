"""
pytest 설정 및 공통 fixtures
"""

import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient
from a2a_core.protocols.message import A2AMessage, MessageType, Priority
from a2a_core.registry.service_registry import ServiceRegistry, AgentInfo


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def service_registry():
    """서비스 레지스트리 fixture"""
    registry = ServiceRegistry()
    yield registry


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP 클라이언트 fixture"""
    async with AsyncClient(base_url="http://localhost:8001") as client:
        yield client


@pytest.fixture
def sample_agent_info():
    """샘플 에이전트 정보"""
    return AgentInfo(
        agent_id="test-agent-123",
        name="Test Agent",
        description="테스트용 에이전트",
        endpoint="http://localhost:9999",
        capabilities=[
            {
                "name": "test_capability",
                "version": "1.0",
                "description": "테스트 능력"
            }
        ],
        status="active"
    )


@pytest.fixture
def sample_message():
    """샘플 A2A 메시지"""
    return A2AMessage.create_request(
        sender_id="sender-123",
        receiver_id="receiver-456",
        action="test_action",
        payload={"test": "data"}
    )


@pytest.fixture
async def mock_agent_server(unused_tcp_port_factory):
    """목업 에이전트 서버"""
    from fastapi import FastAPI
    import uvicorn
    from threading import Thread
    
    port = unused_tcp_port_factory()
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.post("/message")
    async def receive_message(message: dict):
        return {"status": "received", "message_id": message.get("header", {}).get("message_id")}
    
    # 서버를 별도 스레드에서 실행
    server = uvicorn.Server(
        config=uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error")
    )
    thread = Thread(target=server.run)
    thread.daemon = True
    thread.start()
    
    # 서버가 시작될 때까지 대기
    await asyncio.sleep(0.5)
    
    yield f"http://localhost:{port}"
    
    # 서버 종료
    server.should_exit = True
    thread.join(timeout=5)