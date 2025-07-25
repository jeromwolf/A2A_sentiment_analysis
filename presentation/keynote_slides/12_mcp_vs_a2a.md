# 슬라이드 12: MCP vs A2A 비교

## 두 프로토콜의 차이점

| 특징 | MCP | A2A |
|------|-----|-----|
| **용도** | 외부 도구/데이터 접근 | 에이전트 간 협업 |
| **통신 방식** | Request-Response | Event-Driven |
| **프로토콜** | JSON-RPC 2.0 | Custom Message |
| **상태 관리** | Stateless | Stateful |
| **표준화** | 공개 표준 | 자체 구현 |
| **확장성** | 도구 추가 용이 | 에이전트 추가 용이 |
| **에러 처리** | 동기식 | 비동기식 Fallback |

### 💡 핵심
**"각각의 강점을 살려 상호 보완적으로 사용"**