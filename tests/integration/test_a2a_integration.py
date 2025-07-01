"""
A2A 시스템 통합 테스트

전체 시스템의 통합 동작을 검증하는 테스트
"""

import pytest
import asyncio
import httpx
from unittest.mock import patch
from a2a_core.registry.service_registry import ServiceRegistry, AgentInfo
from a2a_core.protocols.message import A2AMessage, MessageType
from agents.nlu_agent_v2 import NLUAgentV2


class TestA2AIntegration:
    """A2A 시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_agent_registration_and_discovery(self):
        """에이전트 등록 및 발견 통합 테스트"""
        # Given: 서비스 레지스트리
        registry = ServiceRegistry()
        
        # When: 여러 에이전트를 등록
        nlu_agent_info = AgentInfo(
            agent_id="nlu-001",
            name="NLU Agent",
            description="자연어 처리",
            endpoint="http://localhost:8108",
            capabilities=[{"name": "extract_ticker", "version": "2.0"}],
            status="active"
        )
        
        news_agent_info = AgentInfo(
            agent_id="news-001",
            name="News Agent",
            description="뉴스 수집",
            endpoint="http://localhost:8107",
            capabilities=[{"name": "collect_news", "version": "1.0"}],
            status="active"
        )
        
        await registry.register_agent(nlu_agent_info)
        await registry.register_agent(news_agent_info)
        
        # Then: 능력별로 에이전트를 발견할 수 있어야 함
        nlu_agents = await registry.discover_agents("extract_ticker")
        assert len(nlu_agents) == 1
        assert nlu_agents[0].name == "NLU Agent"
        
        news_agents = await registry.discover_agents("collect_news")
        assert len(news_agents) == 1
        assert news_agents[0].name == "News Agent"
        
        # 모든 에이전트 발견
        all_agents = await registry.discover_agents()
        assert len(all_agents) == 2
        
    @pytest.mark.asyncio
    async def test_message_flow_between_agents(self):
        """에이전트 간 메시지 흐름 테스트"""
        # Given: Mock 에이전트들
        sender_agent = {
            "agent_id": "sender-001",
            "message_queue": asyncio.Queue(),
            "received_responses": []
        }
        
        receiver_agent = {
            "agent_id": "receiver-001",
            "message_queue": asyncio.Queue(),
            "received_requests": []
        }
        
        # When: 요청 메시지 전송
        request = A2AMessage.create_request(
            sender_id=sender_agent["agent_id"],
            receiver_id=receiver_agent["agent_id"],
            action="process_data",
            payload={"data": [1, 2, 3]}
        )
        
        await receiver_agent["message_queue"].put(request)
        
        # 수신자가 메시지 처리
        received_msg = await receiver_agent["message_queue"].get()
        assert received_msg.body["action"] == "process_data"
        
        # 응답 생성
        response = A2AMessage.create_response(
            original_message=received_msg,
            sender_id=receiver_agent["agent_id"],
            result={"processed": True, "count": 3},
            success=True
        )
        
        await sender_agent["message_queue"].put(response)
        
        # Then: 발신자가 응답 수신
        received_response = await sender_agent["message_queue"].get()
        assert received_response.header.correlation_id == request.header.message_id
        assert received_response.body["success"] is True
        assert received_response.body["result"]["count"] == 3
        
    @pytest.mark.asyncio
    async def test_event_broadcasting(self):
        """이벤트 브로드캐스팅 통합 테스트"""
        # Given: 여러 에이전트의 메시지 큐
        agent_queues = {
            "agent-1": asyncio.Queue(),
            "agent-2": asyncio.Queue(),
            "agent-3": asyncio.Queue()
        }
        
        # When: 이벤트 브로드캐스트
        event = A2AMessage.create_event(
            sender_id="broadcaster",
            event_type="system_alert",
            event_data={"level": "warning", "message": "High load detected"}
        )
        
        # 모든 에이전트에게 이벤트 전송 (브로드캐스터 제외)
        for agent_id, queue in agent_queues.items():
            await queue.put(event)
            
        # Then: 모든 에이전트가 이벤트를 수신
        for agent_id, queue in agent_queues.items():
            received_event = await queue.get()
            assert received_event.header.message_type == MessageType.EVENT
            assert received_event.body["event_type"] == "system_alert"
            assert received_event.body["event_data"]["level"] == "warning"
            
    @pytest.mark.asyncio
    async def test_nlu_agent_integration(self):
        """NLU 에이전트 통합 테스트"""
        # Given: NLU 에이전트 인스턴스
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            nlu_agent = NLUAgentV2()
            
            # 가상의 레지스트리 등록
            with patch.object(nlu_agent, '_register_to_registry', new_callable=AsyncMock):
                with patch.object(nlu_agent, '_heartbeat_loop', new_callable=AsyncMock):
                    with patch.object(nlu_agent, 'broadcast_event', new_callable=AsyncMock):
                        # When: 티커 추출 요청
                        request = A2AMessage.create_request(
                            sender_id="orchestrator",
                            receiver_id=nlu_agent.agent_id,
                            action="extract_ticker",
                            payload={"query": "테슬라 주가 전망이 어떻습니까?"}
                        )
                        
                        # 응답을 저장할 mock
                        responses = []
                        async def mock_reply(msg, result, success):
                            responses.append((result, success))
                            
                        nlu_agent.reply_to_message = mock_reply
                        
                        # 메시지 처리
                        await nlu_agent.handle_message(request)
                        
                        # Then: 올바른 응답이 생성되어야 함
                        assert len(responses) == 1
                        result, success = responses[0]
                        assert success is True
                        assert result["ticker"] == "TSLA"
                        assert result["company_name"] == "테슬라"
                        
                        # 이벤트가 브로드캐스트되어야 함
                        nlu_agent.broadcast_event.assert_called_once()
                        
    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self):
        """하트비트 메커니즘 통합 테스트"""
        # Given: 레지스트리와 에이전트
        registry = ServiceRegistry()
        
        agent_info = AgentInfo(
            agent_id="test-agent",
            name="Test Agent",
            description="테스트",
            endpoint="http://localhost:9999",
            capabilities=[],
            status="active"
        )
        
        # When: 에이전트 등록 후 하트비트 업데이트
        await registry.register_agent(agent_info)
        initial_heartbeat = agent_info.last_heartbeat
        
        await asyncio.sleep(0.1)
        await registry.update_heartbeat("test-agent")
        
        # Then: 하트비트가 업데이트되어야 함
        updated_agent = await registry.get_agent_info("test-agent")
        assert updated_agent.last_heartbeat > initial_heartbeat
        
    @pytest.mark.asyncio
    async def test_error_handling_flow(self):
        """에러 처리 흐름 통합 테스트"""
        # Given: 에러를 발생시키는 상황
        request = A2AMessage.create_request(
            sender_id="client",
            receiver_id="service",
            action="invalid_action",
            payload={}
        )
        
        # When: 에러 응답 생성
        error_response = A2AMessage.create_error(
            sender_id="service",
            receiver_id="client",
            error_code="ACTION_NOT_FOUND",
            error_message="The requested action 'invalid_action' is not supported",
            correlation_id=request.header.message_id
        )
        
        # Then: 에러 응답이 올바른 구조를 가져야 함
        assert error_response.header.message_type == MessageType.ERROR
        assert error_response.header.correlation_id == request.header.message_id
        assert error_response.body["error_code"] == "ACTION_NOT_FOUND"
        assert "invalid_action" in error_response.body["error_message"]
        
    @pytest.mark.asyncio
    async def test_service_registry_api(self):
        """서비스 레지스트리 API 통합 테스트"""
        # Given: FastAPI 테스트 클라이언트
        from fastapi.testclient import TestClient
        from a2a_core.registry.service_registry import app
        
        client = TestClient(app)
        
        # When: 에이전트 등록 API 호출
        agent_data = {
            "agent_id": "api-test-agent",
            "name": "API Test Agent",
            "description": "API 테스트용",
            "endpoint": "http://localhost:7777",
            "capabilities": [{"name": "test_cap", "version": "1.0"}],
            "status": "active"
        }
        
        response = client.post("/register", json=agent_data)
        
        # Then: 성공 응답
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        
        # 등록된 에이전트 조회
        response = client.get(f"/agents/{agent_data['agent_id']}")
        assert response.status_code == 200
        agent_info = response.json()
        assert agent_info["name"] == "API Test Agent"
        
        # 에이전트 발견
        response = client.get("/discover?capability=test_cap")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        
        # 등록 해제
        response = client.delete(f"/register/{agent_data['agent_id']}")
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_message_priority_handling(self):
        """메시지 우선순위 처리 통합 테스트"""
        # Given: 다양한 우선순위의 메시지들
        messages = []
        
        for priority in ["low", "normal", "high", "urgent"]:
            msg = A2AMessage.create_request(
                sender_id="sender",
                receiver_id="receiver",
                action="priority_test",
                payload={"priority": priority}
            )
            msg.metadata.priority = priority
            messages.append(msg)
            
        # When: 우선순위별로 정렬
        sorted_messages = sorted(
            messages,
            key=lambda m: ["low", "normal", "high", "urgent"].index(m.metadata.priority.value),
            reverse=True
        )
        
        # Then: urgent가 먼저 처리되어야 함
        assert sorted_messages[0].metadata.priority.value == "urgent"
        assert sorted_messages[-1].metadata.priority.value == "low"