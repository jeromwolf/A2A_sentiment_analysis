# Agent-to-Agent(A2A) 프로토콜과 투자 감성 분석 시스템 구현

## 발표 일정 (1시간)
- A2A 프로토콜 개념 소개 (15분)
- 프로토콜 구조 및 메시지 체계 (15분)
- 투자 감성 분석 시스템 아키텍처 (15분)
- 핵심 소스코드 리뷰 및 시연 (15분)

---

## 1부: Agent-to-Agent(A2A) 프로토콜이란? (15분)

### 1.1 A2A 프로토콜의 개념

#### 정의
- **분산 AI 에이전트 간 자율적 협업을 위한 통신 프로토콜**
- 마이크로서비스 아키텍처를 AI 에이전트에 적용
- 각 에이전트는 독립적으로 실행되며 표준화된 메시지로 통신

#### 핵심 특징
1. **자율성(Autonomy)**: 각 에이전트가 독립적으로 의사결정
2. **발견가능성(Discoverability)**: 동적으로 다른 에이전트를 찾아 협업
3. **확장성(Scalability)**: 새로운 에이전트를 쉽게 추가 가능
4. **내결함성(Fault Tolerance)**: 일부 에이전트 장애에도 시스템 동작

### 1.2 왜 A2A 프로토콜이 필요한가?

#### 기존 방식의 한계
```
[ 모놀리식 AI 시스템 ]
┌─────────────────────┐
│   단일 AI 모델      │
│  - NLP              │
│  - 데이터 수집      │
│  - 감성 분석        │
│  - 리포트 생성      │
└─────────────────────┘
문제점: 확장 어려움, 단일 장애점, 재사용성 낮음
```

#### A2A 방식의 장점
```
[ A2A 기반 분산 시스템 ]
┌─────┐  ┌─────┐  ┌─────┐
│ NLP │  │News │  │ SEC │
│Agent│  │Agent│  │Agent│
└──┬──┘  └──┬──┘  └──┬──┘
   │        │        │
   └────────┴────────┘
         Registry
```

### 1.3 실제 적용 사례: 투자 감성 분석

- **문제**: "애플 주식 어때?" → 종합적인 투자 분석 필요
- **해결**: 9개의 전문 AI 에이전트가 협업하여 분석
  - NLU: 자연어에서 종목 추출
  - 데이터 수집: 뉴스, 트위터, SEC 공시
  - 분석: 감성 분석, 정량 분석, 리스크 평가
  - 보고서: 종합 리포트 생성

---

## 2부: A2A 프로토콜 구조 및 메시지 체계 (15분)

### 2.1 프로토콜 아키텍처

#### 핵심 구성요소
```
┌─────────────────────────────────────────────┐
│             Service Registry                 │
│  - 에이전트 등록/해제                       │
│  - 능력(Capability) 기반 검색              │
│  - 헬스체크 및 하트비트                    │
└─────────────────────────────────────────────┘
                    ↑ ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  BaseAgent   │ │  BaseAgent   │ │  BaseAgent   │
│  - 자동등록  │ │  - 메시지큐  │ │  - 이벤트    │
│  - 메시지처리│ │  - 하트비트  │ │  - 브로드캐스팅│
└──────────────┘ └──────────────┘ └──────────────┘
```

### 2.2 메시지 프로토콜 상세

#### 메시지 구조
```json
{
  "header": {
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z",
    "sender_id": "news-agent-001",
    "receiver_id": "orchestrator-001",
    "message_type": "response",
    "protocol_version": "1.0",
    "correlation_id": "original-request-id"
  },
  "body": {
    "action": "news_data_collection",
    "payload": {
      "ticker": "AAPL",
      "articles": [...]
    }
  },
  "metadata": {
    "priority": "high",
    "ttl": 30,
    "require_ack": false
  }
}
```

#### 메시지 타입
1. **REQUEST**: 에이전트가 다른 에이전트에게 작업 요청
2. **RESPONSE**: 요청에 대한 응답 (correlation_id로 연결)
3. **EVENT**: 모든 에이전트에게 브로드캐스트
4. **ERROR**: 오류 발생 시 전송

### 2.3 에이전트 생명주기

```
1. 시작(Startup)
   ↓
2. 레지스트리 등록
   - agent_id, capabilities, endpoints
   ↓
3. 하트비트 시작 (30초 간격)
   ↓
4. 메시지 처리 루프
   - 메시지 수신 → 처리 → 응답
   ↓
5. 종료 시 레지스트리 해제
```

### 2.4 통신 패턴

#### 1. Direct Messaging (1:1)
```
Orchestrator → NLU Agent: "애플 주식 어때?"에서 ticker 추출 요청
NLU Agent → Orchestrator: ticker "AAPL" 응답
```

#### 2. Dynamic Discovery
```python
# 감성 분석 가능한 에이전트 찾기
agents = await registry.discover(capability="sentiment_analysis")
```

#### 3. Event Broadcasting
```python
# 데이터 수집 완료 이벤트 브로드캐스트
await agent.broadcast_event(
    event_type="data_collected",
    event_data={"source": "news", "count": 10}
)
```

---

## 3부: 투자 감성 분석 시스템 아키텍처 (15분)

### 3.1 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (index_v2.html)               │
│                    WebSocket 실시간 통신                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│              Main Orchestrator (port 8100)              │
│                 워크플로우 조정자                        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                Service Registry (port 8001)              │
│              에이전트 등록 및 발견 서비스                │
└─────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───┴────┐          ┌────┴────┐         ┌────┴────┐
│  NLU   │          │  Data   │         │Analysis │
│ Agent  │          │ Agents  │         │ Agents  │
│ (8108) │          │News(8307)│        │Sentiment│
│        │          │Twitter  │         │Quant    │
│        │          │ (8209)  │         │Score    │
│        │          │SEC(8210)│         │Risk     │
└────────┘          └─────────┘         └─────────┘
```

### 3.2 워크플로우 상세

#### Step 1: 사용자 질의 처리
```
사용자: "애플 주식 어때?"
    ↓ WebSocket
Orchestrator
    ↓ HTTP POST
NLU Agent: ticker 추출 → "AAPL"
```

#### Step 2: 병렬 데이터 수집
```
Orchestrator가 3개 에이전트에 동시 요청:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ News Agent  │  │Twitter Agent│  │ SEC Agent   │
│ Finnhub API │  │Twitter API  │  │ EDGAR API   │
└─────────────┘  └─────────────┘  └─────────────┘
```

#### Step 3: 감성 분석 및 점수 계산
```
Sentiment Agent (Gemini AI)
    ↓
Score Calculation Agent
- SEC 공시: 가중치 1.5 (가장 신뢰도 높음)
- 뉴스: 가중치 1.0 (표준)
- 트위터: 가중치 0.7 (변동성 높음)
    ↓
최종 점수: 가중 평균
```

#### Step 4: 종합 분석 및 보고서
```
Quantitative Agent: 기술적 지표 분석
    +
Risk Analysis Agent: 리스크 평가
    ↓
Report Generation Agent: HTML/PDF 보고서
```

### 3.3 각 에이전트 상세 기능

#### NLU Agent (자연어 이해)
- **기능**: 한국어/영어 종목명 → 티커 심볼 변환
- **예시**: "삼성전자" → "005930.KS", "애플" → "AAPL"
- **기술**: 정규표현식 + 사전 매핑

#### Data Collection Agents
1. **News Agent**
   - Finnhub API로 최신 뉴스 수집
   - 기사 본문 스크래핑 (BeautifulSoup)
   - 3개 기사 기본 분석

2. **Twitter Agent**
   - Twitter API v2 사용
   - 관련 트윗 및 감성 수집
   - 실시간 시장 분위기 파악

3. **SEC Agent**
   - EDGAR API로 공시 자료 수집
   - 10-K, 10-Q, 8-K 등 주요 서류
   - 재무 정보 추출

#### Analysis Agents
1. **Sentiment Analysis**
   - Gemini AI로 텍스트 감성 분석
   - -1(매우 부정) ~ +1(매우 긍정) 점수
   - 맥락 기반 심층 분석

2. **Quantitative Analysis**
   - yfinance로 가격 데이터 수집
   - 기술적 지표 계산 (MA, RSI 등)
   - 통계적 분석

3. **Risk Analysis**
   - 종합적 리스크 평가
   - 시장, 기업, 산업 리스크
   - 투자 권고사항

### 3.4 기술 스택

```
Backend:
- Python 3.8+
- FastAPI (비동기 웹 프레임워크)
- Uvicorn (ASGI 서버)
- Pydantic (데이터 검증)

AI/ML:
- Google Gemini AI
- pandas/numpy
- scipy

APIs:
- Finnhub (뉴스)
- Twitter API v2
- SEC EDGAR
- yfinance (주가)

Frontend:
- HTML5/CSS3/JavaScript
- WebSocket
- Chart.js (차트)
```

---

## 4부: 핵심 소스코드 리뷰 및 시연 (15분)

### 4.1 BaseAgent 구현 리뷰

```python
# a2a_core/base/base_agent.py
class BaseAgent:
    def __init__(self, agent_id: str, name: str, host: str, port: int):
        self.agent_id = agent_id
        self.message_queue = asyncio.Queue()
        self.capabilities = []
        
    async def start(self):
        # 1. 레지스트리 등록
        await self._register_with_registry()
        
        # 2. 하트비트 시작
        asyncio.create_task(self._heartbeat_loop())
        
        # 3. 메시지 처리 루프
        asyncio.create_task(self._process_messages())
        
        # 4. FastAPI 앱 생성
        self.app = self._create_app()
        
    async def send_message(self, receiver_id: str, action: str, payload: dict):
        """다른 에이전트에게 메시지 전송"""
        message = A2AMessage(
            header=MessageHeader(
                sender_id=self.agent_id,
                receiver_id=receiver_id,
                message_type=MessageType.REQUEST
            ),
            body=MessageBody(action=action, payload=payload)
        )
        
        # 수신자 정보 조회
        receiver = await self._get_agent_info(receiver_id)
        
        # HTTP POST로 메시지 전송
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{receiver['host']}:{receiver['port']}/message",
                json=message.dict()
            )
```

### 4.2 Service Registry 구현

```python
# a2a_core/registry/service_registry.py
class ServiceRegistry:
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.capability_index: Dict[str, Set[str]] = {}
        
    async def register_agent(self, agent_info: AgentInfo):
        """에이전트 등록"""
        self.agents[agent_info.agent_id] = agent_info
        
        # Capability 인덱싱
        for cap in agent_info.capabilities:
            if cap.name not in self.capability_index:
                self.capability_index[cap.name] = set()
            self.capability_index[cap.name].add(agent_info.agent_id)
            
    async def discover_agents(self, capability: str) -> List[AgentInfo]:
        """Capability로 에이전트 검색"""
        agent_ids = self.capability_index.get(capability, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
```

### 4.3 Main Orchestrator 워크플로우

```python
# main_orchestrator_v2.py
async def process_query(self, query: str, websocket):
    """전체 분석 워크플로우 조정"""
    try:
        # 1. NLU로 ticker 추출
        await self._send_to_ui(websocket, "status", {
            "message": "자연어 처리 중...",
            "agentId": "nlu"
        })
        ticker = await self._extract_ticker(query)
        
        # 2. 병렬 데이터 수집
        await self._send_to_ui(websocket, "status", {
            "message": "데이터 수집 중...",
            "agentId": "data_collection"
        })
        
        # 비동기 병렬 실행
        news_task = self._collect_news(ticker)
        twitter_task = self._collect_twitter(ticker)
        sec_task = self._collect_sec(ticker)
        
        news_data, twitter_data, sec_data = await asyncio.gather(
            news_task, twitter_task, sec_task
        )
        
        # 3. 감성 분석
        sentiment_result = await self._analyze_sentiment({
            "news": news_data,
            "twitter": twitter_data,
            "sec": sec_data
        })
        
        # 4. 점수 계산 (가중치 적용)
        final_score = await self._calculate_score(sentiment_result)
        
        # 5. 리포트 생성
        report = await self._generate_report(all_results)
        
        # 6. UI로 결과 전송
        await self._send_to_ui(websocket, "result", report)
        
    except Exception as e:
        await self._send_to_ui(websocket, "error", str(e))
```

### 4.4 실제 에이전트 구현 예시

```python
# agents/news_agent_v2_pure.py
class NewsAgentV2(BaseAgent):
    async def handle_message(self, message: A2AMessage) -> dict:
        """A2A 메시지 처리"""
        if message.body.action == "news_data_collection":
            ticker = message.body.payload.get("ticker")
            
            # 뉴스 데이터 수집
            news_data = await self._collect_news_data(ticker)
            
            # 수집 완료 이벤트 브로드캐스트
            await self.broadcast_event(
                event_type="data_collected",
                event_data={
                    "source": "news",
                    "ticker": ticker,
                    "count": len(news_data)
                }
            )
            
            # 응답 전송
            return {
                "success": True,
                "data": news_data,
                "metadata": {
                    "source": "finnhub",
                    "timestamp": datetime.now().isoformat()
                }
            }
```

### 4.5 시스템 시연

#### 시작 방법
```bash
# 1. 환경 설정
cp .env.example .env
# API 키 설정 필요

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 전체 시스템 시작
./start_v2_complete.sh

# 4. UI 접속
open http://localhost:8100
```

#### 시연 시나리오
1. "애플 주식 어때?" 질의 입력
2. 실시간 진행 상황 확인
3. 최종 분석 리포트 확인
4. PDF 다운로드

### 4.6 A2A 프로토콜의 장점 (실제 구현 경험)

1. **확장성**: 새 에이전트 추가가 매우 쉬움
2. **유지보수성**: 각 에이전트가 독립적이어서 개별 수정 가능
3. **재사용성**: 에이전트를 다른 프로젝트에서도 활용 가능
4. **내결함성**: 일부 에이전트 장애 시에도 나머지는 동작
5. **병렬처리**: 자연스러운 병렬 처리로 성능 향상

---

## Q&A 및 토론

### 예상 질문들

1. **Q: 왜 마이크로서비스 대신 A2A를 사용하나요?**
   - A: A2A는 AI 에이전트에 특화된 프로토콜로, 능력 기반 발견, 자율적 협업 등 AI 특화 기능 제공

2. **Q: 성능 오버헤드는 없나요?**
   - A: HTTP 통신 오버헤드는 있지만, 병렬 처리와 독립적 확장으로 상쇄

3. **Q: 보안은 어떻게 처리하나요?**
   - A: 현재는 내부망 사용 전제, 향후 JWT 인증 계획

4. **Q: 실제 프로덕션 사용이 가능한가요?**
   - A: 메시지 큐(Kafka/RabbitMQ) 통합, 분산 레지스트리 등 보완 필요

### 향후 발전 방향

1. **프로토콜 확장**
   - 메시지 암호화 (TLS)
   - 인증/인가 체계 (JWT)
   - 분산 레지스트리 (etcd/Consul)

2. **시스템 개선**
   - 메시지 큐 통합
   - 분산 트레이싱
   - 자동 스케일링

3. **새로운 에이전트**
   - 옵션 분석 에이전트
   - 포트폴리오 최적화 에이전트
   - 실시간 알림 에이전트

---

## 마무리

A2A 프로토콜은 복잡한 AI 시스템을 구축하는 새로운 패러다임을 제시합니다. 
각 에이전트가 자신의 전문 영역에 집중하면서도, 
표준화된 프로토콜을 통해 자유롭게 협업할 수 있습니다.

이 투자 감성 분석 시스템은 A2A 프로토콜의 실제 구현 사례로서,
9개의 전문 AI 에이전트가 협업하여 종합적인 투자 분석을 제공합니다.

**핵심 메시지**: 
"AI의 미래는 하나의 거대한 모델이 아닌, 
수많은 전문 에이전트들의 협업에 있습니다."

감사합니다.