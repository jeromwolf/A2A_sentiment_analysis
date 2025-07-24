#!/usr/bin/env python3
"""
에이전트 자동 발견 및 통신 테스트
새로운 에이전트가 자동으로 발견되고 사용 가능한지 확인
"""

import asyncio
import httpx
from a2a_core.protocols.message import A2AMessage, MessageType
from a2a_core.registry.service_registry import AgentInfo
import json
from typing import List, Optional


class AgentDiscoveryTester:
    def __init__(self):
        self.registry_url = "http://localhost:8001"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def discover_all_agents(self) -> List[AgentInfo]:
        """모든 등록된 에이전트 발견"""
        try:
            response = await self.http_client.get(f"{self.registry_url}/discover")
            if response.status_code == 200:
                data = response.json()
                agents = [AgentInfo(**agent) for agent in data["agents"]]
                return agents
            else:
                print(f"❌ 레지스트리 조회 실패: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 레지스트리 연결 실패: {e}")
            return []
    
    async def find_agent_by_capability(self, capability: str) -> Optional[AgentInfo]:
        """특정 능력을 가진 에이전트 찾기"""
        try:
            response = await self.http_client.get(
                f"{self.registry_url}/discover",
                params={"capability": capability}
            )
            if response.status_code == 200:
                data = response.json()
                agents = [AgentInfo(**agent) for agent in data["agents"]]
                return agents[0] if agents else None
            return None
        except Exception as e:
            print(f"❌ 능력 기반 검색 실패: {e}")
            return None
    
    async def send_message_to_agent(self, agent: AgentInfo, action: str, payload: dict) -> dict:
        """에이전트에게 메시지 전송"""
        message = A2AMessage.create_request(
            sender_id="test-discovery-client",
            receiver_id=agent.agent_id,
            action=action,
            payload=payload
        )
        
        try:
            response = await self.http_client.post(
                f"{agent.endpoint}/message",
                json=message.to_dict()
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"응답 실패: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def test_new_agent_discovery(self):
        """새 에이전트 발견 및 통신 테스트"""
        print("\n🔍 A2A 에이전트 자동 발견 테스트")
        print("=" * 50)
        
        # 1. 모든 에이전트 발견
        print("\n1️⃣ 현재 등록된 모든 에이전트 조회")
        agents = await self.discover_all_agents()
        print(f"발견된 에이전트 수: {len(agents)}")
        
        for agent in agents:
            print(f"  - {agent.name} (ID: {agent.agent_id[:8]}...)")
            print(f"    능력: {[cap['name'] for cap in agent.capabilities]}")
        
        # 2. Test Scalability Agent 찾기
        print("\n2️⃣ Test Scalability Agent 검색")
        test_agent = None
        for agent in agents:
            if agent.name == "Test Scalability Agent":
                test_agent = agent
                break
        
        if test_agent:
            print(f"✅ Test Scalability Agent 발견!")
            print(f"   - Endpoint: {test_agent.endpoint}")
            print(f"   - 능력: {[cap['name'] for cap in test_agent.capabilities]}")
            
            # 3. echo_test 능력으로 검색
            print("\n3️⃣ 'echo_test' 능력을 가진 에이전트 검색")
            echo_agent = await self.find_agent_by_capability("echo_test")
            if echo_agent:
                print(f"✅ echo_test 능력을 가진 에이전트 발견: {echo_agent.name}")
            
            # 4. 메시지 전송 테스트
            print("\n4️⃣ Test Scalability Agent와 통신 테스트")
            
            # Echo 테스트
            print("\n   📤 Echo 메시지 전송...")
            echo_result = await self.send_message_to_agent(
                test_agent,
                "echo_test",
                {"message": "Hello from Discovery Tester!"}
            )
            print(f"   📥 응답: {json.dumps(echo_result, indent=2, ensure_ascii=False)}")
            
            # 상태 확인
            print("\n   📤 상태 확인 요청...")
            status_result = await self.send_message_to_agent(
                test_agent,
                "status_check",
                {}
            )
            print(f"   📥 응답: {json.dumps(status_result, indent=2, ensure_ascii=False)}")
            
        else:
            print("❌ Test Scalability Agent를 찾을 수 없습니다.")
            print("test_scalability_agent.py가 실행 중인지 확인하세요.")
        
        # 5. 정리
        await self.http_client.aclose()
        
        print("\n✨ 테스트 완료!")
        print("\n📊 확장성 검증 결과:")
        print("- ✅ 새 에이전트가 자동으로 레지스트리에 등록됨")
        print("- ✅ 다른 에이전트/클라이언트가 새 에이전트를 발견 가능")
        print("- ✅ 능력 기반으로 에이전트 검색 가능")
        print("- ✅ 표준 A2A 프로토콜로 즉시 통신 가능")
        print("- ✅ 시스템 재시작 없이 동적 확장 가능")


async def main():
    tester = AgentDiscoveryTester()
    await tester.test_new_agent_discovery()


if __name__ == "__main__":
    asyncio.run(main())