#!/usr/bin/env python3
"""NLU 에이전트 직접 테스트"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_nlu_direct():
    """NLU 에이전트 직접 호출 테스트"""
    
    # 레지스트리에서 NLU 에이전트 찾기
    async with httpx.AsyncClient() as client:
        # 1. 레지스트리에서 NLU 에이전트 조회
        print("🔍 레지스트리에서 NLU 에이전트 검색...")
        response = await client.get("http://localhost:8001/discover?capability=extract_ticker")
        agents = response.json()["agents"]
        
        if not agents:
            print("❌ NLU 에이전트를 찾을 수 없습니다")
            return
            
        nlu_agent = agents[0]
        print(f"✅ NLU 에이전트 발견:")
        print(f"   - ID: {nlu_agent['agent_id']}")
        print(f"   - Name: {nlu_agent['name']}")
        print(f"   - Endpoint: {nlu_agent['endpoint']}")
        
        # 2. NLU 에이전트에 메시지 전송
        print("\n📤 NLU 에이전트에 메시지 전송...")
        
        message = {
            "header": {
                "message_id": "test-direct-123",
                "sender_id": "test-orchestrator",
                "receiver_id": nlu_agent["agent_id"],
                "message_type": "request",
                "correlation_id": None,
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "metadata": {}
            },
            "body": {
                "action": "extract_ticker",
                "payload": {
                    "query": "애플 주가 어때?"
                }
            }
        }
        
        print(f"   - URL: {nlu_agent['endpoint']}/message")
        print(f"   - Message ID: {message['header']['message_id']}")
        
        try:
            response = await client.post(
                f"{nlu_agent['endpoint']}/message",
                json=message,
                timeout=10.0
            )
            
            print(f"   - Response status: {response.status_code}")
            print(f"   - Response body: {response.json()}")
            
            if response.status_code == 200:
                print("✅ 메시지 전송 성공!")
            else:
                print(f"❌ 메시지 전송 실패: {response.text}")
                
        except httpx.ConnectError as e:
            print(f"❌ 연결 실패: {e}")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nlu_direct())