---
marp: true
theme: default
paginate: true
---

# MCP 심화 이해 2: 통신 프로토콜

## JSON-RPC 2.0 메시지 구조

### Request 메시지
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "database_query",
    "arguments": {
      "query": "SELECT * FROM users",
      "database": "production"
    }
  },
  "id": "req_123"
}
```

### Response 메시지
```json
{
  "jsonrpc": "2.0",
  "result": {
    "data": [{"id": 1, "name": "John"}],
    "rowCount": 1
  },
  "id": "req_123"
}
```

### 통신 흐름
1. **Initialize** → 2. **Capabilities** → 3. **Discovery** → 4. **Operation**

---