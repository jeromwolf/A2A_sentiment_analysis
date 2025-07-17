# MCP 호환 금융 데이터 API 가격 가이드

## Phase 1: 무료 API (현재 구현 가능)

### 1. **Yahoo Finance (yfinance)**
- **가격**: 완전 무료
- **MCP 기능**: 
  - 실시간 주가 (15분 지연)
  - 과거 가격 데이터
  - 기본 재무제표
  - 뉴스 헤드라인
- **제한**: 비공식 API, 속도 제한
- **용도**: 프로토타입, 개인 프로젝트

### 2. **Alpha Vantage**
- **가격**: 무료 (5 API calls/분, 500 calls/일)
- **MCP 기능**:
  - 실시간 및 과거 주가
  - 기술적 지표 (RSI, MACD 등)
  - 기본적 재무 데이터
  - 섹터 퍼포먼스
- **프리미엄**: $49.99/월 (75 calls/분)
- **용도**: 소규모 서비스

### 3. **Finnhub**
- **가격**: 무료 (60 API calls/분)
- **MCP 기능**:
  - 실시간 주가
  - 회사 뉴스
  - 기본 재무제표
  - 애널리스트 추천 (제한적)
- **프리미엄**: $79.99/월부터
- **용도**: 뉴스 중심 분석

### 4. **IEX Cloud**
- **가격**: 무료 (50,000 messages/월)
- **MCP 기능**:
  - 실시간 주가
  - 과거 데이터
  - 기업 정보
  - 뉴스 피드
- **용도**: 미국 주식 전용

## Phase 2: 중급 API ($100-500/월)

### 1. **Polygon.io**
- **가격**: 
  - Starter: $29.99/월
  - Developer: $99.99/월
  - Professional: $399.99/월
- **MCP 기능**:
  - 실시간 웹소켓 스트리밍
  - 모든 미국 거래소 데이터
  - 옵션/선물 데이터
  - 뉴스 & 감성 분석
  - 기술적 지표
- **API 제한**: 
  - Starter: 100,000 calls/일
  - Professional: 무제한
- **장점**: 가성비 최고, 안정적

### 2. **Twelve Data**
- **가격**:
  - Basic: $19/월 (800 calls/일)
  - Pro: $59/월 (15,000 calls/일)
  - Expert: $159/월 (120,000 calls/일)
- **MCP 기능**:
  - 실시간 & 과거 데이터
  - 120+ 기술적 지표
  - 웹소켓 스트리밍
  - 글로벌 거래소 지원
- **장점**: 한국 주식 지원

### 3. **Tiingo**
- **가격**:
  - Power: $30/월
  - Commercial: $299/월
- **MCP 기능**:
  - End-of-day 가격
  - IEX 실시간 데이터
  - 뉴스 API
  - 기본적 분석 데이터
- **장점**: 깔끔한 API

### 4. **Quandl (Nasdaq Data Link)**
- **가격**: $99-499/월 (데이터셋별)
- **MCP 기능**:
  - 대안 데이터 (Alternative Data)
  - 매크로 경제 지표
  - 상품/원자재 데이터
  - 펀더멘털 데이터
- **장점**: 독특한 데이터셋

### 5. **Benzinga**
- **가격**: 
  - Starter: $177/월
  - Pro: $377/월
- **MCP 기능**:
  - 실시간 뉴스 피드
  - 애널리스트 등급 변경
  - 기업 이벤트 캘린더
  - 감성 분석 점수
- **장점**: 뉴스 전문

## Phase 3: 프리미엄 API (투자 후)

### 1. **Bloomberg Terminal/API**
- **가격**: $2,000-2,500/월 (터미널당)
- **MCP 기능**:
  - 모든 금융 데이터
  - 실시간 뉴스 & 리서치
  - 애널리스트 리포트 전문
  - 채권/파생상품 데이터
  - Bloomberg 채팅
- **API**: B-PIPE, DAPI 별도 협상
- **장점**: 업계 표준, 최고 품질

### 2. **Refinitiv Eikon/Workspace**
- **가격**: $1,800-2,200/월
- **MCP 기능**:
  - 실시간 시장 데이터
  - 뉴스 & 리서치
  - 펀더멘털 데이터
  - ESG 데이터
  - 애널리스트 예측
- **API**: Refinitiv Data Platform
- **장점**: Thomson Reuters 뉴스

### 3. **FactSet**
- **가격**: $2,000-3,000/월
- **MCP 기능**:
  - 통합 금융 데이터
  - 퀀트 분석 도구
  - 포트폴리오 분석
  - 리스크 관리
  - 맞춤형 리포트
- **장점**: 기관 투자자 선호

### 4. **S&P Capital IQ**
- **가격**: $2,500-3,500/월
- **MCP 기능**:
  - 기업 정보 & M&A 데이터
  - 신용 등급
  - 산업 분석
  - 프라이빗 마켓 데이터
- **장점**: 기업 분석 특화

## 실제 구현 예시

### Phase 1 구현 (현재)
```python
# mcp_data_agent.py
class MCPDataAgent:
    def __init__(self):
        self.free_sources = {
            "yahoo": YahooFinanceClient(),      # 무료
            "alphavantage": AlphaVantageClient(), # 무료 티어
            "finnhub": FinnhubClient()           # 무료 티어
        }
```

### Phase 2 구현 (3-6개월)
```python
# 중급 API 추가
self.premium_sources = {
    "polygon": PolygonClient(),      # $99.99/월
    "twelvedata": TwelveDataClient(), # $59/월
    "benzinga": BenzingaClient()     # $177/월
}
# 월 비용: 약 $350
```

### Phase 3 구현 (투자 유치 후)
```python
# 엔터프라이즈 API
self.enterprise_sources = {
    "bloomberg": BloombergClient(),   # $2,500/월
    "refinitiv": RefinitivClient(),   # $2,000/월
    "factset": FactSetClient()        # $2,500/월
}
# 월 비용: 약 $7,000
```

## 비용 최적화 전략

### 1. **계층적 접근**
```python
def get_data(ticker, user_tier):
    if user_tier == "free":
        return self.free_sources.get_data(ticker)
    elif user_tier == "premium":
        return self.premium_sources.get_data(ticker)
    else:  # enterprise
        return self.enterprise_sources.get_data(ticker)
```

### 2. **캐싱 전략**
```python
# 비싼 API일수록 긴 캐시
cache_ttl = {
    "yahoo": 300,      # 5분
    "polygon": 3600,   # 1시간
    "bloomberg": 86400 # 24시간
}
```

### 3. **스마트 라우팅**
```python
# 데이터 종류에 따라 최적 소스 선택
routing_rules = {
    "real_time_quote": "polygon",     # 빠르고 저렴
    "news": "benzinga",               # 뉴스 전문
    "fundamentals": "alphavantage",   # 무료로 충분
    "analyst_report": "bloomberg"     # 프리미엄 필수
}
```

## 발표 시 메시지

"현재는 Phase 1의 무료 API로 프로토타입을 구현했습니다.
시스템은 Phase 3의 Bloomberg까지 즉시 연동 가능하도록 설계되어 있어,
투자 유치 후 API 키만 입력하면 바로 업그레이드됩니다.

단계적 접근으로 초기 비용을 최소화하면서도
미래 확장성을 확보했습니다."