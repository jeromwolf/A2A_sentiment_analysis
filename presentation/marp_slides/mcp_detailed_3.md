---
marp: true
theme: default
paginate: true
---

# MCP 심화 이해 3: 서버 구현

## 실제 투자 분석 MCP 서버

### 우리 프로젝트의 MCP 서버 구현
```python
class InvestmentAnalysisServer:
    def __init__(self):
        self.name = "투자 분석 MCP 서버"
        
    @server.list_tools()
    async def list_tools(self) -> List[Tool]:
        """사용 가능한 금융 도구 목록"""
        return [
            Tool(
                name="get_bloomberg_data",
                description="Bloomberg Terminal 데이터 조회",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "data_type": {"type": "string",
                            "enum": ["price", "fundamentals", "news"]}
                    }
                }
            ),
            Tool(
                name="analyze_market_sentiment",
                description="시장 심리 분석",
                inputSchema={"ticker": {"type": "string"}}
            )
        ]
    
    @server.call_tool()
    async def call_tool(self, name: str, arguments: dict):
        if name == "get_bloomberg_data":
            # 실제 Bloomberg API 호출
            return await self.fetch_bloomberg_data(
                arguments["ticker"], 
                arguments["data_type"]
            )
```

---