# MCP Integration Guide - A2A와 외부 MCP 서버 연동

## 개요

이 문서는 A2A 시스템이 외부 MCP (Model Context Protocol) 서버를 호출하여 사용하는 방법을 설명합니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   A2A System                             │
│                                                         │
│  ┌─────────────────┐     ┌──────────────────────────┐ │
│  │ Orchestrator    │────▶│ MCP Yahoo Finance Agent  │ │
│  └─────────────────┘     └───────────┬──────────────┘ │
│                                      │                  │
│  ┌─────────────────┐     ┌──────────┼──────────────┐ │
│  │ Other A2A       │     │ MCP Alpha│Vantage Agent │ │
│  │ Agents          │     └───────────┴──────────────┘ │
│  └─────────────────┘                 │                 │
└──────────────────────────────────────┼─────────────────┘
                                       │
                    External MCP Servers
                                       │
         ┌─────────────────────────────┼─────────────────────────┐
         │                             │                         │
    ┌────▼──────────┐         ┌───────▼────────┐       ┌───────▼────────┐
    │ Yahoo Finance │         │ Alpha Vantage  │       │   Polygon.io   │
    │  MCP Server   │         │  MCP Server    │       │  MCP Server    │
    └───────────────┘         └────────────────┘       └────────────────┘
```

## 구현 내용

### 1. MCP 클라이언트 (utils/mcp_client.py)
- JSON-RPC 2.0 프로토콜 구현
- 표준 MCP 메서드 지원:
  - `initialize`: 서버 초기화
  - `tools/list`: 도구 목록 조회
  - `tools/call`: 도구 실행
  - `resources/read`: 리소스 읽기

### 2. A2A MCP 에이전트

#### MCP Yahoo Finance Agent (포트 8213)
```python
# 기존 quantitative_analysis_agent를 대체
# Yahoo Finance MCP 서버 호출하여 데이터 수집

주요 기능:
- 실시간 주가 조회
- 기업 정보 조회
- 과거 가격 데이터
- 기술적 지표 계산
- 재무제표 조회
```

#### MCP Alpha Vantage Agent (포트 8214)
```python
# 고급 시장 데이터 제공
# Alpha Vantage MCP 서버 호출

주요 기능:
- 실시간 주가 (QUOTE_ENDPOINT)
- 시계열 데이터 (TIME_SERIES_DAILY)
- 기술적 지표 (RSI, MACD, BB, SMA, EMA)
- 회사 개요 (OVERVIEW)
```

## 설치 및 실행

### 1. 환경 변수 설정
```bash
# .env 파일에 추가
ALPHA_VANTAGE_API_KEY=your_api_key_here
YAHOO_FINANCE_MCP_URL=http://localhost:3001
ALPHA_VANTAGE_MCP_URL=http://localhost:3002
```

### 2. Docker Compose로 실행
```bash
# 기존 A2A 시스템 실행
docker-compose up -d

# MCP 서버 및 에이전트 추가 실행
docker-compose -f docker-compose.mcp.yml up -d
```

### 3. 개별 실행 (개발용)
```bash
# Yahoo Finance MCP 서버 실행 (별도 터미널)
git clone https://github.com/Alex2Yang97/yahoo-finance-mcp
cd yahoo-finance-mcp
npm install
npm start

# Alpha Vantage MCP 서버 실행 (별도 터미널)
git clone https://github.com/berlinbra/alpha-vantage-mcp
cd alpha-vantage-mcp
npm install
ALPHA_VANTAGE_API_KEY=your_key npm start

# A2A MCP 에이전트 실행
python agents/mcp_yahoo_finance_agent.py
python agents/mcp_alpha_vantage_agent.py
```

## 사용 예시

### 1. 오케스트레이터에서 MCP 에이전트 호출
```python
# main_orchestrator_v2.py 수정 예시

async def analyze_with_mcp(ticker: str):
    # 기존 A2A 에이전트
    news_task = call_agent("news_agent", {"ticker": ticker})
    twitter_task = call_agent("twitter_agent", {"ticker": ticker})
    
    # MCP 에이전트 추가
    yahoo_task = call_agent("mcp_yahoo_finance_agent", {"ticker": ticker})
    alpha_task = call_agent("mcp_alpha_vantage_agent", {"ticker": ticker})
    
    # 병렬 실행
    results = await asyncio.gather(
        news_task, twitter_task, yahoo_task, alpha_task
    )
```

### 2. API 직접 호출
```bash
# Yahoo Finance MCP 에이전트 호출
curl -X POST http://localhost:8213/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# Alpha Vantage MCP 에이전트 호출
curl -X POST http://localhost:8214/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# 실시간 주가만 조회
curl -X POST http://localhost:8214/real_time_quote \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# 고급 기술적 분석
curl -X POST http://localhost:8214/advanced_analysis \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "indicators": ["RSI", "MACD", "BBANDS"]}'
```

## 장점

### 1. 표준화된 인터페이스
- MCP 프로토콜을 따르는 모든 서버와 호환
- 새로운 MCP 서버 추가가 용이

### 2. 확장성
- 외부 MCP 서버는 독립적으로 업데이트 가능
- A2A 시스템 수정 없이 새로운 데이터 소스 추가

### 3. 유연성
- 무료 데이터 (Yahoo Finance)와 유료 데이터 (Alpha Vantage) 혼용
- 사용자 요구에 따라 적절한 데이터 소스 선택

## 추가 가능한 MCP 서버

1. **Polygon.io MCP** - 고품질 실시간 시장 데이터
2. **Financial Datasets MCP** - 표준화된 재무제표
3. **SEC EDGAR MCP** - SEC 공시 데이터
4. **FRED MCP** - 경제 지표 데이터

## 주의사항

1. **API 키 관리**
   - Alpha Vantage는 무료 티어 제한 있음 (5 calls/min, 500 calls/day)
   - 프로덕션에서는 유료 플랜 고려

2. **에러 처리**
   - MCP 서버 다운 시 폴백 로직 구현
   - 네트워크 오류 처리

3. **캐싱**
   - 반복 요청 최소화를 위한 캐싱 구현 권장
   - Redis 등 활용

## 결론

A2A 시스템이 외부 MCP 서버를 호출하도록 수정함으로써:
- 기존 A2A의 강력한 오케스트레이션 능력 유지
- MCP 생태계의 다양한 데이터 소스 활용
- 두 프로토콜의 장점을 결합한 하이브리드 아키텍처 구현