# 슬라이드 19: BaseAgent 클래스

## 모든 에이전트의 기반

### 핵심 기능
```python
class BaseAgent:
    # 1. 자동 등록
    async def start(self):
        await self._register_with_registry()
        await self._start_heartbeat()
    
    # 2. 메시지 전송
    async def send_message(self, 
                          recipient: str,
                          action: str,
                          payload: dict):
        # A2A 프로토콜로 전송
    
    # 3. 이벤트 브로드캐스트
    async def broadcast_event(self,
                             event_type: str,
                             event_data: dict):
        # 관심있는 에이전트에게 전파
```

### 상속만으로 즉시 A2A 에이전트화
- 레지스트리 등록 자동화
- 헬스체크 자동화
- 메시지 라우팅 자동화