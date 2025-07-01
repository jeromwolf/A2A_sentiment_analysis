"""
서비스 레지스트리 단위 테스트

TDD 방식으로 작성된 테스트
"""

import pytest
from datetime import datetime, timedelta
from a2a_core.registry.service_registry import ServiceRegistry, AgentInfo


class TestServiceRegistry:
    """서비스 레지스트리 테스트"""
    
    @pytest.mark.asyncio
    async def test_register_agent(self, service_registry, sample_agent_info):
        """에이전트 등록 테스트"""
        # When: 에이전트를 등록하면
        result = await service_registry.register_agent(sample_agent_info)
        
        # Then: 성공적으로 등록되어야 함
        assert result["status"] == "registered"
        assert sample_agent_info.agent_id in service_registry.agents
        assert service_registry.agents[sample_agent_info.agent_id].name == "Test Agent"
        
    @pytest.mark.asyncio
    async def test_register_agent_without_id(self, service_registry):
        """ID 없이 에이전트 등록 테스트"""
        # Given: ID가 없는 에이전트 정보
        agent_info = AgentInfo(
            agent_id="",
            name="No ID Agent",
            description="ID 없는 에이전트",
            endpoint="http://localhost:8888",
            capabilities=[],
            status="active"
        )
        
        # When: 등록하면
        result = await service_registry.register_agent(agent_info)
        
        # Then: 자동으로 ID가 생성되어야 함
        assert result["status"] == "registered"
        assert agent_info.agent_id != ""
        assert len(agent_info.agent_id) == 36  # UUID 길이
        
    @pytest.mark.asyncio
    async def test_deregister_agent(self, service_registry, sample_agent_info):
        """에이전트 등록 해제 테스트"""
        # Given: 등록된 에이전트
        await service_registry.register_agent(sample_agent_info)
        
        # When: 등록을 해제하면
        result = await service_registry.deregister_agent(sample_agent_info.agent_id)
        
        # Then: 레지스트리에서 제거되어야 함
        assert result["status"] == "deregistered"
        assert sample_agent_info.agent_id not in service_registry.agents
        
    @pytest.mark.asyncio
    async def test_deregister_nonexistent_agent(self, service_registry):
        """존재하지 않는 에이전트 등록 해제 시 예외 발생"""
        # When & Then: 존재하지 않는 에이전트 해제 시 예외
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service_registry.deregister_agent("nonexistent-id")
        assert exc_info.value.status_code == 404
        
    @pytest.mark.asyncio
    async def test_update_heartbeat(self, service_registry, sample_agent_info):
        """하트비트 업데이트 테스트"""
        # Given: 등록된 에이전트
        await service_registry.register_agent(sample_agent_info)
        original_heartbeat = sample_agent_info.last_heartbeat
        
        # When: 하트비트를 업데이트하면
        await asyncio.sleep(0.1)  # 시간 차이를 위해
        result = await service_registry.update_heartbeat(sample_agent_info.agent_id)
        
        # Then: 타임스탬프가 업데이트되어야 함
        assert result["status"] == "ok"
        updated_agent = service_registry.agents[sample_agent_info.agent_id]
        assert updated_agent.last_heartbeat > original_heartbeat
        
    @pytest.mark.asyncio
    async def test_discover_all_agents(self, service_registry):
        """모든 활성 에이전트 발견 테스트"""
        # Given: 여러 에이전트 등록
        agents = []
        for i in range(3):
            agent = AgentInfo(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                description=f"테스트 에이전트 {i}",
                endpoint=f"http://localhost:900{i}",
                capabilities=[],
                status="active",
                last_heartbeat=datetime.now()
            )
            await service_registry.register_agent(agent)
            agents.append(agent)
            
        # When: 모든 에이전트를 발견하면
        discovered = await service_registry.discover_agents()
        
        # Then: 모든 활성 에이전트가 반환되어야 함
        assert len(discovered) == 3
        discovered_ids = {agent.agent_id for agent in discovered}
        assert discovered_ids == {"agent-0", "agent-1", "agent-2"}
        
    @pytest.mark.asyncio
    async def test_discover_agents_by_capability(self, service_registry):
        """능력별 에이전트 발견 테스트"""
        # Given: 다른 능력을 가진 에이전트들
        agent1 = AgentInfo(
            agent_id="nlp-agent",
            name="NLP Agent",
            description="자연어 처리",
            endpoint="http://localhost:9001",
            capabilities=[{"name": "extract_ticker", "version": "1.0"}],
            status="active",
            last_heartbeat=datetime.now()
        )
        
        agent2 = AgentInfo(
            agent_id="data-agent",
            name="Data Agent",
            description="데이터 수집",
            endpoint="http://localhost:9002",
            capabilities=[{"name": "collect_news", "version": "1.0"}],
            status="active",
            last_heartbeat=datetime.now()
        )
        
        await service_registry.register_agent(agent1)
        await service_registry.register_agent(agent2)
        
        # When: 특정 능력으로 검색하면
        nlp_agents = await service_registry.discover_agents("extract_ticker")
        data_agents = await service_registry.discover_agents("collect_news")
        
        # Then: 해당 능력을 가진 에이전트만 반환
        assert len(nlp_agents) == 1
        assert nlp_agents[0].agent_id == "nlp-agent"
        
        assert len(data_agents) == 1
        assert data_agents[0].agent_id == "data-agent"
        
    @pytest.mark.asyncio
    async def test_inactive_agents_filtered(self, service_registry):
        """비활성 에이전트 필터링 테스트"""
        # Given: 오래된 하트비트를 가진 에이전트
        old_heartbeat = datetime.now() - timedelta(seconds=100)
        inactive_agent = AgentInfo(
            agent_id="inactive-agent",
            name="Inactive Agent",
            description="비활성 에이전트",
            endpoint="http://localhost:9999",
            capabilities=[],
            status="active",
            last_heartbeat=old_heartbeat
        )
        
        active_agent = AgentInfo(
            agent_id="active-agent",
            name="Active Agent",
            description="활성 에이전트",
            endpoint="http://localhost:9998",
            capabilities=[],
            status="active",
            last_heartbeat=datetime.now()
        )
        
        await service_registry.register_agent(inactive_agent)
        await service_registry.register_agent(active_agent)
        
        # When: 에이전트를 발견하면
        discovered = await service_registry.discover_agents()
        
        # Then: 활성 에이전트만 반환
        assert len(discovered) == 1
        assert discovered[0].agent_id == "active-agent"
        
    @pytest.mark.asyncio
    async def test_capability_index_update(self, service_registry):
        """능력 인덱스 업데이트 테스트"""
        # Given: 여러 능력을 가진 에이전트
        agent = AgentInfo(
            agent_id="multi-cap-agent",
            name="Multi Capability Agent",
            description="다중 능력 에이전트",
            endpoint="http://localhost:9997",
            capabilities=[
                {"name": "capability_a", "version": "1.0"},
                {"name": "capability_b", "version": "1.0"}
            ],
            status="active"
        )
        
        # When: 에이전트를 등록하면
        await service_registry.register_agent(agent)
        
        # Then: 능력 인덱스가 업데이트되어야 함
        assert "capability_a" in service_registry.capabilities_index
        assert "capability_b" in service_registry.capabilities_index
        assert agent.agent_id in service_registry.capabilities_index["capability_a"]
        assert agent.agent_id in service_registry.capabilities_index["capability_b"]
        
        # When: 에이전트를 해제하면
        await service_registry.deregister_agent(agent.agent_id)
        
        # Then: 능력 인덱스에서도 제거되어야 함
        assert agent.agent_id not in service_registry.capabilities_index.get("capability_a", set())
        assert agent.agent_id not in service_registry.capabilities_index.get("capability_b", set())


import asyncio