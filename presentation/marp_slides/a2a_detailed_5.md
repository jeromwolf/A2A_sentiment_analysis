---
marp: true
theme: default
paginate: true
---

# A2A 심화 이해 5: 실전 구현 가이드

## 우리 프로젝트의 핵심 기능 구현

### 1. A2A 실패 시 Fallback 처리
```python
# News Agent의 실제 구현
async def send_message(self, recipient: str, action: str, payload: dict):
    try:
        # A2A 통신 시도
        agent_info = await self._discover_agent(recipient)
        if agent_info:
            return await self._send_a2a_message(
                agent_info['endpoint'], 
                {"action": action, "payload": payload}
            )
    except Exception as e:
        logger.warning(f"⚠️ A2A 실패, HTTP로 재시도: {e}")
    
    # Fallback: 직접 HTTP 호출
    return await self._http_fallback(recipient, action, payload)
```

### 2. MCP와 A2A 통합 (MCP Data Agent)
```python
class MCPDataAgent(BaseAgent):
    def __init__(self):
        super().__init__("MCP Data Agent", port=8214)
        self.mcp_client = MCPClient()
        
    async def handle_message(self, message: dict):
        # A2A 메시지 수신
        if message['action'] == 'collect_data':
            ticker = message['payload']['ticker']
            
            # MCP 서버로 데이터 요청
            bloomberg_data = await self.mcp_client.call_tool(
                "get_bloomberg_data",
                {"ticker": ticker, "data_type": "fundamentals"}
            )
            
            # A2A로 결과 전달
            return {"status": "success", "data": bloomberg_data}
```

### 3. 실제 사용 현황
- **11개 에이전트**: 각각 특화된 역할 수행
- **평균 응답 시간**: 7초 (병렬 처리로 57% 단축)
- **동시 처리**: 최대 50개 요청

---