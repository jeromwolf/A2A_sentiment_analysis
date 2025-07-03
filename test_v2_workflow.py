#!/usr/bin/env python3
"""V2 워크플로우 테스트 스크립트"""

import asyncio
import websockets
import json
import sys

async def test_workflow():
    uri = "ws://localhost:8100/ws/v2"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 쿼리 전송
            query = {"query": "애플 주가 어때?"}
            await websocket.send(json.dumps(query))
            print(f"📤 쿼리 전송: {query}")
            
            # 응답 수신
            print("\n📥 응답 수신 중...")
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(response)
                    print(f"\n📊 수신된 메시지:")
                    print(f"  타입: {data.get('type')}")
                    print(f"  페이로드: {json.dumps(data.get('payload', {}), indent=2, ensure_ascii=False)}")
                    
                    # 최종 리포트 수신 시 종료
                    if data.get('type') == 'report_generated':
                        print("\n✅ 최종 리포트 수신 완료!")
                        break
                        
                except asyncio.TimeoutError:
                    print("\n⏱️ 타임아웃 - 60초 동안 응답 없음")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 연결이 종료되었습니다")
                    break
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 V2 워크플로우 테스트 시작")
    asyncio.run(test_workflow())