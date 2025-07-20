# 슬라이드 14: 전체 아키텍처

## AI 투자 분석 시스템 구조

```
사용자 → Web UI → Main Orchestrator (A2A)
                          ↓
            ┌─────────────┴─────────────┐
            ↓                           ↓
      [내부 에이전트들]            [MCP Agent]
         (A2A 통신)                     ↓
            ↓                    [외부 API/도구]
      - NLU Agent                 - Stock API
      - News Agent                - Chart Tools
      - Twitter Agent             - PDF Export
      - SEC Agent
      - Sentiment Agent
      - Score Agent
      - Risk Agent
      - Report Agent
```

### 핵심 설계 원칙
- **느슨한 결합**: 에이전트 독립성
- **높은 응집도**: 명확한 책임 분리
- **확장 가능**: 새 에이전트 추가 용이