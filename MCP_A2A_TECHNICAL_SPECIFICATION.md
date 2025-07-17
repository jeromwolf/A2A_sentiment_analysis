# MCP + A2A 하이브리드 아키텍처 기술 정의서

## 1. 개요 (Executive Summary)

### 1.1 목적
본 기술 정의서는 A2A(Agent-to-Agent) 프로토콜과 MCP(Model Context Protocol)를 결합한 하이브리드 투자 분석 시스템의 아키텍처를 정의합니다.

### 1.2 핵심 가치
- **A2A**: 멀티 에이전트 간 협업 및 오케스트레이션
- **MCP**: 외부 프리미엄 데이터 및 도구 접근
- **통합 효과**: 기관투자자급 분석을 개인투자자에게 제공

## 2. 아키텍처 정의

### 2.1 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 인터페이스                      │
│                    (WebSocket + REST API)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                   Main Orchestrator (A2A)                    │
│                        Port: 8100                            │
│              • 에이전트 라우팅 및 조정                       │
│              • 워크플로우 관리                               │
│              • 결과 통합                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                      │
┌───────┴────────┐                    ┌───────┴────────┐
│  A2A Agents    │                    │  MCP-Enhanced  │
│                │                    │    Agents      │
├────────────────┤                    ├────────────────┤
│ • NLU Agent    │                    │ • MCP Data     │
│ • News Agent   │                    │   Agent        │
│ • Twitter Agent│                    │ • MCP Quant    │
│ • SEC Agent    │                    │   Agent        │
│ • DART Agent   │                    │ • MCP Research │
│ • Sentiment    │                    │   Agent        │
│ • Risk Agent   │                    └────────┬───────┘
│ • Report Agent │                             │
└────────────────┘                             │
                                               │
                                    ┌──────────┴──────────┐
                                    │   MCP Servers       │
                                    ├─────────────────────┤
                                    │ • Bloomberg Term.   │
                                    │ • Refinitiv Eikon   │
                                    │ • FactSet           │
                                    │ • Alpha Vantage Pro │
                                    │ • Quandl            │
                                    └─────────────────────┘
```

### 2.2 통신 프로토콜 스택

```
┌─────────────────────────────────────┐
│         Application Layer           │
├─────────────────────────────────────┤
│   A2A Protocol  │   MCP Protocol    │
│   (Agents)      │   (Tools/Data)    │
├─────────────────────────────────────┤
│         JSON-RPC 2.0                │
├─────────────────────────────────────┤
│    HTTPS/WSS    │    HTTP/Stdio     │
├─────────────────────────────────────┤
│         TCP/IP Stack                │
└─────────────────────────────────────┘
```

## 3. A2A 프로토콜 정의

### 3.1 메시지 구조
```python
class A2AMessage:
    header: MessageHeader
    body: MessageBody
    metadata: MessageMetadata

class MessageHeader:
    message_id: str          # UUID
    message_type: MessageType  # REQUEST, RESPONSE, EVENT
    sender_id: str           # 발신 에이전트 ID
    recipient_id: str        # 수신 에이전트 ID
    timestamp: datetime
    version: str = "1.0"

class MessageBody:
    action: str              # 요청 액션
    payload: Dict[str, Any]  # 실제 데이터
    
class MessageMetadata:
    correlation_id: str      # 요청-응답 연결
    priority: int            # 0-10
    timeout: int             # 밀리초
    retry_policy: Dict
```

### 3.2 에이전트 등록 프로토콜
```json
{
  "agent_id": "mcp_data_agent_001",
  "agent_type": "data_collector",
  "capabilities": [
    {
      "name": "mcp_data_access",
      "version": "1.0",
      "mcp_servers": ["bloomberg", "refinitiv"],
      "data_types": ["analyst_reports", "real_time_quotes"]
    }
  ],
  "endpoint": "http://localhost:8215",
  "health_check": "/health",
  "metadata": {
    "mcp_enabled": true,
    "cache_ttl": 3600
  }
}
```

### 3.3 에이전트 간 통신 플로우
```
Agent A                    Registry                    Agent B
   │                          │                          │
   │─── Register ──────────>  │                          │
   │<── ACK ─────────────────  │                          │
   │                          │  <──── Register ─────────│
   │                          │  ───── ACK ────────────> │
   │                          │                          │
   │─── Discover(Agent B) ──> │                          │
   │<── Agent B Info ───────  │                          │
   │                          │                          │
   │─────────────── REQUEST ────────────────────────────>│
   │<────────────── RESPONSE ────────────────────────────│
```

## 4. MCP 프로토콜 정의

### 4.1 MCP 클라이언트 인터페이스
```python
class MCPClient:
    def __init__(self, server_url: str, auth_config: Dict):
        self.server_url = server_url
        self.auth = auth_config
        self.connection = None
    
    async def connect(self) -> bool:
        """MCP 서버 연결"""
        pass
    
    async def list_tools(self) -> List[Tool]:
        """사용 가능한 도구 목록"""
        pass
    
    async def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """도구 실행"""
        pass
    
    async def stream_data(self, subscription: Dict) -> AsyncIterator:
        """실시간 데이터 스트림"""
        pass
```

### 4.2 MCP 메시지 형식
```json
{
  "jsonrpc": "2.0",
  "method": "tools.execute",
  "params": {
    "tool": "get_analyst_reports",
    "arguments": {
      "ticker": "AAPL",
      "period": "3M",
      "min_rating": "Buy"
    }
  },
  "id": "req_12345"
}
```

### 4.3 MCP 서버 능력 정의
```yaml
bloomberg_mcp:
  capabilities:
    - real_time_quotes
    - historical_data
    - analyst_reports
    - economic_indicators
  rate_limits:
    requests_per_second: 100
    data_points_per_day: 1000000
  auth_method: api_key

refinitiv_mcp:
  capabilities:
    - market_data
    - news_analytics
    - company_fundamentals
    - esg_scores
  rate_limits:
    requests_per_minute: 500
    concurrent_connections: 10
  auth_method: oauth2
```

## 5. 하이브리드 에이전트 구현

### 5.1 MCP 강화 에이전트 구조
```python
class MCPEnhancedAgent(BaseAgent):
    def __init__(self, agent_config: Dict, mcp_config: Dict):
        super().__init__(**agent_config)
        
        # MCP 클라이언트 초기화
        self.mcp_clients = {}
        for server_name, server_config in mcp_config.items():
            self.mcp_clients[server_name] = MCPClient(
                server_url=server_config['url'],
                auth_config=server_config['auth']
            )
        
        # 캐시 설정
        self.cache = RedisCache(ttl=3600)
        
        # 비용 추적기
        self.cost_tracker = CostTracker(
            monthly_budget=mcp_config.get('monthly_budget', 1000)
        )
    
    async def process_with_mcp(self, request: Dict) -> Dict:
        """A2A 요청을 MCP 데이터로 강화"""
        # 1. 캐시 확인
        cached_data = await self.cache.get(request['ticker'])
        if cached_data:
            return cached_data
        
        # 2. MCP 데이터 수집
        mcp_results = {}
        for client_name, client in self.mcp_clients.items():
            if self.cost_tracker.can_use(client_name):
                try:
                    data = await client.execute_tool(
                        'get_market_data',
                        {'ticker': request['ticker']}
                    )
                    mcp_results[client_name] = data
                    self.cost_tracker.log_usage(client_name, data['cost'])
                except Exception as e:
                    logger.error(f"MCP {client_name} error: {e}")
        
        # 3. 결과 통합 및 캐싱
        integrated_result = self.integrate_data(
            a2a_data=request,
            mcp_data=mcp_results
        )
        await self.cache.set(request['ticker'], integrated_result)
        
        return integrated_result
```

### 5.2 스마트 라우팅 로직
```python
class SmartRouter:
    def __init__(self):
        self.routing_rules = {
            "basic_analysis": ["news", "twitter", "sec"],
            "professional_analysis": ["news", "twitter", "sec", "mcp_data"],
            "institutional_analysis": ["mcp_data", "mcp_quant", "mcp_research"],
            "real_time_trading": ["mcp_data", "quantitative"]
        }
    
    def determine_agents(self, user_request: Dict) -> List[str]:
        """사용자 요청 분석 후 필요한 에이전트 결정"""
        analysis_type = self._classify_request(user_request)
        
        # 비용 및 응답 시간 고려
        if user_request.get('premium', False):
            return self.routing_rules.get(analysis_type, [])
        else:
            # 무료 에이전트만 사용
            return [a for a in self.routing_rules.get(analysis_type, []) 
                   if not a.startswith('mcp_')]
```

## 6. 데이터 통합 및 스코어링

### 6.1 데이터 소스 가중치
```python
SOURCE_WEIGHTS = {
    # A2A 소스 (무료)
    "news": 1.0,
    "twitter": 0.7,
    "sec_filings": 1.5,
    "dart_filings": 1.5,
    
    # MCP 소스 (프리미엄)
    "analyst_reports": 2.0,
    "institutional_research": 2.2,
    "real_time_market_data": 1.8,
    "alternative_data": 1.6,
    "quant_signals": 1.9
}
```

### 6.2 통합 스코어 계산
```python
def calculate_integrated_score(data_sources: Dict[str, Any]) -> float:
    """
    여러 데이터 소스를 통합하여 최종 투자 스코어 계산
    Returns: -100 to +100
    """
    weighted_sum = 0
    total_weight = 0
    
    for source, data in data_sources.items():
        if source in SOURCE_WEIGHTS and 'sentiment_score' in data:
            weight = SOURCE_WEIGHTS[source]
            score = data['sentiment_score']
            confidence = data.get('confidence', 1.0)
            
            weighted_sum += score * weight * confidence
            total_weight += weight * confidence
    
    if total_weight > 0:
        return (weighted_sum / total_weight)
    return 0.0
```

## 7. 보안 및 인증

### 7.1 A2A 보안
```python
class A2ASecurity:
    def __init__(self):
        self.jwt_secret = os.environ['A2A_JWT_SECRET']
        self.agent_keys = {}  # 에이전트별 API 키
    
    def generate_agent_token(self, agent_id: str) -> str:
        """에이전트용 JWT 토큰 생성"""
        payload = {
            'agent_id': agent_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_agent_token(self, token: str) -> Dict:
        """에이전트 토큰 검증"""
        return jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
```

### 7.2 MCP 인증
```python
class MCPAuth:
    def __init__(self):
        self.auth_providers = {
            'bloomberg': BloombergAuth(),
            'refinitiv': OAuth2Auth(),
            'factset': APIKeyAuth()
        }
    
    async def authenticate(self, server: str) -> Dict:
        """MCP 서버별 인증"""
        provider = self.auth_providers.get(server)
        if provider:
            return await provider.get_credentials()
        raise ValueError(f"Unknown MCP server: {server}")
```

## 8. 성능 최적화

### 8.1 캐싱 전략
```yaml
cache_strategy:
  layers:
    - name: memory_cache
      ttl: 300  # 5분
      max_size: 1000
    
    - name: redis_cache
      ttl: 3600  # 1시간
      max_size: 10000
      
    - name: persistent_cache
      ttl: 86400  # 24시간
      storage: postgresql
      
  invalidation_rules:
    - event: market_close
      invalidate: ['real_time_quotes', 'intraday_data']
    - event: earnings_release
      invalidate: ['analyst_reports', 'estimates']
```

### 8.2 병렬 처리
```python
class ParallelProcessor:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_agents_parallel(self, agents: List[str], request: Dict):
        """에이전트 병렬 실행"""
        async with self.semaphore:
            tasks = []
            for agent in agents:
                task = self.call_agent(agent, request)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return self.merge_results(results)
```

## 9. 모니터링 및 관측성

### 9.1 메트릭 정의
```python
# Prometheus 메트릭
METRICS = {
    # A2A 메트릭
    'a2a_request_total': Counter('a2a_request_total', 'Total A2A requests', ['agent', 'action']),
    'a2a_request_duration': Histogram('a2a_request_duration_seconds', 'A2A request duration'),
    'a2a_active_agents': Gauge('a2a_active_agents', 'Number of active agents'),
    
    # MCP 메트릭  
    'mcp_api_calls': Counter('mcp_api_calls_total', 'Total MCP API calls', ['server', 'endpoint']),
    'mcp_api_cost': Counter('mcp_api_cost_dollars', 'MCP API cost', ['server']),
    'mcp_cache_hit_rate': Gauge('mcp_cache_hit_rate', 'Cache hit rate'),
    
    # 비즈니스 메트릭
    'analysis_completed': Counter('analysis_completed_total', 'Completed analyses', ['type']),
    'analysis_quality_score': Histogram('analysis_quality_score', 'Quality score distribution')
}
```

### 9.2 로깅 표준
```python
import structlog

logger = structlog.get_logger()

# 구조화된 로깅
logger.info(
    "analysis_completed",
    user_id=user_id,
    ticker=ticker,
    agents_used=["news", "mcp_data"],
    mcp_cost=0.75,
    duration_ms=1234,
    cache_hits=3,
    quality_score=0.92
)
```

## 10. 배포 아키텍처

### 10.1 컨테이너 구성
```yaml
version: '3.8'

services:
  # A2A 인프라
  registry:
    image: a2a/registry:latest
    ports:
      - "8001:8001"
    environment:
      - DB_URL=postgresql://localhost/a2a_registry
  
  orchestrator:
    image: a2a/orchestrator:latest
    ports:
      - "8100:8100"
    depends_on:
      - registry
      - redis
  
  # MCP 강화 에이전트
  mcp_data_agent:
    image: a2a/mcp-data-agent:latest
    ports:
      - "8215:8215"
    environment:
      - MCP_BLOOMBERG_KEY=${MCP_BLOOMBERG_KEY}
      - MCP_REFINITIV_KEY=${MCP_REFINITIV_KEY}
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./mcp_cache:/app/cache
  
  # 캐시 및 큐
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy lru
    
  # 모니터링
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### 10.2 확장성 고려사항
```yaml
scaling_strategy:
  horizontal:
    - component: mcp_agents
      min_replicas: 2
      max_replicas: 10
      scale_metric: cpu_usage > 70%
      
  vertical:
    - component: orchestrator
      cpu_request: 2
      cpu_limit: 4
      memory_request: 4Gi
      memory_limit: 8Gi
      
  cache_scaling:
    redis_cluster:
      nodes: 6
      replicas: 1
      sharding: consistent_hash
```

## 11. 장애 처리 및 복구

### 11.1 서킷 브레이커
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
```

### 11.2 폴백 전략
```python
class FallbackStrategy:
    def __init__(self):
        self.fallback_chains = {
            "market_data": [
                ("mcp_bloomberg", self.get_bloomberg_data),
                ("mcp_refinitiv", self.get_refinitiv_data),
                ("free_yahoo", self.get_yahoo_data),
                ("cached_data", self.get_cached_data)
            ]
        }
    
    async def get_data_with_fallback(self, data_type: str, params: Dict):
        """폴백 체인을 따라 데이터 획득 시도"""
        for source, method in self.fallback_chains[data_type]:
            try:
                return await method(params)
            except Exception as e:
                logger.warning(f"Fallback: {source} failed", error=str(e))
                continue
        
        raise AllSourcesFailedError(f"All sources failed for {data_type}")
```

## 12. 테스트 전략

### 12.1 통합 테스트
```python
class IntegrationTest:
    async def test_full_analysis_flow(self):
        """전체 분석 플로우 테스트"""
        # 1. 오케스트레이터 시작
        orchestrator = await start_orchestrator()
        
        # 2. 에이전트 등록 확인
        agents = await orchestrator.list_agents()
        assert len(agents) >= 5
        
        # 3. 분석 요청
        result = await orchestrator.analyze({
            "query": "AAPL 전문 분석 요청",
            "include_premium": True
        })
        
        # 4. 결과 검증
        assert result['status'] == 'completed'
        assert 'mcp_data' in result['sources']
        assert result['quality_score'] > 0.8
```

### 12.2 부하 테스트
```yaml
load_test_scenarios:
  - name: peak_hours
    duration: 30m
    users: 1000
    requests_per_second: 100
    endpoints:
      - /analyze (70%)
      - /real_time_quote (20%)
      - /report (10%)
    
  - name: mcp_stress
    duration: 10m
    concurrent_mcp_calls: 500
    cache_hit_ratio_target: 0.8
    cost_budget_limit: 100
```

## 13. 버전 관리 및 마이그레이션

### 13.1 API 버전 관리
```python
API_VERSIONS = {
    "v1": {
        "deprecated": False,
        "sunset_date": None,
        "features": ["basic_analysis", "news", "twitter"]
    },
    "v2": {
        "deprecated": False,
        "sunset_date": None,
        "features": ["v1_features", "mcp_integration", "real_time_data"]
    }
}
```

### 13.2 마이그레이션 전략
```python
class MigrationManager:
    async def migrate_to_mcp_enhanced(self):
        """기존 에이전트를 MCP 강화 버전으로 마이그레이션"""
        # 1. 새 에이전트 배포
        await self.deploy_new_agents()
        
        # 2. 트래픽 점진적 이동 (카나리 배포)
        for percentage in [10, 25, 50, 75, 100]:
            await self.route_traffic_percentage(percentage)
            await self.monitor_health(duration=300)  # 5분 모니터링
            
            if not self.is_healthy():
                await self.rollback()
                break
        
        # 3. 구 버전 제거
        if self.migration_successful():
            await self.cleanup_old_version()
```

## 14. 비용 관리

### 14.1 비용 추적 시스템
```python
class CostManagement:
    def __init__(self, config: Dict):
        self.monthly_budget = config['monthly_budget']
        self.alert_threshold = config['alert_threshold']
        self.cost_per_api = {
            'bloomberg_real_time': 0.10,
            'bloomberg_historical': 0.05,
            'refinitiv_news': 0.02,
            'analyst_reports': 0.50
        }
    
    async def track_api_usage(self, api_name: str, count: int):
        cost = self.cost_per_api.get(api_name, 0) * count
        await self.record_cost(api_name, cost)
        
        if await self.get_monthly_total() > self.alert_threshold:
            await self.send_cost_alert()
```

### 14.2 비용 최적화
```yaml
cost_optimization:
  strategies:
    - name: intelligent_caching
      cache_expensive_apis: true
      cache_duration:
        analyst_reports: 86400  # 24시간
        real_time_quotes: 60    # 1분
        
    - name: request_batching
      batch_window: 100ms
      max_batch_size: 50
      
    - name: tiered_service
      free_tier:
        - news_agent
        - twitter_agent
        - basic_analysis
      premium_tier:
        - mcp_data
        - institutional_research
        - real_time_trading
```

## 15. 결론

본 기술 정의서는 A2A와 MCP를 결합한 하이브리드 투자 분석 시스템의 완전한 아키텍처를 정의합니다. 

### 핵심 성과 지표 (KPI)
- **분석 품질**: 기관투자자 리포트 대비 90% 이상 품질
- **응답 시간**: 95%ile < 3초
- **비용 효율성**: 사용자당 월 $10 미만
- **가용성**: 99.9% 이상
- **확장성**: 초당 1,000건 이상 처리

### 로드맵
1. **Phase 1** (1개월): 기본 MCP 통합
2. **Phase 2** (2개월): 프리미엄 데이터 소스 연동
3. **Phase 3** (3개월): 고급 분석 기능 구현
4. **Phase 4** (6개월): 글로벌 확장 및 다국어 지원

이 아키텍처를 통해 개인 투자자에게 기관급 투자 분석 서비스를 제공하는 혁신적인 플랫폼을 구축할 수 있습니다.