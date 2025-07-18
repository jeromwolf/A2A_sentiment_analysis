# MCP와 A2A 통합 아키텍처 구현 계획

## 개요
A2A(Agent-to-Agent)의 강력한 에이전트 협업 체계와 MCP(Model Context Protocol)의 외부 도구 접근 능력을 결합하여, 
무료와 프리미엄 데이터를 균형있게 활용하는 전문 투자 분석 플랫폼 구축

## 핵심 차이점

### MCP (Model Context Protocol)
- **범위**: 단일 Agent의 모델 + 도구
- **강점**: 컨텍스트 강화, 도구 통합
- **상호작용**: 모델 ↔ 도구
- **통합 방향**: 수직적 통합 (애플리케이션-모델)
- **통신 방식**: JSON-RPC 2.0 기반, HTTP (Stdio, SSE)
- **메시지 형식**: JSON 컨텍스트 제공
- **보안**: 대화 세션 수준 액세스 제어
- **활용 예시**: 모델에 DB 쿼리 전송, 외부 도구 활용

### A2A (Agent-to-Agent)
- **범위**: Multi Agents 간 통신
- **강점**: 에이전트 간 통신 및 협업
- **상호작용**: 에이전트 ↔ 에이전트
- **통합 방향**: 수평적 통합 (에이전트-에이전트)
- **통신 방식**: JSON-RPC 2.0 기반, HTTPS (TLS)
- **메시지 형식**: 에이전트 간 메시지 표준화
- **보안**: OAuth / OpenAPI 인증
- **활용 예시**: 연구 에이전트와 코딩 에이전트 간 협업

## 현재 시스템 분석

### 기존 A2A 아키텍처
- **Main Orchestrator** (포트 8100): WebSocket 기반 중앙 조정
- **데이터 수집 에이전트**: News(8307), Twitter(8209), SEC(8210), DART(8213)
- **분석 에이전트**: Sentiment(8202), Quantitative(8211), Risk(8212)
- **결과 처리**: Score Calculation(8203), Report Generation(8204)

### MCP Data Agent 현황
- **포트**: 8215
- **현재 상태**: 구현 완료, 오케스트레이터 미통합
- **제공 데이터**:
  - 애널리스트 리포트
  - 브로커 추천
  - 내부자 거래 정보

## 구현 로드맵

### Phase 1: 즉시 통합 (1일)
#### 1.1 오케스트레이터 수정
```python
# main_orchestrator_v2.py의 _start_data_collection 메서드
agent_ports = {
    "news": 8307,
    "twitter": 8209,
    "sec": 8210,  # 또는 "dart": 8213 (한국 기업)
    "mcp": 8215   # MCP 에이전트 추가
}
```

#### 1.2 가중치 시스템 업데이트
```python
# score_calculation_agent_v2.py
SOURCE_WEIGHTS = {
    "기업 공시": 1.5,
    "뉴스": 1.0,
    "트위터": 0.7,
    # 프리미엄 데이터 추가
    "애널리스트 리포트": 2.0,  # 최고 신뢰도
    "브로커 추천": 1.8,
    "내부자 거래": 1.6
}
```

### Phase 2: MCP 클라이언트 통합 (3-5일)
#### 2.1 의존성 설치
```bash
pip install mcp-client
# 또는 
pip install anthropic-mcp
```

#### 2.2 실제 MCP 연동 구현
```python
# agents/mcp_data_agent.py
from mcp import Client
import asyncio

class MCPDataAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.mcp_clients = {
            "bloomberg": Client("mcp://bloomberg-terminal"),
            "refinitiv": Client("mcp://refinitiv-eikon"),
            "yahoo_finance": Client("mcp://yahoo-finance-plus"),
            "alphavantage": Client("mcp://alphavantage-premium")
        }
    
    async def fetch_premium_data(self, ticker: str):
        tasks = []
        for name, client in self.mcp_clients.items():
            if client.is_available():
                tasks.append(self._fetch_from_source(name, client, ticker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._merge_results(results)
```

### Phase 3: 지능형 라우팅 (1주일)
#### 3.1 요청 분석기 구현
```python
class RequestAnalyzer:
    def analyze_data_needs(self, user_query: str) -> Dict[str, bool]:
        needs = {
            "basic_data": True,  # 항상 기본 데이터 수집
            "premium_data": False
        }
        
        # 프리미엄 데이터 필요 조건
        premium_keywords = ["전문 분석", "애널리스트", "기관", "내부자", "상세 분석"]
        if any(keyword in user_query for keyword in premium_keywords):
            needs["premium_data"] = True
        
        return needs
```

#### 3.2 비용 최적화 라우팅
```python
async def smart_routing(self, ticker: str, analysis_needs: Dict):
    agents_to_call = ["news", "twitter", "sec"]  # 기본 에이전트
    
    if analysis_needs["premium_data"] and self.budget_available():
        agents_to_call.append("mcp")
    
    return await self._call_agents(agents_to_call, ticker)
```

### Phase 4: 캐싱 및 비용 관리 (2-3일)
#### 4.1 Redis 캐시 구현
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_premium_data(ttl=3600):  # 1시간 기본 캐시
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ticker, *args, **kwargs):
            cache_key = f"mcp:{ticker}:{func.__name__}"
            
            # 캐시 확인
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 실제 API 호출
            result = await func(self, ticker, *args, **kwargs)
            
            # 캐시 저장
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 4.2 비용 추적 시스템
```python
class CostTracker:
    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.current_usage = 0.0
        self.usage_log = []
    
    def can_use_premium(self, estimated_cost: float) -> bool:
        return (self.current_usage + estimated_cost) <= self.monthly_budget
    
    def log_usage(self, service: str, cost: float):
        self.current_usage += cost
        self.usage_log.append({
            "timestamp": datetime.now(),
            "service": service,
            "cost": cost
        })
```

### Phase 5: UI/UX 개선 (1-2일)
#### 5.1 프리미엄 데이터 표시
```javascript
// index_v2.html에 추가
function displayPremiumData(data) {
    if (data.analyst_reports) {
        $('#premium-section').show();
        $('#analyst-reports').html(formatAnalystReports(data.analyst_reports));
    }
}

function showDataSourceBadges(sources) {
    sources.forEach(source => {
        const badge = source.is_premium 
            ? '<span class="badge badge-premium">프리미엄</span>'
            : '<span class="badge badge-free">무료</span>';
        $('.data-sources').append(badge);
    });
}
```

#### 5.2 비용 대시보드
```html
<div id="cost-dashboard" class="mt-3">
    <h5>프리미엄 데이터 사용량</h5>
    <div class="progress">
        <div class="progress-bar" role="progressbar" style="width: 25%">
            월 예산의 25% 사용
        </div>
    </div>
    <small>남은 예산: $750 / $1000</small>
</div>
```

## 환경 설정

### .env 파일 업데이트
```env
# 기존 설정
GEMINI_API_KEY=your-gemini-key
FINNHUB_API_KEY=your-finnhub-key
TWITTER_BEARER_TOKEN=your-twitter-token

# MCP 설정 추가
MCP_BLOOMBERG_URL=mcp://bloomberg.com/terminal
MCP_BLOOMBERG_KEY=your-bloomberg-key
MCP_REFINITIV_URL=mcp://refinitiv.com/eikon
MCP_REFINITIV_KEY=your-refinitiv-key
MCP_YAHOO_FINANCE_KEY=your-yahoo-key
MCP_ALPHAVANTAGE_KEY=your-alpha-key

# 비용 관리
MCP_MONTHLY_BUDGET=1000  # USD
MCP_CACHE_TTL=3600      # 초 단위
MCP_RATE_LIMIT=100      # 시간당 요청 수

# Redis 캐시
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 테스트 계획

### 단위 테스트
```python
# tests/test_mcp_integration.py
async def test_mcp_agent_connection():
    agent = MCPDataAgent()
    assert agent.health_check() == "healthy"

async def test_premium_data_fetch():
    agent = MCPDataAgent()
    data = await agent.fetch_analyst_reports("AAPL")
    assert "ratings" in data
    assert "target_price" in data

async def test_cost_tracking():
    tracker = CostTracker(monthly_budget=1000)
    assert tracker.can_use_premium(50) == True
    tracker.log_usage("bloomberg", 50)
    assert tracker.current_usage == 50
```

### 통합 테스트
```bash
# 전체 시스템 테스트
./start_v2_complete.sh

# MCP 통합 확인
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "애플 주식 전문 애널리스트 의견 포함해서 분석해줘"}'

# 캐시 동작 확인 (동일 요청 반복)
time curl -X POST http://localhost:8215/collect_mcp_data \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## 모니터링 및 운영

### 로깅 구성
```python
import logging
from pythonjsonlogger import jsonlogger

# JSON 형식 로깅
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger("mcp_agent")
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# 사용 예
logger.info("MCP data fetched", extra={
    "ticker": ticker,
    "source": "bloomberg",
    "cost": 0.50,
    "cache_hit": False
})
```

### 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge

# Prometheus 메트릭
mcp_requests_total = Counter('mcp_requests_total', 'Total MCP requests', ['source'])
mcp_request_duration = Histogram('mcp_request_duration_seconds', 'MCP request duration')
mcp_budget_remaining = Gauge('mcp_budget_remaining_dollars', 'Remaining monthly budget')

# 사용 예
with mcp_request_duration.time():
    data = await fetch_from_bloomberg(ticker)
mcp_requests_total.labels(source='bloomberg').inc()
```

## 예상 효과

### 장점
1. **데이터 품질 향상**: 프리미엄 애널리스트 리포트로 분석 정확도 증가
2. **비용 효율성**: 스마트 라우팅과 캐싱으로 불필요한 API 호출 최소화
3. **확장성**: 표준 MCP 프로토콜로 새로운 데이터 소스 쉽게 추가
4. **사용자 만족도**: 무료/프리미엄 옵션 제공으로 다양한 니즈 충족

### 주의사항
1. **API 비용 관리**: 월별 예산 모니터링 필수
2. **레이트 리밋**: 각 서비스별 제한 준수
3. **데이터 라이선스**: 프리미엄 데이터 재배포 제한 확인
4. **장애 대응**: MCP 서버 다운시 기본 데이터만으로 서비스 지속

## 결론
A2A의 강력한 에이전트 협업 체계를 유지하면서 MCP를 통한 외부 프리미엄 데이터 접근을 추가함으로써, 무료 서비스의 접근성과 프리미엄 서비스의 전문성을 모두 제공하는 하이브리드 투자 분석 플랫폼 구현 가능