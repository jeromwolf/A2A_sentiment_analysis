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

## 📚 추가 자료

- [pytest 문서](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

**테스트는 코드의 품질과 신뢰성을 보장합니다. 항상 테스트를 먼저 작성하세요!**