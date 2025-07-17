"""
MCP (Model Context Protocol) 표준 클라이언트 구현
JSON-RPC 2.0 기반 통신
"""

import json
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid

@dataclass
class MCPResource:
    """MCP 리소스 정의"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"

@dataclass
class MCPTool:
    """MCP 도구 정의"""
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPClient:
    """MCP 표준 호환 클라이언트"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = httpx.AsyncClient()
        self.request_id = 0
        
    async def initialize(self) -> Dict[str, Any]:
        """MCP 서버 초기화 및 능력 협상"""
        response = await self._json_rpc_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": True}
            },
            "clientInfo": {
                "name": "a2a-sentiment-analyzer",
                "version": "1.0.0"
            }
        })
        return response
    
    async def list_resources(self) -> List[MCPResource]:
        """사용 가능한 리소스 목록 조회"""
        response = await self._json_rpc_request("resources/list", {})
        resources = response.get("resources", [])
        return [MCPResource(**r) for r in resources]
    
    async def list_tools(self) -> List[MCPTool]:
        """사용 가능한 도구 목록 조회"""
        response = await self._json_rpc_request("tools/list", {})
        tools = response.get("tools", [])
        return [MCPTool(**t) for t in tools]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """리소스 읽기"""
        response = await self._json_rpc_request("resources/read", {
            "uri": uri
        })
        return response.get("contents", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구 실행"""
        response = await self._json_rpc_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return response.get("content", [])
    
    async def _json_rpc_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 2.0 요청 전송"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        response = await self.client.post(
            self.server_url,
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"MCP 서버 오류: {response.status_code}")
        
        result = response.json()
        
        if "error" in result:
            raise Exception(f"MCP 오류: {result['error']}")
        
        return result.get("result", {})
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


# MCP 데이터 수집을 위한 래퍼
class MCPDataCollector:
    """MCP를 통한 프리미엄 데이터 수집"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:3000"):
        self.client = MCPClient(mcp_server_url)
        self.initialized = False
    
    async def initialize(self):
        """MCP 클라이언트 초기화"""
        if not self.initialized:
            await self.client.initialize()
            self.initialized = True
    
    async def get_analyst_reports(self, ticker: str) -> List[Dict[str, Any]]:
        """애널리스트 리포트 조회"""
        await self.initialize()
        
        # MCP 도구 호출
        result = await self.client.call_tool("getAnalystReports", {
            "ticker": ticker,
            "limit": 5
        })
        
        return result.get("reports", [])
    
    async def get_insider_trading(self, ticker: str) -> List[Dict[str, Any]]:
        """내부자 거래 정보 조회"""
        await self.initialize()
        
        result = await self.client.call_tool("getInsiderTrading", {
            "ticker": ticker,
            "days": 90
        })
        
        return result.get("transactions", [])
    
    async def get_market_sentiment(self, ticker: str) -> Dict[str, Any]:
        """시장 심리 지표 조회"""
        await self.initialize()
        
        result = await self.client.call_tool("getMarketSentiment", {
            "ticker": ticker
        })
        
        return result
    
    async def get_all_premium_data(self, ticker: str) -> Dict[str, Any]:
        """모든 프리미엄 데이터 통합 조회"""
        await self.initialize()
        
        # 병렬로 모든 데이터 수집
        tasks = [
            self.get_analyst_reports(ticker),
            self.get_insider_trading(ticker),
            self.get_market_sentiment(ticker)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "analyst_reports": results[0] if not isinstance(results[0], Exception) else [],
            "insider_trading": results[1] if not isinstance(results[1], Exception) else [],
            "market_sentiment": results[2] if not isinstance(results[2], Exception) else {}
        }


# 사용 예시
async def example_usage():
    """MCP 클라이언트 사용 예시"""
    collector = MCPDataCollector()
    
    try:
        # 애플 주식의 프리미엄 데이터 수집
        premium_data = await collector.get_all_premium_data("AAPL")
        
        print("📊 애널리스트 리포트:", len(premium_data["analyst_reports"]))
        print("💼 내부자 거래:", len(premium_data["insider_trading"]))
        print("🎯 시장 심리:", premium_data["market_sentiment"])
        
    finally:
        await collector.client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())