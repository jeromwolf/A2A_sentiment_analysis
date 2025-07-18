# 에이전트 투자 시대를 준비하다
## MCP + A2A 기반 협업 분석 시스템

### 발표자: 캘리

---

## 1. 서론: 왜 프로토콜이 중요한가?

### 현재 AI 시스템의 한계
```
[현재 상황]
ChatGPT ←X→ Claude ←X→ Gemini ←X→ Custom AI
   ↓           ↓          ↓           ↓
 고립된      서로       통신       불가능
```

### 프로토콜이 가져올 미래
```
[프로토콜 기반 미래]
ChatGPT ←→ Claude ←→ Gemini ←→ Custom AI
   ↑           ↑          ↑           ↑
      공통 프로토콜로 자유로운 협업
```

---

## 2. MCP (Model Context Protocol) 이해하기

### MCP란?
**"AI 모델들이 외부 도구와 데이터에 접근하는 표준 방법"**

### 핵심 개념
```
┌─────────────┐     MCP Protocol    ┌──────────────┐
│   AI Model  │ ←─────────────────→ │  MCP Server  │
│  (Claude)   │    JSON-RPC 2.0     │ (Data/Tools) │
└─────────────┘                     └──────────────┘
        ↓                                   ↓
   요청: "주가 데이터"              제공: 실시간 데이터
```

### MCP 구조 (우리의 구현)
```python
# 1. MCP 메시지 구조 (JSON-RPC 2.0)
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "getStockData",
        "arguments": {"ticker": "AAPL"}
    },
    "id": 1
}

# 2. 우리가 구현한 MCP 클라이언트
class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        
    async def call_tool(self, tool_name: str, arguments: dict):
        # JSON-RPC 2.0 형식으로 요청
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self.request_id
        }
        # 서버로 전송하고 응답 받기
        response = await self.send_request(request)
        return response["result"]
```

### MCP 장점
1. **표준화**: Anthropic이 만든 공식 프로토콜
2. **호환성**: 모든 AI 시스템이 같은 방식으로 도구 사용
3. **확장성**: 새로운 도구 추가가 쉬움

---

## 3. A2A (Agent-to-Agent) 프로토콜 이해하기

### A2A란?
**"AI 에이전트들이 서로 대화하는 표준 방법"**

### 왜 A2A가 필요한가?
```
[일반 API 호출]
에이전트A → HTTP POST → 에이전트B
- 하드코딩된 엔드포인트
- 에이전트 추가 시 모든 코드 수정
- 장애 전파

[A2A 프로토콜]
에이전트A → 레지스트리 → 에이전트B 발견 → 메시지 전송
- 동적 발견
- 느슨한 결합
- 장애 격리
```

### 우리의 A2A 구현

#### 1. 메시지 구조
```python
# a2a_core/protocols/message.py
@dataclass
class MessageHeader:
    message_id: str      # 고유 ID
    sender_id: str       # 보낸 에이전트
    receiver_id: str     # 받을 에이전트
    timestamp: datetime  # 시간
    message_type: MessageType  # REQUEST/RESPONSE/EVENT
    correlation_id: str  # 요청-응답 매칭

@dataclass
class A2AMessage:
    header: MessageHeader
    body: Dict[str, Any]
    metadata: MessageMetadata
```

#### 2. 서비스 레지스트리
```python
# a2a_core/registry/registry_server.py
class ServiceRegistry:
    def register_agent(self, agent_info: AgentInfo):
        """에이전트 등록"""
        self.agents[agent_info.agent_id] = agent_info
        
    def discover_agents(self, capability: str = None):
        """능력 기반 에이전트 발견"""
        if capability:
            return [a for a in self.agents.values() 
                   if capability in a.capabilities]
        return list(self.agents.values())
```

#### 3. 베이스 에이전트
```python
# a2a_core/base/base_agent.py
class BaseAgent(ABC):
    async def send_message(self, receiver_id: str, 
                          action: str, payload: dict):
        """A2A 메시지 전송"""
        # 1. 레지스트리에서 수신자 찾기
        receiver = await self.discover_agent(receiver_id)
        
        # 2. 메시지 생성
        message = A2AMessage.create_request(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            action=action,
            payload=payload
        )
        
        # 3. 전송
        response = await self.http_client.post(
            f"{receiver.endpoint}/message",
            json=message.to_dict()
        )
```

---

## 4. 우리 시스템의 설계 철학

### 레이어드 아키텍처
```
┌─────────────────────────────────────┐
│         사용자 인터페이스 (UI)        │
├─────────────────────────────────────┤
│        오케스트레이터 (조정자)        │
├─────────────────────────────────────┤
│      A2A 프로토콜 레이어            │
├─────────────────────────────────────┤
│   에이전트들 (10개의 전문 AI)        │
├─────────────────────────────────────┤
│      MCP 프로토콜 레이어            │
├─────────────────────────────────────┤
│   외부 데이터/도구 (API, DB)         │
└─────────────────────────────────────┘
```

### 실제 동작 흐름 (코드로 보기)

#### Step 1: 사용자 요청
```javascript
// index_v2.html
socket.send(JSON.stringify({
    action: 'analyze',
    query: '애플 주가 전망 어때?'
}));
```

#### Step 2: 오케스트레이터가 A2A로 NLU 에이전트 호출
```python
# main_orchestrator_v2.py
async def handle_user_query(self, query: str):
    # A2A 메시지로 NLU 에이전트 호출
    message = await self.send_message(
        receiver_id="nlu-agent",
        action="extract_ticker",
        payload={"query": query}
    )
```

#### Step 3: NLU 에이전트의 메시지 처리
```python
# agents/nlu_agent_v2.py
async def handle_message(self, message: A2AMessage):
    if message.body.get("action") == "extract_ticker":
        query = message.body.get("payload", {}).get("query")
        
        # 티커 추출 로직
        ticker = self.extract_ticker(query)
        
        # A2A 응답 전송
        await self.reply_to_message(
            message,
            result={"ticker": ticker, "exchange": "NASDAQ"},
            success=True
        )
```

#### Step 4: 데이터 수집 (병렬 처리)
```python
# 여러 에이전트에게 동시에 A2A 메시지 전송
tasks = []
for agent_id in ["news-agent", "twitter-agent", "sec-agent"]:
    task = self.send_message(
        receiver_id=agent_id,
        action="collect_data",
        payload={"ticker": "AAPL"}
    )
    tasks.append(task)

# 모든 응답 대기
results = await asyncio.gather(*tasks)
```

#### Step 5: MCP를 통한 프리미엄 데이터 접근
```python
# agents/mcp_data_agent.py
async def get_premium_data(self, ticker: str):
    # MCP 프로토콜로 외부 데이터 요청
    result = await self.mcp_client.call_tool(
        "getAnalystReports",
        {"ticker": ticker, "limit": 5}
    )
    return result
```

---

## 5. 프로토콜 기반 설계의 장점

### 1. 플러그 앤 플레이
```python
# 새로운 에이전트 추가가 간단함
class NewAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="New Analysis Agent",
            port=8999
        )
        self.add_capability("new_analysis")
    
    async def handle_message(self, message):
        # 메시지 처리 로직만 구현하면 됨
        pass
```

### 2. 장애 격리
```python
# 한 에이전트 장애가 전체 시스템에 영향 없음
try:
    result = await self.send_message("twitter-agent", ...)
except Exception:
    # Twitter 에이전트 장애 시 다른 분석은 계속
    logger.warning("Twitter agent unavailable")
    continue
```

### 3. 동적 확장
```yaml
# 설정만으로 에이전트 추가/제거
agents:
  - name: "Crypto Agent"
    port: 8216
    capabilities: ["crypto_analysis"]
  - name: "ESG Agent"  
    port: 8217
    capabilities: ["esg_scoring"]
```

---

## 6. 실제 구현 시연

### 시연 1: A2A 메시지 흐름 보기
```bash
# 레지스트리에서 등록된 에이전트 확인
curl http://localhost:8001/agents

# 응답
{
  "agents": [
    {"agent_id": "nlu-agent", "capabilities": ["ticker_extraction"]},
    {"agent_id": "news-agent", "capabilities": ["news_collection"]},
    ...
  ]
}
```

### 시연 2: 프로토콜 로그 확인
```
[오케스트레이터]
📤 A2A 메시지 전송: extract_ticker -> nlu-agent
   Message ID: 550e8400-e29b-41d4-a716-446655440000

[NLU 에이전트]
📨 A2A 메시지 수신: extract_ticker from orchestrator
   처리 중...
📤 A2A 응답 전송: SUCCESS (ticker: AAPL)
```

### 시연 3: MCP 도구 호출
```python
# MCP 서버에 도구 목록 요청
{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
}

# 응답
{
    "jsonrpc": "2.0",
    "result": {
        "tools": [
            {
                "name": "getStockData",
                "description": "실시간 주가 조회"
            },
            {
                "name": "getAnalystReports",  
                "description": "애널리스트 리포트"
            }
        ]
    }
}
```

---

## 7. 다른 프로젝트와의 차별점

### 일반적인 AI 시스템
```python
# 하드코딩된 API 호출
def analyze_stock(ticker):
    news = requests.post("http://localhost:8080/news", {"ticker": ticker})
    sentiment = requests.post("http://localhost:8081/sentiment", {"data": news})
    return sentiment
```

### 우리의 프로토콜 기반 시스템
```python
# 동적이고 확장 가능한 구조
async def analyze_stock(ticker):
    # 필요한 능력을 가진 에이전트 자동 발견
    collectors = await self.discover_agents("data_collection")
    analyzers = await self.discover_agents("sentiment_analysis")
    
    # 프로토콜 기반 통신
    for agent in collectors:
        await self.send_message(agent.agent_id, "collect", {"ticker": ticker})
```

---

## 8. 핵심 메시지

### 우리가 구현한 것
1. ✅ **A2A 프로토콜 완전 구현**
   - 메시지 구조, 레지스트리, 베이스 에이전트
   - 10개 에이전트가 실제로 A2A로 통신

2. ✅ **MCP 클라이언트 구현**
   - JSON-RPC 2.0 표준 준수
   - 외부 도구/데이터 접근 준비 완료

3. ✅ **실제 작동하는 투자 분석 시스템**
   - 뉴스, SNS, 공시 통합 분석
   - 실시간 처리 및 결과 제공

### 왜 이것이 미래인가?
**"프로토콜은 AI 시대의 TCP/IP입니다"**
- 인터넷이 TCP/IP로 연결되었듯이
- AI들은 MCP/A2A로 연결될 것입니다

---

## 마무리

**"우리는 단순히 투자 분석 도구를 만든 것이 아닙니다.
AI 에이전트들이 협업하는 미래의 표준을 구현했습니다."**

감사합니다! 🙏