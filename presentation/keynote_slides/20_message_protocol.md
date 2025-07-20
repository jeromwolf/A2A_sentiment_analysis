# 슬라이드 20: 메시지 프로토콜

## A2A 메시지 구조

### 메시지 형식
```python
class A2AMessage:
    header: MessageHeader
    body: Dict[str, Any]

class MessageHeader:
    message_id: str      # 고유 ID
    message_type: str    # REQUEST/RESPONSE/EVENT
    sender_id: str       # 송신 에이전트
    recipient_id: str    # 수신 에이전트
    timestamp: datetime  # 타임스탬프
    correlation_id: str  # 요청-응답 매칭
```

### 메시지 타입
- **REQUEST**: 작업 요청
- **RESPONSE**: 요청에 대한 응답
- **EVENT**: 브로드캐스트 이벤트

### 특징
- UUID 기반 추적
- 비동기 응답 지원
- 이벤트 구독 모델