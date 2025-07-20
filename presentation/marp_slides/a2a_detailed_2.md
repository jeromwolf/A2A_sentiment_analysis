---
marp: true
theme: default
paginate: true
---

# A2A 심화 이해 2: BaseAgent 구현

## 우리 프로젝트의 BaseAgent

### 실제 구현된 BaseAgent 클래스
```python
class BaseAgent:
    def __init__(self, name: str, port: int, 
                 capabilities: List[str] = None):
        self.name = name
        self.port = port
        self.capabilities = capabilities or []
        self.registry_url = "http://localhost:8001"
        self.agent_info = None
        
    async def send_message(self, recipient: str, action: str, 
                          payload: dict) -> dict:
        """다른 에이전트에게 메시지 전송 (예: news-agent → sentiment-agent)"""
        
        # 1. 레지스트리에서 수신자 정보 조회
        agent_info = await self._discover_agent(recipient)
        if not agent_info:
            logger.warning(f"⚠️ A2A 실패, HTTP로 재시도")
            # Fallback: 직접 HTTP 호출
            return await self._http_fallback(recipient, action, payload)
            
        # 2. A2A 메시지 전송
        message_id = str(uuid.uuid4())
        response = await self._send_a2a_message(
            agent_info['endpoint'],
            {
                "sender": self.name,
                "action": action,
                "payload": payload,
                "message_id": message_id
            }
        )
        return response
```

---