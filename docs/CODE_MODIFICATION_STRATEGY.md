# 코드 수정 전략 - MCP + A2A 프로토콜 완전 구현

## 목표
발표에서 "우리는 MCP와 A2A 프로토콜을 제대로 구현했다"고 자신있게 말할 수 있도록 코드 수정

## 수정 우선순위

### Phase 1: A2A 프로토콜 실제 사용 (2-3시간)
1. **main_orchestrator_v2.py 수정**
   - 모든 HTTP 직접 호출을 A2A 메시지로 변경
   - 메시지 응답 대기 및 처리 로직 구현
   
2. **데이터 수집 에이전트들 A2A 지원**
   - news_agent_v2.py
   - twitter_agent_v2.py
   - sec_agent_v2_pure.py
   - dart_agent_v2.py

3. **분석 에이전트들 A2A 지원**
   - sentiment_analysis_agent_v2.py
   - quantitative_analysis_agent_v2.py
   - score_calculation_agent_v2.py

### Phase 2: MCP 표준 구현 강화 (1-2시간)
1. **MCP 서버 시뮬레이터 구현**
   - 실제 MCP 서버처럼 동작하는 목업 서버
   - JSON-RPC 2.0 완전 지원
   
2. **mcp_data_agent.py 개선**
   - 실제 MCP 클라이언트 사용
   - 도구 목록 조회 기능
   - 리소스 접근 기능

### Phase 3: 시연 가능한 데모 준비 (1시간)
1. **로깅 및 모니터링**
   - A2A 메시지 흐름 시각화
   - MCP 호출 로그
   
2. **에러 처리**
   - 우아한 실패 처리
   - 폴백 메커니즘

## 구체적인 수정 계획

### 1. main_orchestrator_v2.py 수정

**현재 코드 (HTTP 직접 호출):**
```python
# _send_data_collection_request_http 메서드
response = await http_client.post(
    f"http://localhost:{port}/collect_{agent_type}_data",
    json={"ticker": ticker}
)
```

**수정할 코드 (A2A 메시지):**
```python
# _send_data_collection_request_a2a 메서드
message = await self.send_message(
    receiver_id=f"{agent_type}-agent",
    action="collect_data",
    payload={"ticker": ticker},
    priority=Priority.HIGH
)

# 응답 대기
response = await self.wait_for_response(message.header.message_id)
```

### 2. 에이전트 메시지 핸들러 수정

**모든 에이전트에 추가할 코드:**
```python
async def handle_message(self, message: A2AMessage):
    """A2A 메시지 처리"""
    if message.header.message_type == MessageType.REQUEST:
        action = message.body.get("action")
        
        if action == "collect_data":
            # 데이터 수집 로직
            result = await self.collect_data(
                message.body.get("payload", {})
            )
            
            # A2A 응답 전송
            await self.reply_to_message(
                message,
                result={"data": result},
                success=True
            )
```

### 3. MCP 서버 시뮬레이터

**새 파일: mcp_server_simulator.py**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.post("/")
async def handle_jsonrpc(request: dict):
    """JSON-RPC 2.0 요청 처리"""
    method = request.get("method")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "Investment MCP Server"}
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "tools": [
                    {
                        "name": "getAnalystReports",
                        "description": "Get analyst reports"
                    }
                ]
            }
        }
```

### 4. 시각적 로깅 추가

**utils/protocol_logger.py**
```python
class ProtocolLogger:
    @staticmethod
    def log_a2a_message(message: A2AMessage, direction: str):
        """A2A 메시지 로깅"""
        if direction == "SEND":
            print(f"📤 [A2A] {message.header.sender_id} → {message.header.receiver_id}")
            print(f"   Action: {message.body.get('action')}")
            print(f"   ID: {message.header.message_id}")
        else:
            print(f"📥 [A2A] {message.header.sender_id} → {message.header.receiver_id}")
            print(f"   Response: {'SUCCESS' if message.body.get('success') else 'FAILED'}")
    
    @staticmethod
    def log_mcp_call(method: str, params: dict):
        """MCP 호출 로깅"""
        print(f"🔧 [MCP] Method: {method}")
        print(f"   Params: {params}")
```

## 실행 계획

### Step 1: 백업
```bash
cp -r . ../a2a_sentiment_analysis_backup
```

### Step 2: 브랜치 생성
```bash
git checkout -b feature/real-a2a-mcp-implementation
```

### Step 3: 단계별 수정
1. main_orchestrator_v2.py 수정 (30분)
2. 각 에이전트 handle_message 추가 (1시간)
3. MCP 서버 시뮬레이터 구현 (30분)
4. 로깅 및 테스트 (30분)

### Step 4: 테스트
```bash
# 전체 시스템 테스트
./start_v2_complete.sh

# 개별 컴포넌트 테스트
python -m pytest tests/test_a2a_messages.py
```

## 성공 기준

1. ✅ 모든 에이전트 간 통신이 A2A 메시지로 이루어짐
2. ✅ 레지스트리에서 에이전트 동적 발견
3. ✅ MCP 서버와 실제 JSON-RPC 통신
4. ✅ 로그에서 프로토콜 흐름 확인 가능
5. ✅ 에러 발생 시에도 시스템 안정성 유지

## 위험 요소 및 대응

1. **시간 부족**
   - 핵심 부분만 수정하고 나머지는 "진행 중"으로 표시
   
2. **버그 발생**
   - 기존 코드 백업 유지
   - 핵심 기능만 A2A로 전환
   
3. **성능 저하**
   - 캐싱 강화
   - 타임아웃 조정