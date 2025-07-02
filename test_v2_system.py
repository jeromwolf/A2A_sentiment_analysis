#!/usr/bin/env python3
"""
V2 시스템 전체 테스트 스크립트
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_v2_orchestrator():
    """V2 오케스트레이터를 통한 전체 시스템 테스트"""
    
    print("🚀 A2A V2 시스템 통합 테스트 시작\n")
    
    # 1. Registry 상태 확인
    print("1️⃣ Registry 상태 확인...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8001/discover")
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                print(f"✅ Registry 작동 중 - 등록된 에이전트: {len(agents)}개")
                for agent in agents[:3]:  # 처음 3개만 표시
                    print(f"   - {agent.get('name')} (port {agent.get('port')})")
                if len(agents) > 3:
                    print(f"   ... 외 {len(agents)-3}개")
            else:
                print(f"❌ Registry 응답 오류: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Registry 연결 실패: {e}")
        print("   Registry를 먼저 시작하세요: python -m a2a_core.registry.registry_server")
        return
    
    print()
    
    # 2. Main Orchestrator V2 테스트
    print("2️⃣ Main Orchestrator V2 테스트...")
    test_query = "애플 주가 분석해줘"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # WebSocket 대신 HTTP POST로 테스트
            print(f"   쿼리: '{test_query}'")
            
            response = await client.post(
                "http://localhost:8100/analyze",
                json={"query": test_query}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 분석 완료!")
                print(f"   - 처리 시간: {result.get('processing_time', 'N/A')}")
                print(f"   - 수집된 데이터:")
                
                # 데이터 소스별 결과
                for source in ['news', 'twitter', 'sec']:
                    data = result.get('data', {}).get(source, [])
                    print(f"     - {source}: {len(data)}개")
                
                # 최종 점수
                if 'final_score' in result:
                    print(f"   - 최종 감성 점수: {result['final_score']:.2f}")
                
                # 분석 보고서 일부
                if 'report' in result:
                    print(f"   - 보고서 생성: ✅")
                    print(f"     {result['report'][:200]}...")
                    
            else:
                print(f"❌ 오케스트레이터 오류: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
                
    except httpx.ConnectError:
        print("❌ Main Orchestrator V2에 연결할 수 없습니다")
        print("   시작하세요: uvicorn main_orchestrator_v2:app --port 8100 --reload")
    except Exception as e:
        print(f"❌ 테스트 실패: {type(e).__name__}: {e}")
    
    print("\n" + "="*50)
    
    # 3. 개별 V2 어댑터 직접 테스트
    print("\n3️⃣ V2 데이터 수집 어댑터 직접 테스트...")
    
    adapters = [
        ("News V2", 8207, "news_data_collection"),
        ("Twitter V2", 8209, "twitter_data_collection"),
        ("SEC V2", 8210, "sec_data_collection")
    ]
    
    for name, port, action in adapters:
        print(f"\n{name} 어댑터 테스트...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # A2A 메시지 형식으로 요청
                message = {
                    "header": {
                        "message_id": f"test-{port}-{datetime.now().timestamp()}",
                        "message_type": "request",
                        "sender_id": "test-client",
                        "timestamp": datetime.now().isoformat()
                    },
                    "body": {
                        "action": action,
                        "payload": {
                            "ticker": "AAPL"
                        }
                    }
                }
                
                response = await client.post(
                    f"http://localhost:{port}/agent/message",
                    json=message
                )
                
                if response.status_code == 200:
                    result = response.json()
                    body = result.get("body", {})
                    if body.get("success"):
                        data_count = body.get("result", {}).get("count", 0)
                        print(f"   ✅ 성공 - 수집된 데이터: {data_count}개")
                    else:
                        print(f"   ❌ 실패 - {body.get('result', {}).get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ HTTP 오류: {response.status_code}")
                    
        except httpx.ConnectError:
            print(f"   ❌ 연결 실패 - 포트 {port}에서 실행 중인지 확인하세요")
        except Exception as e:
            print(f"   ❌ 오류: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_v2_orchestrator())