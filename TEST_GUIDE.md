# A2A 시스템 테스트 가이드

## 🧪 TDD (Test-Driven Development) 접근법

이 프로젝트는 TDD 방식으로 개발되었으며, 모든 핵심 컴포넌트에 대한 포괄적인 테스트를 포함합니다.

## 📋 테스트 구조

```
tests/
├── __init__.py
├── conftest.py          # pytest fixtures 및 공통 설정
├── unit/                # 단위 테스트
│   ├── test_service_registry.py
│   ├── test_message_protocol.py
│   ├── test_base_agent.py
│   └── test_nlu_agent_v2.py
├── integration/         # 통합 테스트
│   └── test_a2a_integration.py
└── fixtures/           # 테스트 데이터
```

## 🚀 테스트 실행 방법

### 1. 테스트 환경 설정
```bash
# 테스트 의존성 설치
pip install -r test_requirements.txt
```

### 2. 전체 테스트 실행
```bash
# 실행 권한 부여 (최초 1회)
chmod +x run_tests.sh

# 전체 테스트 실행
./run_tests.sh
```

### 3. 특정 테스트 실행
```bash
# 단위 테스트만
./run_tests.sh unit

# 통합 테스트만
./run_tests.sh integration

# 커버리지 리포트 생성
./run_tests.sh coverage
```

### 4. 개별 테스트 실행
```bash
# 특정 파일
pytest tests/unit/test_message_protocol.py -v

# 특정 테스트 함수
pytest tests/unit/test_service_registry.py::TestServiceRegistry::test_register_agent -v

# 특정 마커로 필터링
pytest -m "not slow" -v
```

## 📊 테스트 커버리지

현재 목표 커버리지: **80% 이상**

커버리지 확인:
```bash
pytest --cov=a2a_core --cov=agents --cov-report=html
open htmlcov/index.html
```

## 🧩 주요 테스트 케이스

### 1. 서비스 레지스트리 테스트
- ✅ 에이전트 등록/해제
- ✅ 동적 에이전트 발견
- ✅ 능력 기반 검색
- ✅ 하트비트 메커니즘
- ✅ 비활성 에이전트 필터링

### 2. 메시지 프로토콜 테스트
- ✅ 요청/응답 메시지 생성
- ✅ 이벤트/에러 메시지 처리
- ✅ 메시지 우선순위
- ✅ TTL 및 만료 처리
- ✅ 재시도 로직

### 3. 베이스 에이전트 테스트
- ✅ 에이전트 초기화
- ✅ 능력 등록
- ✅ 메시지 송수신
- ✅ 이벤트 브로드캐스팅
- ✅ 에이전트 생명주기

### 4. NLU Agent V2 테스트
- ✅ 키워드 기반 티커 추출
- ✅ Gemini API 통합
- ✅ 에러 처리
- ✅ 이벤트 발행

### 5. 통합 테스트
- ✅ 전체 시스템 워크플로우
- ✅ 에이전트 간 통신
- ✅ 에러 전파
- ✅ 성능 테스트

## 🔧 테스트 작성 가이드

### 단위 테스트 템플릿
```python
import pytest
from unittest.mock import Mock, patch

class TestMyComponent:
    """컴포넌트 테스트"""
    
    @pytest.fixture
    def my_component(self):
        """테스트 대상 fixture"""
        return MyComponent()
    
    def test_should_do_something(self, my_component):
        """Given-When-Then 패턴"""
        # Given: 초기 상태 설정
        initial_state = "ready"
        
        # When: 동작 수행
        result = my_component.do_something(initial_state)
        
        # Then: 결과 검증
        assert result == "expected"
```

### 비동기 테스트
```python
@pytest.mark.asyncio
async def test_async_operation():
    """비동기 동작 테스트"""
    # Given
    async_component = AsyncComponent()
    
    # When
    result = await async_component.async_method()
    
    # Then
    assert result is not None
```

## 🐛 디버깅 팁

### 1. 상세 출력
```bash
pytest -vv -s tests/unit/test_service_registry.py
```

### 2. 특정 테스트만 실행
```bash
pytest -k "test_register" -v
```

### 3. 실패한 테스트만 재실행
```bash
pytest --lf -v
```

### 4. 디버거 사용
```python
def test_debug_this():
    import pdb; pdb.set_trace()  # 디버거 중단점
    # 테스트 코드
```

## 📈 성능 테스트

### 벤치마크 실행
```bash
pytest tests/performance --benchmark-only
```

### 부하 테스트
```bash
locust -f tests/performance/locustfile.py
```

## ✅ CI/CD 통합

GitHub Actions 설정:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_requirements.txt
    - name: Run tests
      run: ./run_tests.sh
```

## 🔍 문제 해결

### 1. Import 오류
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. 비동기 테스트 경고
```python
# pytest.ini에 추가
asyncio_mode = auto
```

### 3. 느린 테스트 스킵
```bash
pytest -m "not slow"
```

## 📊 정량적 지표 평가 가이드

시스템이 제공하는 정량적 지표를 올바르게 해석하는 방법입니다.

### 1. 📈 주요 정량적 지표

#### 1.1 주가 관련 지표
- **현재가**: 실시간 주식 가격
- **일일 변동률**: 전일 대비 가격 변화율 (%)
- **52주 최고/최저**: 지난 1년간 최고가와 최저가

#### 1.2 기술적 지표

##### RSI (Relative Strength Index)
- **범위**: 0-100
- **해석**:
  - 70 이상: 과매수 구간 (조정 가능성)
  - 50 근처: 중립 (neutral)
  - 30 이하: 과매도 구간 (반등 가능성)
- **활용**: 매수/매도 타이밍 판단

##### MACD (Moving Average Convergence Divergence)
- **구성**: MACD선, 시그널선, 히스토그램
- **해석**:
  - 상승 교차 (Golden Cross): 매수 신호
  - 하락 교차 (Death Cross): 매도 신호
  - 중립 (neutral): 추세 전환 대기

#### 1.3 가치평가 지표

##### PER (Price Earnings Ratio)
- **계산**: 주가 ÷ 주당순이익
- **해석**:
  - 낮은 PER (< 10): 저평가 가능성
  - 업종 평균 비교 필수
  - Growth Adjusted PER 고려
- **예시**: PER 251 (Growth Adjusted) = 높은 성장성 반영

##### 목표 주가
- **산출 방법**: 
  - DCF (현금흐름할인법)
  - PER 비교법
  - PBR 기반 산정
- **해석**:
  - 현재가 < 목표가: 상승 여력 (%)
  - 현재가 > 목표가: 하락 리스크
  - 예시: 현재 $314 → 목표 $357 (+14.0%)

### 2. 🎯 투자 판단 기준

#### 매수 신호 (Buy)
- RSI < 30 (과매도)
- MACD 상승 교차
- 현재가가 목표가 대비 10% 이상 낮음
- PER이 업종 평균보다 20% 이상 낮음

#### 중립 신호 (Neutral)
- RSI 40-60
- MACD 중립
- 현재가와 목표가 차이 ±5% 이내
- 추가 신호 대기 필요

#### 매도 신호 (Sell)
- RSI > 70 (과매수)
- MACD 하락 교차
- 현재가가 목표가 초과
- 밸류에이션 과열

### 3. 📉 리스크 지표

#### 변동성 지표
- **일일 변동폭**: 일중 최고가-최저가 차이
- **베타(β)**: 시장 대비 변동성
  - β > 1: 시장보다 변동성 큼
  - β < 1: 시장보다 안정적

#### 거래량 지표
- **평균 거래량 대비**: 이상 거래 감지
- **거래대금**: 유동성 평가

### 4. 🔄 종합 평가 방법

1. **다중 지표 교차 검증**
   - 단일 지표로 판단 금지
   - 최소 3개 이상 지표 확인

2. **시간대별 분석**
   - 단기 (일/주 단위)
   - 중기 (월 단위)
   - 장기 (분기/연 단위)

3. **감성 지표와 병행**
   - 정량적 지표 + 감성 분석 결합
   - 시장 심리와 기술적 지표 비교

### 5. ⚠️ 주의사항

- **과도한 의존 금지**: 정량적 지표는 참고용
- **시장 상황 고려**: 전체 시장 트렌드 확인
- **업종 특성 반영**: 업종별 기준 차이 존재
- **지속적 모니터링**: 지표는 실시간 변화

### 6. 💡 실전 활용 예시

```
현재 상황:
- 주가: $313.51 (+1.17%)
- RSI: 50.0 (중립)
- MACD: neutral
- 목표가: $357 (+14.0%)
- PER: 251 (Growth Adjusted)

판단:
→ RSI 중립, 목표가 대비 상승 여력 14%
→ 성장주 특성상 높은 PER 정상
→ 투자 의견: Buy (중장기 관점)
```

## 📚 추가 자료

- [pytest 문서](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [기술적 분석 가이드](https://www.investopedia.com/technical-analysis-4689657)
- [가치평가 지표 해설](https://www.investopedia.com/terms/p/price-earningsratio.asp)

---

**테스트는 코드의 품질과 신뢰성을 보장합니다. 항상 테스트를 먼저 작성하세요!**