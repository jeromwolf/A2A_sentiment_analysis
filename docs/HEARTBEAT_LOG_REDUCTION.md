# 하트비트 로그 감소 가이드

## 문제점
- 하트비트 로그가 30초마다 출력되어 중요한 로그를 보기 어려움
- Registry Server와 httpx 라이브러리에서 너무 많은 하트비트 관련 로그 출력

## 해결 방법

### 1. 하트비트 주기 변경
- `config/settings.yaml`에서 하트비트 주기를 30초에서 10분(600초)로 변경
```yaml
registry:
  heartbeat_interval: 600  # 10분으로 변경 (600초)
```

### 2. Base Agent 수정
- `a2a_core/base/base_agent.py`의 `_heartbeat_loop()` 메소드 수정
- 설정 파일에서 하트비트 주기를 읽도록 변경
- 하트비트 로그를 10회에 1번만 출력 (100분에 1번)

### 3. Registry Server 로그 비활성화
- `a2a_core/registry/registry_server.py`의 `update_heartbeat()` 메소드에서 하트비트 로그 주석 처리

### 4. httpx 로그 레벨 조정
각 에이전트에서 httpx 로그 레벨을 WARNING으로 설정:
```python
# httpx 로그 레벨을 WARNING으로 설정하여 하트비트 로그 숨기기
logging.getLogger("httpx").setLevel(logging.WARNING)
```

적용된 에이전트:
- news_agent_v2_pure.py
- quantitative_agent_v2.py
- dart_agent_v2.py
- 기타 에이전트들

## 효과
- 하트비트 관련 로그가 대폭 감소
- 중요한 비즈니스 로직 로그에 집중 가능
- 시스템 모니터링은 여전히 가능 (하트비트는 백그라운드에서 계속 동작)

## 추가 고려사항
로그가 여전히 많다면:
1. 특정 에이전트의 로그 레벨을 조정
2. 로그 파일 로테이션 설정
3. 로그 필터링 규칙 추가