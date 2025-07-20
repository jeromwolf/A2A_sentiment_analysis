---
marp: true
theme: default
paginate: true
---

# MCP 심화 이해 4: 실전 통합

## 우리 프로젝트의 MCP 설정

### 1. 투자 분석 MCP 서버 설정
```json
{
  "mcpServers": {
    "investment-analysis": {
      "command": "python",
      "args": ["/path/to/mcp-investment-analysis-server/server.py"],
      "env": {
        "BLOOMBERG_API_KEY": "${BLOOMBERG_KEY}",
        "REFINITIV_TOKEN": "${REFINITIV_TOKEN}",
        "FACTSET_CREDENTIALS": "${FACTSET_CREDS}"
      }
    }
  }
}
```

### 2. 제공하는 프리미엄 금융 도구
```python
# MCP 서버가 제공하는 도구들
tools = [
    {
        "name": "get_bloomberg_data",
        "description": "Bloomberg Terminal 데이터 조회",
        "premium": True
    },
    {
        "name": "get_refinitiv_eikon", 
        "description": "Refinitiv Eikon 실시간 데이터",
        "premium": True
    },
    {
        "name": "analyze_market_sentiment",
        "description": "AI 기반 시장 심리 분석"
    }
]
```

### 3. A2A와 MCP 통합 포인트
- **MCP Data Agent** (port: 8214)가 브리지 역할
- A2A 메시지를 받아 MCP 도구 호출
- 결과를 다시 A2A로 전달

---