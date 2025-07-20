---
marp: true
theme: default
paginate: true
---

# A2A 심화 이해 1: 프로토콜 설계

## 우리 프로젝트의 A2A 프로토콜

### 실제 사용중인 에이전트 정보 구조
```python
# AgentInfo: 레지스트리에 등록되는 에이전트 정보
class AgentInfo:
    def __init__(self, name: str, endpoint: str, 
                 capabilities: List[str]):
        self.id = str(uuid.uuid4())  # 고유 ID
        self.name = name  # 예: "news-agent", "sentiment-agent"
        self.endpoint = endpoint  # 예: "http://localhost:8307"
        self.capabilities = capabilities  # 예: ["news_collection"]
        self.status = "healthy"
        self.last_heartbeat = datetime.utcnow()
        self.metadata = {
            "version": "2.0",
            "started_at": datetime.utcnow().isoformat()
        }

# A2A 메시지 구조 (실제 사용)
{
    "sender": "main-orchestrator",
    "action": "collect_data",  # 또는 "analyze", "calculate_score" 등
    "payload": {
        "ticker": "AAPL",
        "data": {...}
    },
    "message_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---