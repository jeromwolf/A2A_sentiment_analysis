---
marp: true
theme: default
paginate: true
---

# MCP 심화 이해 5: 고급 패턴

## 우리 프로젝트의 MCP 활용 패턴

### 1. 대량 데이터 처리 (Bloomberg/Refinitiv)
```python
@server.call_tool()
async def call_tool(self, name: str, arguments: dict):
    if name == "get_market_data_batch":
        # 여러 티커 동시 조회
        tickers = arguments["tickers"]  # ["AAPL", "GOOGL", "MSFT"]
        
        tasks = []
        for ticker in tickers:
            task = self._fetch_premium_data(ticker)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        return {"data": results, "source": "Bloomberg Terminal"}
```

### 2. 실시간 스트리밍 데이터
```python
@server.tool(streaming=True)
async def stream_market_updates(ticker: str):
    """실시간 시장 데이터 스트리밍"""
    async with RefinitivWebSocket() as ws:
        await ws.subscribe(ticker)
        async for update in ws:
            yield {
                "ticker": ticker,
                "price": update.price,
                "volume": update.volume,
                "timestamp": update.timestamp
            }
```

### 3. MCP + A2A 하이브리드 통합
```python
# MCP Data Agent가 A2A와 MCP를 연결
class MCPDataAgent(BaseAgent):
    async def handle_collect_data(self, message):
        ticker = message['payload']['ticker']
        
        # MCP 서버에서 프리미엄 데이터 요청
        premium_data = await self.mcp_client.call_tool(
            "get_institutional_analysis",
            {"ticker": ticker, "include_proprietary": True}
        )
        
        # A2A로 결과 전달
        return {"premium_data": premium_data}
```

---