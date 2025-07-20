---
marp: true
theme: default
paginate: true
---

# MCP 심화 이해 1: 아키텍처

## Model Context Protocol 기술 아키텍처

### 핵심 구성 요소

```
┌─────────────┐     JSON-RPC 2.0      ┌─────────────┐
│  MCP Host   │◄────────────────────►│ MCP Server  │
│  (Claude,   │                      │ (데이터소스) │
│   ChatGPT)  │                      └─────────────┘
└─────────────┘
       │
       ▼
┌─────────────┐
│ MCP Client  │
│ (프로토콜   │
│  구현체)    │
└─────────────┘
```

### 설계 원칙
1. **Transport-agnostic**: stdio, HTTP/SSE, WebSocket 모두 지원
2. **Stateful Connection**: 연결 상태 유지, 세션 관리
3. **Capability Negotiation**: 클라이언트-서버 간 기능 협상
4. **Language Server Protocol 기반**: 검증된 아키텍처 차용

---