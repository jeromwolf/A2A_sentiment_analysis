"""
베이스 에이전트 단위 테스트

TDD 방식으로 작성된 베이스 에이전트 동작 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType, Priority


class TestAgent(BaseAgent):
    """테스트용 구체 에이전트 구현"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handled_messages = []
        self.started = False
        self.stopped = False
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리 구현"""
        self.handled_messages.append(message)
        
    async def on_start(self):
        """시작 시 호출"""
        self.started = True
        
    async def on_stop(self):
        """종료 시 호출"""
        self.stopped = True


class TestBaseAgent:
    """베이스 에이전트 테스트"""
    
    @pytest.fixture
    def test_agent(self):
        """테스트 에이전트 fixture"""
        return TestAgent(
            name="Test Agent",
            description="테스트용 에이전트",
            port=9999,
            registry_url="http://localhost:8001"
        )
        
    def test_agent_initialization(self, test_agent):
        """에이전트 초기화 테스트"""
        # Then: 올바르게 초기화되어야 함
        assert test_agent.name == "Test Agent"
        assert test_agent.description == "테스트용 에이전트"
        assert test_agent.port == 9999
        assert test_agent.endpoint == "http://localhost:9999"
        assert test_agent.agent_id is not None
        assert len(test_agent.agent_id) == 36  # UUID
        assert test_agent.capabilities == []
        
    @pytest.mark.asyncio
    async def test_register_capability(self, test_agent):
        """능력 등록 테스트"""
        # Given: 능력 정의
        capability = {
            "name": "test_capability",
            "version": "1.0",
            "description": "테스트 능력"
        }
        
        # When: 능력을 등록하면
        await test_agent.register_capability(capability)
        
        # Then: 능력 목록에 추가되어야 함
        assert len(test_agent.capabilities) == 1
        assert test_agent.capabilities[0]["name"] == "test_capability"
        
    @pytest.mark.asyncio
    async def test_agent_start_process(self, test_agent):
        """에이전트 시작 프로세스 테스트"""
        # Given: Mock HTTP 클라이언트
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock 레지스트리 응답
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.put.return_value = mock_response
            
            # When: 에이전트를 시작하면
            await test_agent.start()
            
            # Then: 초기화 과정이 실행되어야 함
            assert test_agent.http_client is not None
            assert test_agent.started is True  # on_start 호출됨
            assert test_agent.heartbeat_task is not None
            
            # 레지스트리에 등록 시도
            mock_client.post.assert_called()
            register_call = mock_client.post.call_args
            assert "register" in register_call[0][0]
            
    @pytest.mark.asyncio
    async def test_agent_stop_process(self, test_agent):
        """에이전트 종료 프로세스 테스트"""
        # Given: 시작된 에이전트
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.post.return_value = Mock(status_code=200)
            mock_client.delete.return_value = Mock(status_code=200)
            
            await test_agent.start()
            
            # When: 에이전트를 종료하면
            await test_agent.stop()
            
            # Then: 정리 과정이 실행되어야 함
            assert test_agent.stopped is True  # on_stop 호출됨
            assert test_agent.heartbeat_task.cancelled()
            
            # 레지스트리에서 등록 해제 시도
            mock_client.delete.assert_called()
            
    @pytest.mark.asyncio
    async def test_send_message(self, test_agent):
        """메시지 전송 테스트"""
        # Given: Mock 설정
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # 수신자 정보 응답
            receiver_info = {
                "agent_id": "receiver-123",
                "name": "Receiver Agent",
                "endpoint": "http://localhost:8888"
            }
            mock_client.get.return_value = Mock(
                status_code=200,
                json=lambda: receiver_info
            )
            
            # 메시지 전송 성공 응답
            mock_client.post.return_value = Mock(status_code=200)
            
            await test_agent.start()
            
            # When: 메시지를 전송하면
            sent_message = await test_agent.send_message(
                receiver_id="receiver-123",
                action="test_action",
                payload={"data": "test"},
                priority=Priority.HIGH,
                require_ack=True
            )
            
            # Then: 올바른 메시지가 전송되어야 함
            assert sent_message is not None
            assert sent_message.header.sender_id == test_agent.agent_id
            assert sent_message.header.receiver_id == "receiver-123"
            assert sent_message.body["action"] == "test_action"
            assert sent_message.metadata.priority == Priority.HIGH
            assert sent_message.metadata.require_ack is True
            
    @pytest.mark.asyncio
    async def test_discover_agents(self, test_agent):
        """에이전트 발견 테스트"""
        # Given: Mock 설정
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # 발견된 에이전트 목록
            discovered_agents = {
                "agents": [
                    {
                        "agent_id": "agent-1",
                        "name": "Agent 1",
                        "endpoint": "http://localhost:8001",
                        "capabilities": [{"name": "capability_a"}],
                        "status": "active"
                    },
                    {
                        "agent_id": "agent-2",
                        "name": "Agent 2",
                        "endpoint": "http://localhost:8002",
                        "capabilities": [{"name": "capability_b"}],
                        "status": "active"
                    }
                ]
            }
            mock_client.get.return_value = Mock(
                status_code=200,
                json=lambda: discovered_agents
            )
            
            await test_agent.start()
            
            # When: 에이전트를 발견하면
            agents = await test_agent.discover_agents("capability_a")
            
            # Then: 에이전트 목록이 반환되어야 함
            assert len(agents) == 2
            assert agents[0].agent_id == "agent-1"
            assert agents[1].agent_id == "agent-2"
            
            # 캐시에 저장되어야 함
            assert "agent-1" in test_agent.known_agents
            assert "agent-2" in test_agent.known_agents
            
    @pytest.mark.asyncio
    async def test_broadcast_event(self, test_agent):
        """이벤트 브로드캐스트 테스트"""
        # Given: Mock 설정
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # 발견된 에이전트들
            discovered_agents = {
                "agents": [
                    {
                        "agent_id": "agent-1",
                        "name": "Agent 1",
                        "endpoint": "http://localhost:8001",
                        "capabilities": [],
                        "status": "active"
                    },
                    {
                        "agent_id": test_agent.agent_id,  # 자기 자신
                        "name": test_agent.name,
                        "endpoint": test_agent.endpoint,
                        "capabilities": [],
                        "status": "active"
                    }
                ]
            }
            mock_client.get.return_value = Mock(
                status_code=200,
                json=lambda: discovered_agents
            )
            mock_client.post.return_value = Mock(status_code=200)
            
            await test_agent.start()
            
            # When: 이벤트를 브로드캐스트하면
            await test_agent.broadcast_event(
                event_type="test_event",
                event_data={"info": "broadcast test"}
            )
            
            # Then: 자기 자신을 제외한 모든 에이전트에게 전송
            # post 호출 중 레지스트리 등록 제외
            post_calls = [call for call in mock_client.post.call_args_list 
                         if "message" in str(call)]
            assert len(post_calls) == 1  # 자기 자신 제외
            
    @pytest.mark.asyncio
    async def test_message_queue_processing(self, test_agent):
        """메시지 큐 처리 테스트"""
        # Given: 시작된 에이전트
        with patch('httpx.AsyncClient'):
            await test_agent.start()
            
            # When: 메시지를 큐에 추가하면
            test_message = A2AMessage.create_request(
                sender_id="sender-123",
                receiver_id=test_agent.agent_id,
                action="test_action",
                payload={"test": "data"}
            )
            
            await test_agent.message_queue.put(test_message)
            
            # 메시지 처리를 위해 잠시 대기
            await asyncio.sleep(0.1)
            
            # Then: handle_message가 호출되어야 함
            assert len(test_agent.handled_messages) == 1
            assert test_agent.handled_messages[0] == test_message
            
    @pytest.mark.asyncio
    async def test_expired_message_handling(self, test_agent):
        """만료된 메시지 처리 테스트"""
        # Given: 만료된 메시지
        with patch('httpx.AsyncClient'):
            await test_agent.start()
            
            expired_message = A2AMessage.create_request(
                sender_id="sender-123",
                receiver_id=test_agent.agent_id,
                action="old_action",
                payload={}
            )
            expired_message.metadata.ttl = 1
            expired_message.header.timestamp = datetime.now() - timedelta(seconds=2)
            
            # When: 만료된 메시지를 큐에 추가
            await test_agent.message_queue.put(expired_message)
            await asyncio.sleep(0.1)
            
            # Then: 메시지가 처리되지 않아야 함
            assert len(test_agent.handled_messages) == 0
            
    def test_health_endpoint(self, test_agent):
        """헬스체크 엔드포인트 테스트"""
        # Given: FastAPI 테스트 클라이언트
        from fastapi.testclient import TestClient
        client = TestClient(test_agent.app)
        
        # When: 헬스체크 요청
        response = client.get("/health")
        
        # Then: 상태 정보 반환
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent_id"] == test_agent.agent_id
        assert data["name"] == test_agent.name
        assert "timestamp" in data
        
    def test_capabilities_endpoint(self, test_agent):
        """능력 조회 엔드포인트 테스트"""
        # Given: 능력이 등록된 에이전트
        test_agent.capabilities = [
            {"name": "capability_1", "version": "1.0"},
            {"name": "capability_2", "version": "2.0"}
        ]
        
        from fastapi.testclient import TestClient
        client = TestClient(test_agent.app)
        
        # When: 능력 조회 요청
        response = client.get("/capabilities")
        
        # Then: 능력 목록 반환
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == test_agent.agent_id
        assert len(data["capabilities"]) == 2
        assert data["capabilities"][0]["name"] == "capability_1"


from datetime import datetime, timedelta