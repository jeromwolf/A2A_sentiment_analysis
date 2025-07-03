import asyncio
import websockets
import json

async def test_v2_system():
    uri = "ws://localhost:8100/ws/v2"
    
    async with websockets.connect(uri) as websocket:
        # 쿼리 전송
        query = {"query": "애플 주가 어때?"}
        await websocket.send(json.dumps(query))
        print(f"전송: {query}")
        
        # 응답 수신
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                print(f"수신: {data}")
                
                # 리포트가 수신되면 종료
                if data.get("type") == "result" and "report" in data.get("payload", {}):
                    print("\n✅ 전체 파이프라인 성공!")
                    break
                    
            except asyncio.TimeoutError:
                print("⏱️ 타임아웃")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_v2_system())