---
marp: true
theme: default
paginate: true
backgroundColor: #fff
color: #1D1D1F
style: |
  /* 기본 폰트 설정 */
  section {
    font-family: 'Pretendard', 'SF Pro Display', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    font-size: 28px;
    line-height: 1.6;
  }
  
  /* 제목 스타일 */
  h1 {
    color: #007AFF;
    font-size: 56px;
    font-weight: 700;
    margin-bottom: 30px;
  }
  
  h2 {
    color: #1D1D1F;
    font-size: 48px;
    font-weight: 600;
    margin-bottom: 24px;
  }
  
  h3 {
    color: #FF9500;
    font-size: 36px;
    font-weight: 600;
    margin-bottom: 20px;
  }
  
  h4 {
    color: #5856D6;
    font-size: 32px;
    font-weight: 500;
    margin-bottom: 16px;
  }
  
  /* 본문 텍스트 */
  p, li {
    font-size: 28px;
    line-height: 1.8;
  }
  
  /* 강조 텍스트 */
  strong {
    font-weight: 600;
    color: #007AFF;
  }
  
  /* 인용구 */
  blockquote {
    font-size: 32px;
    font-style: italic;
    color: #5856D6;
    border-left: 4px solid #007AFF;
    padding-left: 20px;
    margin: 20px 0;
  }
  
  /* 코드 블록 */
  code {
    font-family: 'SF Mono', 'D2Coding', 'Consolas', monospace;
    font-size: 24px;
    background-color: #F5F5F7;
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  pre code {
    font-size: 22px;
    line-height: 1.5;
    padding: 20px;
  }
  
  /* 테이블 */
  table {
    margin: 0 auto;
    font-size: 26px;
    border-collapse: collapse;
  }
  
  th {
    font-weight: 600;
    background-color: #F5F5F7;
    padding: 12px 20px;
  }
  
  td {
    padding: 10px 20px;
    border-bottom: 1px solid #E5E5EA;
  }
  
  /* 리스트 */
  ul, ol {
    margin-left: 40px;
  }
  
  /* 유틸리티 클래스 */
  .center {
    text-align: center;
  }
  
  .small {
    font-size: 24px;
  }
  
  .large {
    font-size: 36px;
  }
  
  .emoji {
    font-size: 48px;
  }
---

<!-- _class: center -->

# A2A + MCP 하이브리드 아키텍처를 활용한
# AI 투자 분석 시스템

### 에이전트 간 협업과 외부 도구 통합의 실제 구현

<br>

발표자: [이름]
날짜: 2025년 7월 24일

---

# 목차

## 오늘의 발표 내용

1. **문제 정의와 배경**
   - 투자 분석의 도전 과제

2. **핵심 프로토콜 소개**
   - MCP (Model Context Protocol)
   - A2A (Agent-to-Agent) Protocol

3. **하이브리드 아키텍처**
   - 설계 철학과 구현

4. **실제 구현 사례**
   - 시스템 데모와 결과

5. **인사이트와 미래**
   - 배운 점과 향후 계획

---

# 문제 정의

## 투자 결정을 위해 필요한 정보는?

### 다양한 데이터 소스
- 📰 **뉴스**: 실시간 시장 동향
- 🐦 **소셜 미디어**: 투자자 심리
- 📊 **공시 자료**: 기업 재무 정보
- 📈 **시장 데이터**: 가격, 거래량

### 핵심 과제
> **"어떻게 이 모든 정보를 통합하여 
> 의미 있는 인사이트를 도출할 것인가?"**

---

# 기존 접근법의 한계

## 전통적인 시스템의 문제점

### 1. 직접 API 연동의 복잡성
- 각 데이터 소스마다 다른 API 규격
- 인증, 레이트 리밋, 에러 처리 중복

### 2. 확장성 부족
- 새로운 데이터 소스 추가 시 전체 시스템 수정
- 모듈 간 강한 결합도

### 3. 유지보수의 어려움
- API 변경 시 연쇄적인 수정 필요
- 단일 장애점(Single Point of Failure)

---

# 우리의 해결책

## A2A + MCP 하이브리드 아키텍처

### 두 가지 프로토콜의 조합

#### 내부 조율: A2A Protocol
- 에이전트 간 자율적 협업
- 유연한 워크플로우

#### 외부 연동: MCP
- 표준화된 도구/API 접근
- 일관된 인터페이스

### 💡 핵심 아이디어
> **"적재적소에 적합한 프로토콜 사용"**

---

# MCP란 무엇인가?

## Model Context Protocol (MCP)

### Anthropic이 제안한 개방형 표준

- **목적**: AI 모델과 외부 도구/데이터 간 통신 표준화
- **발표**: 2024년 11월
- **채택**: Claude, VSCode, 다양한 개발 도구

### 핵심 개념
> **"AI가 외부 세계와 소통하는 표준 언어"**

### 주요 특징
- JSON-RPC 2.0 기반
- 언어 중립적
- 확장 가능한 구조

---

# MCP 핵심 특징

## MCP의 주요 구성 요소

### 1. Tools (도구)
- 실행 가능한 함수들
- 파라미터와 반환값 정의

### 2. Resources (리소스)
- 접근 가능한 데이터
- 파일, DB, API 등

### 3. Prompts (프롬프트)
- 재사용 가능한 템플릿
- 컨텍스트 관리

### 특징
- ✅ **Stateless**: 상태 비저장
- ✅ **표준화**: 일관된 인터페이스
- ✅ **보안**: 권한 관리 내장

---

# MCP 코드 예제

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
    "arguments": {"ticker": "AAPL"}
  },
  "id": 2
}
```

---

# A2A란 무엇인가?

## Agent-to-Agent Protocol

### 에이전트 간 직접 통신 프로토콜

- **목적**: 자율적인 AI 에이전트들의 협업
- **특징**: 중앙 집중식 제어 없이 P2P 통신
- **장점**: 확장성, 유연성, 장애 격리

### 핵심 개념
> **"에이전트들이 서로 대화하며 문제를 해결"**

### 실제 활용
- 각 에이전트는 특정 역할 수행
- 필요 시 다른 에이전트에게 작업 위임
- 이벤트 기반 비동기 통신

---

# A2A 핵심 특징

## A2A의 주요 구성 요소

### 1. BaseAgent (기본 에이전트)
- 모든 에이전트의 기반 클래스
- 메시지 송수신 기능 내장

### 2. Registry Server (레지스트리)
- 에이전트 등록 및 발견
- 실시간 상태 모니터링

### 3. Message Protocol (메시지 프로토콜)
- 헤더: 송신자, 수신자, 메시지 ID
- 바디: 액션, 페이로드

### 특징
- ✅ **Stateful**: 상태 유지
- ✅ **이벤트 기반**: 비동기 통신
- ✅ **자율성**: 독립적 의사결정

---

# A2A 코드 예제

## A2A 통신 예시

### 메시지 전송
```python
# 감성 분석 요청
await self.send_message(
    recipient="sentiment-agent",
    action="analyze",
    payload={
        "ticker": "AAPL",
        "data": collected_data
    }
)
```

### 메시지 처리
```python
async def handle_message(self, message: A2AMessage):
    if message.body.get("action") == "analyze":
        result = await self.analyze_sentiment(
            message.body.get("payload")
        )
        await self.reply_to_message(message, result)
```

---

# MCP vs A2A 비교

## 두 프로토콜의 차이점

| 특징 | MCP | A2A |
|------|-----|-----|
| **용도** | 외부 도구/데이터 접근 | 에이전트 간 협업 |
| **통신 방식** | Request-Response | Event-Driven |
| **프로토콜** | JSON-RPC 2.0 | Custom Message |
| **상태 관리** | Stateless | Stateful |
| **표준화** | 공개 표준 | 자체 구현 |
| **확장성** | 도구 추가 용이 | 에이전트 추가 용이 |

### 💡 핵심
> **"각각의 강점을 살려 상호 보완적으로 사용"**

---

# 왜 하이브리드인가?

## 하이브리드 아키텍처의 장점

### 내부 시스템: A2A
- ✅ 에이전트 간 유연한 협업
- ✅ 복잡한 워크플로우 처리
- ✅ 상태 관리와 이벤트 처리

### 외부 연동: MCP
- ✅ 표준화된 API 접근
- ✅ 다양한 도구 통합
- ✅ 보안과 권한 관리

### 시너지 효과
1. **유연성**: 내부는 자유롭게, 외부는 표준으로
2. **확장성**: 양방향 확장 가능
3. **안정성**: 프로토콜별 격리로 장애 최소화

---

# 전체 아키텍처

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
```

---

# 에이전트 구성

## 11개 전문 에이전트의 역할

### 데이터 수집 (4개)
- **NLU Agent**: 자연어 → 티커 추출
- **News Agent**: 뉴스 데이터 수집
- **Twitter Agent**: 소셜 미디어 감성
- **SEC Agent**: 기업 공시 자료

### 분석 처리 (5개)
- **Sentiment Agent**: 감성 분석 (Gemini AI)
- **Quantitative Agent**: 기술적 지표 분석
- **Score Agent**: 가중치 기반 점수 계산
- **Risk Agent**: 리스크 평가
- **Report Agent**: 최종 리포트 생성

---

# 데이터 플로우

## 요청에서 응답까지의 여정

### 1️⃣ 사용자 질문
"애플 주가 어때?"

### 2️⃣ NLU 처리
질문 → 티커 추출 (AAPL)

### 3️⃣ 병렬 데이터 수집
- News: 5개 기사
- Twitter: 실시간 트윗
- SEC: 최근 공시

### 4️⃣ 통합 분석
- 감성 점수 계산
- 기술적 지표 분석

### 5️⃣ 최종 리포트
종합 투자 분석 보고서 생성

---

# 기술 스택

## 사용된 기술들

### Backend
- **Python 3.11**: 메인 언어
- **FastAPI**: 비동기 웹 프레임워크
- **WebSocket**: 실시간 통신
- **asyncio**: 비동기 처리

### AI/ML
- **Gemini AI**: 감성 분석
- **yfinance**: 주가 데이터
- **ta**: 기술적 지표

### 외부 API
- NewsAPI, Finnhub
- Twitter API v2
- SEC EDGAR

---

# 확장성 설계

## 새로운 기능 추가가 쉬운 이유

### 새 데이터 소스 추가 예시

```python
# 1. 새 에이전트 생성
class RedditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Reddit Agent",
            port=8220
        )
    
    async def collect_reddit_data(self, ticker):
        # Reddit API 호출
        return reddit_posts

# 2. 자동 등록 및 통합
# 시스템 재시작만으로 즉시 사용 가능
```

---

# BaseAgent 클래스

## 모든 에이전트의 기반

### 핵심 기능
```python
class BaseAgent:
    # 1. 자동 등록
    async def start(self):
        await self._register_with_registry()
        await self._start_heartbeat()
    
    # 2. 메시지 전송
    async def send_message(self, 
                          recipient: str,
                          action: str,
                          payload: dict):
        # A2A 프로토콜로 전송
```

### 상속만으로 즉시 A2A 에이전트화
- 레지스트리 등록 자동화
- 헬스체크 자동화
- 메시지 라우팅 자동화

---

# 메시지 프로토콜

## A2A 메시지 구조

```python
class A2AMessage:
    header: MessageHeader
    body: Dict[str, Any]

class MessageHeader:
    message_id: str      # 고유 ID
    message_type: str    # REQUEST/RESPONSE/EVENT
    sender_id: str       # 송신 에이전트
    recipient_id: str    # 수신 에이전트
    timestamp: datetime  # 타임스탬프
    correlation_id: str  # 요청-응답 매칭
```

### 메시지 타입
- **REQUEST**: 작업 요청
- **RESPONSE**: 요청에 대한 응답
- **EVENT**: 브로드캐스트 이벤트

---

# 레지스트리 서버

## 에이전트 디스커버리

### 1. 에이전트 등록
```json
POST /register
{
  "name": "News Agent",
  "endpoint": "http://localhost:8307",
  "capabilities": ["news_collection"]
}
```

### 2. 에이전트 발견
```json
GET /discover?capability=news_collection
→ 해당 능력을 가진 에이전트 목록
```

### 3. 헬스 모니터링
- 30초마다 하트비트
- 실패 시 자동 제거

---

# 데이터 수집 병렬화

## 성능 최적화: 동시 실행

### 순차 실행 (기존 방식)
```
News (2초) → Twitter (3초) → SEC (2초) = 총 7초
```

### 병렬 실행 (A2A 방식)
```python
# 모든 에이전트에게 동시 요청
tasks = []
for agent in ["news", "twitter", "sec", "mcp"]:
    task = self.send_message(
        recipient=agent,
        action="collect_data",
        payload={"ticker": ticker}
    )
    tasks.append(task)

# 동시 실행
await asyncio.gather(*tasks)
```

**성능 향상: 7초 → 3초 (57% 단축)**

---

# 에러 처리

## 장애 대응: Fallback 메커니즘

### 3단계 에러 처리

#### 1️⃣ A2A 통신 시도
```python
success = await self.send_message(
    recipient="news-agent",
    action="collect_data"
)
```

#### 2️⃣ 실패 시 HTTP 직접 호출
```python
if not success:
    response = await http_client.post(
        "http://localhost:8307/collect_news_data"
    )
```

#### 3️⃣ 그래도 실패 시 기본값
```python
return {"data": [], "error": "Service unavailable"}
```

---

# 시연 시나리오

## 실제 시스템 작동 과정

### 시연 내용
**"애플 주가 어때?"**

### 예상 플로우
1. **자연어 이해**: "애플" → "AAPL"
2. **데이터 수집** (병렬)
   - 📰 뉴스: 5건
   - 🐦 트위터: 실시간
   - 📊 SEC: 최근 공시
3. **AI 분석**
   - 감성 점수: 65/100
   - 기술 지표: RSI 50
4. **종합 평가**
   - 투자 의견: 중립

---

<!-- _class: center -->

# 실행 과정

## [시연 영상]

<br>

### 📹 녹화된 데모 영상 재생

<br>

총 소요 시간: 약 15초

---

# 분석 결과

## 생성된 투자 분석 리포트

### 📊 AAPL 종합 분석 결과

#### 감성 분석 점수: 65/100 (긍정적)
- 뉴스: 70점 (긍정적 실적 전망)
- 소셜: 55점 (혼재된 의견)
- 공시: 70점 (안정적 재무)

#### 기술적 지표
- RSI: 50 (중립)
- MACD: 중립 신호

#### 💡 투자 의견
**"단기 관망, 장기 긍정적"**

---

# 성능 지표

## 시스템 성능 분석

| 단계 | 시간 |
|------|------|
| NLU 처리 | 0.5초 |
| 데이터 수집 (병렬) | 3초 |
| 감성 분석 | 2초 |
| 점수 계산 | 0.5초 |
| 리포트 생성 | 1초 |
| **총 시간** | **약 7초** |

### 처리 용량
- 동시 요청: 50개
- 시간당 처리: 500+ 분석

---

# 실제 활용 사례

## 다양한 활용 시나리오

### 1. 개인 투자자
- 투자 전 종합 분석
- 포트폴리오 모니터링

### 2. 금융 기관
- 고객 상담 지원
- 리서치 자동화

### 3. 핀테크 스타트업
- API로 서비스 통합
- 로보어드바이저 백엔드

### 확장 가능성
- 암호화폐 분석
- 부동산 투자 분석
- ESG 투자 평가

---

# 배운 점

## 프로젝트를 통해 얻은 인사이트

### 기술적 교훈
1. **프로토콜 선택의 중요성**
   - 용도에 맞는 프로토콜 사용
   - 과도한 표준화는 오히려 제약

2. **비동기 처리의 힘**
   - 병렬 실행으로 큰 성능 향상
   - 이벤트 기반 아키텍처의 유연성

3. **에러 처리의 중요성**
   - Graceful Degradation
   - 부분 실패 허용 설계

---

# 향후 계획

## 다음 단계는?

### 단기 계획 (3개월)
- ✨ 더 많은 데이터 소스 추가
- 📊 실시간 모니터링 대시보드
- 🔔 알림 시스템 구축

### 중기 계획 (6개월)
- 🤖 자체 LLM 파인튜닝
- 📈 백테스팅 기능

### 장기 비전
- **오픈소스 프로젝트화**
- **AI 투자 분석 표준 제시**

### 💬 함께 만들어가요!
GitHub: [프로젝트 링크]
Email: [연락처]

---

<!-- _class: center -->

# 감사합니다

## Q&A

<br>

### 🙋 질문을 환영합니다!

<br>

**발표자료 및 소스코드**
github.com/[your-repo]