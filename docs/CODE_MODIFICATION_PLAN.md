# 코드 수정 계획 및 일정

## 📅 전체 일정 (7/17 - 7/24)

### D-7 ~ D-5 (7/17-7/19): 1차 주석 및 MCP 통합
### D-4 ~ D-2 (7/20-7/22): 데모 준비 및 테스트
### D-1 (7/23): 최종 점검
### D-Day (7/24): 발표

## 1차 수정: MCP 에이전트 활성화 (7/17-7/18)

### 1.1 main_orchestrator_v2.py 수정
```python
# 파일: main_orchestrator_v2.py
# 위치: 라인 200-220 근처 (_start_data_collection 메서드)
# 작업 시간: 30분

# 현재 코드
if is_korean:
    agent_ports = {
        "news": 8307,
        "twitter": 8209,
        "dart": 8213
    }
else:
    agent_ports = {
        "news": 8307,
        "twitter": 8209,
        "sec": 8210
    }

# 수정 후
if is_korean:
    agent_ports = {
        "news": 8307,
        "twitter": 8209,
        "dart": 8213,
        "mcp": 8215  # MCP 에이전트 추가
    }
else:
    agent_ports = {
        "news": 8307,
        "twitter": 8209,
        "sec": 8210,
        "mcp": 8215  # MCP 에이전트 추가
    }

# 추가로 대기 에이전트 리스트에도 포함
self.waiting_agents = list(agent_ports.keys())
```

### 1.2 start_v2_complete.sh 수정
```bash
# 파일: start_v2_complete.sh
# 위치: 에이전트 시작 부분
# 작업 시간: 10분

# MCP 에이전트 시작 추가
echo "Starting MCP Data Agent..."
uvicorn agents.mcp_data_agent:app --port 8215 --reload > logs/mcp_agent.log 2>&1 &
echo "MCP Data Agent started on port 8215"
sleep 2
```

### 1.3 agents/mcp_data_agent.py 개선
```python
# 파일: agents/mcp_data_agent.py
# 작업 시간: 2시간

# 1. 실제 무료 API 연동 추가 (라인 140-200)
import yfinance as yf
import requests
from datetime import datetime, timedelta

async def _fetch_analyst_reports(self, ticker: str) -> Dict[str, Any]:
    """실제 데이터 + 시뮬레이션 혼합"""
    try:
        # Yahoo Finance에서 기본 추천 정보 가져오기
        stock = yf.Ticker(ticker)
        info = stock.info
        
        recommendations = {
            "current_rating": info.get('recommendationMean', 3.0),
            "recommendation_key": info.get('recommendationKey', 'hold'),
            "number_of_analysts": info.get('numberOfAnalystOpinions', 0)
        }
        
        # 시뮬레이션 데이터로 보강
        enhanced_data = {
            "real_data": recommendations,
            "simulated_reports": [
                {
                    "analyst": "AI Fund Analytics",
                    "rating": self._convert_rating(recommendations['recommendation_key']),
                    "target_price": info.get('targetMeanPrice', 0),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": f"Based on {recommendations['number_of_analysts']} analysts"
                }
            ],
            "consensus_rating": recommendations['recommendation_key'],
            "data_source": "Yahoo Finance (Free) + Simulation"
        }
        
        return enhanced_data
        
    except Exception as e:
        logger.warning(f"Yahoo Finance 오류, 시뮬레이션 데이터 사용: {e}")
        # 기존 시뮬레이션 데이터 반환
        return self._get_simulation_data(ticker)

# 2. Alpha Vantage 연동 추가
async def _fetch_market_sentiment(self, ticker: str) -> Dict[str, Any]:
    """Alpha Vantage 뉴스 감성 분석"""
    api_key = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
    url = f"https://www.alphavantage.co/query"
    
    params = {
        'function': 'NEWS_SENTIMENT',
        'tickers': ticker,
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if 'feed' in data:
            # 실제 뉴스 감성 분석
            sentiment_scores = []
            for article in data['feed'][:5]:
                if 'overall_sentiment_score' in article:
                    sentiment_scores.append(article['overall_sentiment_score'])
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                "sentiment_score": avg_sentiment,
                "articles_analyzed": len(sentiment_scores),
                "data_source": "Alpha Vantage",
                "is_real_data": True
            }
    except Exception as e:
        logger.warning(f"Alpha Vantage 오류: {e}")
    
    # 폴백: 시뮬레이션 데이터
    return {
        "sentiment_score": 0.65,
        "articles_analyzed": 0,
        "data_source": "Simulation",
        "is_real_data": False
    }
```

## 2차 수정: UI 및 데이터 표시 개선 (7/19)

### 2.1 index_v2.html 수정
```javascript
// 파일: index_v2.html
// 위치: displayDataCollection 함수 (라인 300-400)
// 작업 시간: 1시간

// MCP 데이터 특별 표시 추가
if (data.source === 'mcp') {
    $('#data-collection').append(`
        <div class="alert alert-info">
            <h5><i class="fas fa-star"></i> 프리미엄 데이터 (MCP)</h5>
            <div class="row">
                <div class="col-md-4">
                    <strong>애널리스트 리포트</strong>
                    <p>평균 목표가: $${data.analyst_reports.target_price}</p>
                    <p>추천 등급: ${data.analyst_reports.consensus_rating}</p>
                </div>
                <div class="col-md-4">
                    <strong>브로커 추천</strong>
                    <p>Buy: ${data.broker_recommendations.buy}명</p>
                    <p>Hold: ${data.broker_recommendations.hold}명</p>
                </div>
                <div class="col-md-4">
                    <strong>데이터 소스</strong>
                    <span class="badge badge-warning">
                        ${data.data_source || 'Simulation'}
                    </span>
                </div>
            </div>
        </div>
    `);
}

// 진행 상태에 MCP 추가
function updateProgress(agent, status) {
    const agentNames = {
        'news': '뉴스',
        'twitter': '트위터', 
        'sec': 'SEC',
        'dart': 'DART',
        'mcp': 'MCP 프리미엄'  // 추가
    };
}
```

### 2.2 agents/score_calculation_agent_v2.py 수정
```python
# 파일: agents/score_calculation_agent_v2.py
# 위치: 라인 50-70 (SOURCE_WEIGHTS)
# 작업 시간: 30분

# 현재 가중치
SOURCE_WEIGHTS = {
    "기업 공시": 1.5,
    "뉴스": 1.0,
    "트위터": 0.7
}

# MCP 가중치 추가
SOURCE_WEIGHTS = {
    "기업 공시": 1.5,
    "뉴스": 1.0,
    "트위터": 0.7,
    "MCP 애널리스트": 2.0,  # 최고 가중치
    "MCP 브로커": 1.8,
    "MCP 감성": 1.6
}

# calculate_weighted_score 메서드 수정
async def calculate_weighted_score(self, data_collection):
    # MCP 데이터 처리 추가
    if 'mcp' in data_collection:
        mcp_data = data_collection['mcp'].get('data', {})
        
        if 'analyst_reports' in mcp_data:
            # 애널리스트 평점을 감성 점수로 변환
            rating = mcp_data['analyst_reports'].get('current_rating', 3)
            sentiment_score = (rating - 3) * 25  # 1-5 스케일을 -50~50으로 변환
            
            scores['MCP 애널리스트'] = {
                'score': sentiment_score,
                'confidence': 0.9
            }
```

## 3차 수정: 한글 처리 및 번역 (7/20)

### 3.1 agents/mcp_data_agent.py 한글 지원
```python
# 파일: agents/mcp_data_agent.py
# 위치: 각 데이터 수집 메서드
# 작업 시간: 1시간

# 한국 주식 처리 추가
def _is_korean_stock(self, ticker: str) -> bool:
    return ticker.endswith('.KS') or ticker.endswith('.KQ')

async def _fetch_analyst_reports(self, ticker: str) -> Dict[str, Any]:
    if self._is_korean_stock(ticker):
        # 한국 주식용 데이터
        return {
            "reports": [
                {
                    "analyst": "미래에셋증권",
                    "rating": "매수",
                    "target_price": 85000,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": "반도체 업황 개선 기대"
                },
                {
                    "analyst": "NH투자증권",
                    "rating": "보유",
                    "target_price": 80000,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": "단기 실적 압박 우려"
                }
            ],
            "consensus_rating": "매수",
            "average_target": 82500,
            "currency": "KRW"
        }
```

### 3.2 utils/translation_manager.py 수정
```python
# 파일: utils/translation_manager.py
# 위치: 번역 사전 추가
# 작업 시간: 30분

# MCP 관련 용어 추가
FINANCIAL_TERMS.update({
    "analyst report": "애널리스트 리포트",
    "broker recommendation": "브로커 추천",
    "insider sentiment": "내부자 심리",
    "institutional flow": "기관 자금 흐름",
    "target price": "목표 주가",
    "consensus rating": "컨센서스 등급",
    "buy": "매수",
    "sell": "매도",
    "hold": "보유",
    "strong buy": "적극 매수",
    "strong sell": "적극 매도"
})
```

## 4차 수정: 에러 처리 및 안정성 (7/21)

### 4.1 전체 에이전트 타임아웃 설정
```python
# 각 에이전트 파일에 추가
# 작업 시간: 2시간 (모든 에이전트)

class SomeAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.timeout = 30  # 30초 타임아웃
        self.max_retries = 3
        
    async def safe_request(self, func, *args, **kwargs):
        """안전한 요청 처리"""
        for attempt in range(self.max_retries):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"타임아웃 발생 (시도 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"오류 발생: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 지수 백오프
```

### 4.2 데모 모드 추가
```python
# 파일: main_orchestrator_v2.py
# 위치: 환경 변수 확인 부분
# 작업 시간: 1시간

DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

if DEMO_MODE:
    # 데모 모드에서는 캐시된 데이터 우선 사용
    logger.info("데모 모드 활성화: 캐시 데이터 사용")
    
    # 타임아웃 단축
    DEFAULT_TIMEOUT = 10  # 10초
    
    # 에러 시 폴백 데이터 사용
    USE_FALLBACK_DATA = True
```

## 5차 수정: 발표용 최적화 (7/22)

### 5.1 로딩 메시지 개선
```javascript
// 파일: index_v2.html
// 작업 시간: 30분

const loadingMessages = {
    'news': '📰 뉴스 데이터 수집 중...',
    'twitter': '🐦 트위터 감성 분석 중...',
    'sec': '📊 SEC 공시 자료 확인 중...',
    'mcp': '💎 프리미엄 데이터 접근 중...',
    'sentiment': '🤖 AI 감성 분석 진행 중...',
    'score': '📈 종합 점수 계산 중...',
    'report': '📄 최종 리포트 생성 중...'
};
```

### 5.2 발표 시나리오 스크립트
```python
# 파일: demo_scenarios.py (새 파일)
# 작업 시간: 1시간

DEMO_SCENARIOS = {
    "apple_with_mcp": {
        "query": "애플 주식 전문가 의견 포함해서 분석해줘",
        "expected_agents": ["news", "twitter", "sec", "mcp"],
        "cache_data": {
            "AAPL": {
                "news": {...},  # 미리 준비된 데이터
                "mcp": {
                    "analyst_reports": {
                        "consensus_rating": "Buy",
                        "target_price": 220
                    }
                }
            }
        }
    }
}
```

## 작업 일정 요약

| 날짜 | 작업 내용 | 예상 시간 |
|------|----------|-----------|
| 7/17 | MCP 통합 (orchestrator, start script) | 3시간 |
| 7/18 | MCP 에이전트 실제 API 연동 | 4시간 |
| 7/19 | UI 개선 및 가중치 시스템 | 2시간 |
| 7/20 | 한글 지원 및 번역 | 2시간 |
| 7/21 | 에러 처리 및 안정성 | 3시간 |
| 7/22 | 발표 최적화 및 데모 준비 | 2시간 |
| 7/23 | 최종 테스트 및 리허설 | 3시간 |

## 주의사항

1. **단계별 테스트**: 각 수정 후 반드시 전체 시스템 테스트
2. **백업**: 수정 전 현재 작동하는 버전 백업
3. **롤백 계획**: 문제 발생 시 즉시 이전 버전으로 복구
4. **데모 데이터**: 네트워크 문제 대비 캐시 데이터 준비

## 테스트 명령어

```bash
# 1. 개별 에이전트 테스트
curl -X POST http://localhost:8215/collect_mcp_data \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# 2. 전체 시스템 테스트
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "애플 주식 전문가 의견 포함해서 분석해줘"}'

# 3. 웹소켓 연결 테스트
wscat -c ws://localhost:8100/ws
```

이 계획대로 진행하면 7/24 발표까지 안정적인 데모가 가능합니다!