#!/usr/bin/env python3
"""
NLU Agent V2 capability 등록 테스트
"""

import asyncio
import httpx
import json
import time

async def test_nlu_capability():
    """NLU Agent V2의 capability 등록을 테스트"""
    
    async with httpx.AsyncClient() as client:
        print("🔍 NLU Agent V2 capability 등록 테스트 시작\n")
        
        # 1. 레지스트리 상태 확인
        print("1️⃣ 레지스트리 상태 확인...")
        try:
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                print(f"✅ 레지스트리 정상 작동 중: {response.json()}")
            else:
                print(f"❌ 레지스트리 응답 오류: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ 레지스트리 연결 실패: {e}")
            print("💡 레지스트리를 먼저 시작해주세요: python -m a2a_core.registry.service_registry")
            return
            
        # 2. NLU Agent V2가 실행 중인지 확인
        print("\n2️⃣ NLU Agent V2 상태 확인...")
        try:
            response = await client.get("http://localhost:8108/health")
            if response.status_code == 200:
                print(f"✅ NLU Agent V2 정상 작동 중: {response.json()}")
            else:
                print(f"❌ NLU Agent V2 응답 오류: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ NLU Agent V2 연결 실패: {e}")
            print("💡 NLU Agent V2를 시작해주세요: python -m agents.nlu_agent_v2")
            return
            
        # 3. capability 검색 (extract_ticker)
        print("\n3️⃣ extract_ticker capability로 에이전트 검색...")
        await asyncio.sleep(2)  # 등록 완료 대기
        
        response = await client.get(
            "http://localhost:8001/discover",
            params={"capability": "extract_ticker"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 검색 결과: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data["count"] > 0:
                print(f"\n✅ extract_ticker capability를 가진 에이전트 {data['count']}개 발견!")
                for agent in data["agents"]:
                    print(f"\n   📌 에이전트: {agent['name']}")
                    print(f"   🆔 ID: {agent['agent_id']}")
                    print(f"   🔧 Capabilities:")
                    for cap in agent['capabilities']:
                        print(f"      - {cap.get('name', 'Unknown')}: {cap.get('description', 'No description')}")
            else:
                print("\n❌ extract_ticker capability를 가진 에이전트를 찾을 수 없습니다.")
                print("💡 NLU Agent V2가 정상적으로 시작되었는지 확인하세요.")
        else:
            print(f"❌ 에이전트 검색 실패: {response.status_code}")
            
        # 4. NLU Agent V2의 capabilities 직접 확인
        print("\n4️⃣ NLU Agent V2의 capabilities 직접 확인...")
        response = await client.get("http://localhost:8108/capabilities")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 NLU Agent V2 capabilities: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ capabilities 조회 실패: {response.status_code}")
            
        # 5. 티커 추출 기능 테스트
        print("\n5️⃣ 티커 추출 기능 테스트...")
        test_message = {
            "header": {
                "message_id": "test-001",
                "message_type": "request",
                "sender_id": "test-client",
                "receiver_id": "nlu-agent-v2",
                "timestamp": time.time()
            },
            "body": {
                "action": "extract_ticker",
                "payload": {
                    "query": "애플 주가가 어떻게 되나요?"
                }
            },
            "metadata": {
                "priority": "normal",
                "require_ack": False
            }
        }
        
        response = await client.post(
            "http://localhost:8108/message",
            json=test_message
        )
        
        if response.status_code == 200:
            print(f"✅ 메시지 전송 성공: {response.json()}")
        else:
            print(f"❌ 메시지 전송 실패: {response.status_code}")
            
        print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(test_nlu_capability())