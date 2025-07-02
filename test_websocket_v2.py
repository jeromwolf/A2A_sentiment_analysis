#!/usr/bin/env python3
"""WebSocket V2 테스트"""

import asyncio
import websockets
import json

async def test_analysis():
    """V2 WebSocket 분석 테스트"""
    uri = "ws://localhost:8100/ws/v2"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ WebSocket 연결 성공: {uri}")
            
            # 쿼리 전송
            query = {"query": "애플 주가 어때?"}
            await websocket.send(json.dumps(query))
            print(f"📤 쿼리 전송: {query}")
            
            # 응답 수신 (최대 60초 대기)
            timeout = 60
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    # 1초 타임아웃으로 메시지 대기
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    print(f"\n📥 메시지 수신:")
                    print(f"   Type: {data.get('type')}")
                    print(f"   Payload: {data.get('payload')}")
                    
                    # 결과 메시지 확인
                    if data.get('type') == 'result':
                        print("\n🎉 분석 완료!")
                        print(f"   최종 점수: {data['payload'].get('final_score')}")
                        print(f"   라벨: {data['payload'].get('final_label')}")
                        break
                        
                    # 오류 메시지 확인
                    elif data.get('type') == 'error':
                        print(f"\n❌ 오류 발생: {data['payload'].get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    # 타임아웃 체크
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"\n⏰ {timeout}초 타임아웃")
                        break
                    continue
                    
    except Exception as e:
        print(f"❌ 연결 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_analysis())