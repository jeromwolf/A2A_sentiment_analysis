#!/usr/bin/env python3
"""V2 워크플로우 최종 테스트 스크립트"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

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
            start_time = datetime.now()
            report_received = False
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=90.0)
                    data = json.loads(response)
                    
                    msg_type = data.get('type')
                    payload = data.get('payload', {})
                    
                    # 주요 이벤트만 출력
                    if msg_type == 'log':
                        message = payload.get('message', '')
                        if any(keyword in message for keyword in ['완료', '점수', '리포트', 'report', '최종', '생성']):
                            print(f"📊 {message}")
                    elif msg_type == 'report_generated':
                        print("\n✅ 최종 리포트 수신!")
                        print("="*60)
                        print(payload.get('report', ''))
                        print("="*60)
                        report_received = True
                        break
                    elif msg_type == 'error':
                        print(f"❌ 오류: {payload}")
                        
                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).seconds
                    print(f"\n⏱️ 타임아웃 - {elapsed}초 경과")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 연결이 종료되었습니다")
                    break
            
            if report_received:
                print("\n✅ 워크플로우 성공적으로 완료!")
            else:
                print("\n⚠️ 워크플로우가 완료되지 않았습니다")
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 V2 워크플로우 최종 테스트 시작")
    asyncio.run(test_workflow())