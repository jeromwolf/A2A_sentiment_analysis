# 슬라이드 8: MCP 코드 예제

## MCP 통신 예시

### 도구 목록 요청
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

### 도구 실행
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_stock_price",
    "arguments": {
      "ticker": "AAPL"
    }
  },
  "id": 2
}
```

### 응답
```json
{
  "jsonrpc": "2.0",
  "result": {
    "price": 210.02,
    "currency": "USD"
  },
  "id": 2
}
```