"""
MCP 서버 직접 테스트
A2A 에이전트 없이 MCP 서버만 테스트
"""

import asyncio
import httpx
import json

async def test_mcp_servers():
    async with httpx.AsyncClient() as client:
        print("🧪 MCP 서버 직접 테스트\n")
        
        # 1. Yahoo Finance MCP 테스트
        print("1️⃣ Yahoo Finance MCP (포트 3001)")
        try:
            # Initialize
            response = await client.post(
                "http://localhost:3001",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {}
                }
            )
            print(f"   초기화: {response.status_code}")
            
            # Get stock quote
            response = await client.post(
                "http://localhost:3001",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "getStockQuote",
                        "arguments": {"symbol": "AAPL"}
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ AAPL 주가: {result}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")
        
        # 2. Alpha Vantage MCP 테스트
        print("\n2️⃣ Alpha Vantage MCP (포트 3002)")
        try:
            # Get RSI
            response = await client.post(
                "http://localhost:3002",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "RSI",
                        "arguments": {"symbol": "GOOGL"}
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ GOOGL RSI: {result}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")
        
        # 3. A2A 통합 테스트 (간단 버전)
        print("\n3️⃣ A2A + MCP 통합 시뮬레이션")
        print("   시나리오: 사용자가 'TSLA 분석해줘' 요청")
        print("   1. A2A 오케스트레이터가 요청 수신")
        print("   2. Yahoo MCP에서 실시간 주가 조회")
        print("   3. Alpha Vantage MCP에서 기술적 지표 조회")
        print("   4. 결과 통합하여 사용자에게 전달")
        
        # 실제 호출
        tasks = []
        
        # Yahoo 주가
        tasks.append(client.post(
            "http://localhost:3001",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "getStockQuote",
                    "arguments": {"symbol": "TSLA"}
                }
            }
        ))
        
        # Alpha Vantage RSI
        tasks.append(client.post(
            "http://localhost:3002",
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "RSI",
                    "arguments": {"symbol": "TSLA"}
                }
            }
        ))
        
        results = await asyncio.gather(*tasks)
        
        print("\n   📊 통합 분석 결과:")
        for i, resp in enumerate(results):
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data and "content" in data["result"]:
                    content = data["result"]["content"][0]["text"]
                    print(f"   - {'주가' if i == 0 else 'RSI'}: {content}")

if __name__ == "__main__":
    asyncio.run(test_mcp_servers())