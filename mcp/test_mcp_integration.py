"""
MCP Integration Test Script
A2A 시스템과 외부 MCP 서버 통합 테스트
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

class MCPIntegrationTester:
    def __init__(self):
        self.base_urls = {
            "orchestrator": "http://localhost:8100",
            "mcp_yahoo": "http://localhost:8213",
            "mcp_alpha": "http://localhost:8214",
            "registry": "http://localhost:8001"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_registry_status(self):
        """레지스트리 상태 확인"""
        print("\n🔍 1. 레지스트리 상태 확인")
        try:
            response = await self.client.get(f"{self.base_urls['registry']}/agents")
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ 등록된 에이전트 수: {len(agents)}")
                for agent in agents:
                    print(f"  - {agent['name']} (포트: {agent['port']})")
            else:
                print(f"❌ 레지스트리 오류: {response.status_code}")
        except Exception as e:
            print(f"❌ 레지스트리 연결 실패: {e}")
    
    async def test_mcp_yahoo_finance(self):
        """Yahoo Finance MCP 에이전트 테스트"""
        print("\n🔍 2. Yahoo Finance MCP 에이전트 테스트")
        
        test_cases = [
            {
                "name": "기본 분석",
                "endpoint": "/analyze",
                "data": {"ticker": "AAPL"}
            },
            {
                "name": "실시간 주가",
                "endpoint": "/real_time_quote",
                "data": {"ticker": "GOOGL"}
            }
        ]
        
        for test in test_cases:
            print(f"\n  📌 {test['name']} 테스트:")
            try:
                response = await self.client.post(
                    f"{self.base_urls['mcp_yahoo']}{test['endpoint']}",
                    json=test['data']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ 성공!")
                    print(f"  - 티커: {result.get('ticker')}")
                    print(f"  - 타임스탬프: {result.get('timestamp')}")
                    
                    if 'quote' in result:
                        print(f"  - 주가 데이터: {bool(result['quote'])}")
                    if 'company_info' in result:
                        print(f"  - 기업 정보: {bool(result['company_info'])}")
                    if 'technical_indicators' in result:
                        print(f"  - 기술적 지표: {bool(result['technical_indicators'])}")
                else:
                    print(f"  ❌ 오류: {response.status_code}")
                    print(f"  - 응답: {response.text}")
            
            except Exception as e:
                print(f"  ❌ 연결 실패: {e}")
    
    async def test_mcp_alpha_vantage(self):
        """Alpha Vantage MCP 에이전트 테스트"""
        print("\n🔍 3. Alpha Vantage MCP 에이전트 테스트")
        
        test_cases = [
            {
                "name": "종합 분석",
                "endpoint": "/analyze",
                "data": {"ticker": "MSFT"}
            },
            {
                "name": "고급 기술적 분석",
                "endpoint": "/advanced_analysis",
                "data": {
                    "ticker": "TSLA",
                    "indicators": ["RSI", "MACD", "BBANDS"]
                }
            }
        ]
        
        for test in test_cases:
            print(f"\n  📌 {test['name']} 테스트:")
            try:
                response = await self.client.post(
                    f"{self.base_urls['mcp_alpha']}{test['endpoint']}",
                    json=test['data']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ 성공!")
                    print(f"  - 티커: {result.get('ticker')}")
                    
                    if 'real_time_quote' in result:
                        print(f"  - 실시간 주가: {bool(result['real_time_quote'])}")
                    if 'indicators' in result:
                        print(f"  - 지표: {list(result['indicators'].keys())}")
                    if 'signal' in result:
                        print(f"  - 트레이딩 신호: {result['signal']}")
                else:
                    print(f"  ❌ 오류: {response.status_code}")
                    print(f"  - 응답: {response.text}")
            
            except Exception as e:
                print(f"  ❌ 연결 실패: {e}")
    
    async def test_orchestrator_integration(self):
        """오케스트레이터 통합 테스트"""
        print("\n🔍 4. 오케스트레이터 통합 테스트")
        
        # WebSocket 연결은 별도 구현 필요
        print("  ℹ️  WebSocket 기반 오케스트레이터는 브라우저에서 테스트하세요")
        print(f"  - URL: {self.base_urls['orchestrator']}")
    
    async def test_mcp_server_direct(self):
        """MCP 서버 직접 호출 테스트"""
        print("\n🔍 5. MCP 서버 직접 호출 테스트 (선택사항)")
        
        mcp_servers = [
            {
                "name": "Yahoo Finance MCP",
                "url": "http://localhost:3001",
                "method": "QUOTE_ENDPOINT",
                "params": {"symbol": "AAPL"}
            },
            {
                "name": "Alpha Vantage MCP",
                "url": "http://localhost:3002",
                "method": "QUOTE_ENDPOINT",
                "params": {"symbol": "AAPL"}
            }
        ]
        
        for server in mcp_servers:
            print(f"\n  📌 {server['name']} 직접 호출:")
            try:
                # JSON-RPC 2.0 요청
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": server["method"],
                        "arguments": server["params"]
                    }
                }
                
                response = await self.client.post(
                    server["url"],
                    json=request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        print(f"  ✅ 성공!")
                        print(f"  - 응답: {json.dumps(result['result'], indent=2)[:200]}...")
                    else:
                        print(f"  ⚠️  결과 없음: {result}")
                else:
                    print(f"  ❌ 오류: {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ MCP 서버 연결 실패: {e}")
                print(f"  ℹ️  MCP 서버가 실행 중인지 확인하세요")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 60)
        print("🚀 MCP Integration Test Suite")
        print("=" * 60)
        
        await self.test_registry_status()
        await self.test_mcp_yahoo_finance()
        await self.test_mcp_alpha_vantage()
        await self.test_orchestrator_integration()
        await self.test_mcp_server_direct()
        
        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


async def main():
    tester = MCPIntegrationTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())