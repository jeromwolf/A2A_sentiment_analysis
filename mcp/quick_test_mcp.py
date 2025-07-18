"""
빠른 MCP 통합 테스트
개별 컴포넌트를 간단히 테스트
"""

import asyncio
import httpx

async def quick_test():
    async with httpx.AsyncClient() as client:
        print("🚀 Quick MCP Integration Test\n")
        
        # 1. 레지스트리 확인
        try:
            print("1️⃣ 레지스트리 확인...")
            resp = await client.get("http://localhost:8001/agents")
            print(f"   등록된 에이전트: {len(resp.json())}개")
        except:
            print("   ❌ 레지스트리 연결 실패")
        
        # 2. Yahoo Finance MCP 테스트
        try:
            print("\n2️⃣ Yahoo Finance MCP 테스트...")
            resp = await client.post(
                "http://localhost:8213/analyze",
                json={"ticker": "AAPL"}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ 성공: {data['ticker']} 분석 완료")
            else:
                print(f"   ❌ 실패: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 연결 실패: {e}")
        
        # 3. Alpha Vantage MCP 테스트
        try:
            print("\n3️⃣ Alpha Vantage MCP 테스트...")
            resp = await client.post(
                "http://localhost:8214/real_time_quote",
                json={"ticker": "GOOGL"}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ 성공: {data['ticker']} 실시간 주가 조회")
            else:
                print(f"   ❌ 실패: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 연결 실패: {e}")
        
        print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(quick_test())