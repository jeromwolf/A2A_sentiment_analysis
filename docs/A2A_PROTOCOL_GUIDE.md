# A2A 프로토콜 구현 가이드

## 🎯 개요

이 문서는 A2A (Agent-to-Agent) 프로토콜을 구현한 새로운 시스템 아키텍처를 설명합니다.

## 🏗️ 핵심 구성요소

### 1. 서비스 레지스트리 (`a2a_core/registry/service_registry.py`)
- **포트**: 8001
- **역할**: 모든 에이전트의 동적 등록/발견/상태 관리
- **주요 기능**:
  - 에이전트 등록/해제
  - 능력 기반 에이전트 검색
  - 하트비트를 통한 상태 모니터링
  - 자동 헬스체크

### 2. 표준 메시지 형식 (`a2a_core/protocols/message.py`)
```python
{
    "header": {
        "message_id": "uuid",
        "timestamp": "2024-01-01T12:00:00Z",
        "sender_id": "agent-uuid",
        "receiver_id": "agent-uuid",
        "message_type": "request|response|event|error",
        "protocol_version": "1.0",
        "correlation_id": "original-message-id"
    },
    "body": {
        "action": "specific_action",
        "payload": {...}
    },
    "metadata": {
        "priority": "normal|high|urgent",
        "ttl": 30,
        "require_ack": false
    }
}
```

### 3. 베이스 에이전트 클래스 (`a2a_core/base/base_agent.py`)
모든 A2A 에이전트가 상속받는 기본 클래스:
- 자동 서비스 레지스트리 등록
- 표준 메시지 송수신
- 하트비트 관리
- 능력 선언 및 광고
- 이벤트 브로드캐스팅

## 🚀 새로운 에이전트 생성 방법

```python
from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="My Agent",
            description="에이전트 설명",
            port=8200,
            registry_url="http://localhost:8001"
        )
    
    async def on_start(self):
        # 능력 등록
        await self.register_capability({
            "name": "my_capability",
            "version": "1.0",
            "description": "능력 설명"
        })
    
    async def handle_message(self, message: A2AMessage):
        # 메시지 처리 로직
        if message.body.get("action") == "my_action":
            result = await self.process_action(message.body["payload"])
            await self.reply_to_message(message, result)
    
    async def on_stop(self):
        # 정리 작업
        pass
```

## 📡 에이전트 간 통신

### 1. 직접 메시지 전송
```python
# 다른 에이전트에게 메시지 전송
await self.send_message(
    receiver_id="target-agent-id",
    action="analyze_data",
    payload={"data": "..."},
    priority=Priority.HIGH
)
```

### 2. 이벤트 브로드캐스팅
```python
# 모든 에이전트에게 이벤트 전송
await self.broadcast_event(
    event_type="data_ready",
    event_data={"source": "news", "count": 10}
)
```

### 3. 동적 에이전트 발견
```python
# 특정 능력을 가진 에이전트 찾기
agents = await self.discover_agents("sentiment_analysis")
for agent in agents:
    await self.send_message(agent.agent_id, ...)
```

## 🔄 마이그레이션 계획

### Phase 1: 기반 구조 (완료)
- ✅ 서비스 레지스트리 구현
- ✅ 표준 메시지 형식 정의
- ✅ 베이스 에이전트 클래스 구현
- ✅ NLU 에이전트 V2 구현

### Phase 2: 데이터 수집 에이전트 (진행 중)
- [ ] News Agent V2
- [ ] Twitter Agent V2
- [ ] SEC Agent V2

### Phase 3: 분석 에이전트
- [ ] Sentiment Analysis Agent V2
- [ ] Score Calculation Agent V2
- [ ] Report Generation Agent V2

### Phase 4: 고급 기능
- [ ] 메시지 큐 통합 (RabbitMQ/Kafka)
- [ ] 분산 트레이싱
- [ ] 에이전트 오토스케일링

## 🛠️ 개발 및 테스트

### 시스템 실행
```bash
# A2A 시스템 시작
./start_a2a.sh

# 서비스 레지스트리 확인
curl http://localhost:8001/health

# 등록된 에이전트 조회
curl http://localhost:8001/discover

# 특정 능력을 가진 에이전트 찾기
curl "http://localhost:8001/discover?capability=extract_ticker"
```

### 에이전트 테스트
```python
# 테스트 메시지 전송
import httpx
import asyncio

async def test_agent():
    async with httpx.AsyncClient() as client:
        # NLU 에이전트 테스트
        response = await client.post(
            "http://localhost:8108/message",
            json={
                "header": {
                    "message_id": "test-123",
                    "sender_id": "test-sender",
                    "receiver_id": "nlu-agent-id",
                    "message_type": "request",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "protocol_version": "1.0"
                },
                "body": {
                    "action": "extract_ticker",
                    "payload": {"query": "애플 주가 어때?"}
                },
                "metadata": {
                    "priority": "normal"
                }
            }
        )
        print(response.json())

asyncio.run(test_agent())
```

## 📊 모니터링

### 서비스 레지스트리 대시보드
- http://localhost:8001/docs - Swagger UI
- 실시간 에이전트 상태 확인
- 능력별 에이전트 검색

### 에이전트 상태 확인
```bash
# 개별 에이전트 헬스체크
curl http://localhost:8108/health

# 에이전트 능력 조회
curl http://localhost:8108/capabilities
```

## 🔐 보안 고려사항

1. **인증/인가**: 현재는 구현되지 않음. 프로덕션에서는 JWT 등 추가 필요
2. **메시지 암호화**: TLS 통신 권장
3. **Rate Limiting**: 에이전트별 요청 제한 필요
4. **감사 로깅**: 모든 메시지 교환 기록

## 📈 성능 최적화

1. **메시지 캐싱**: 자주 사용되는 응답 캐시
2. **연결 풀링**: HTTP 클라이언트 연결 재사용
3. **비동기 처리**: 모든 I/O 작업 비동기화
4. **배치 처리**: 여러 메시지 일괄 전송

## 🚧 알려진 제한사항

1. **단일 레지스트리**: 현재는 중앙집중식. 분산 레지스트리 필요
2. **메시지 영속성**: 메모리 기반. 메시지 큐 통합 필요
3. **트랜잭션**: 분산 트랜잭션 미지원
4. **버전 관리**: 프로토콜 버전 협상 기능 미구현

## 🤝 기여 방법

1. 새로운 에이전트는 반드시 `BaseAgent` 상속
2. 표준 메시지 형식 준수
3. 능력 명세 작성 필수
4. 단위 테스트 포함

---

**질문이나 제안사항은 Issues를 통해 공유해주세요!**