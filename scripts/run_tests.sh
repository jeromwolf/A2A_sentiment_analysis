#!/bin/bash

echo "🧪 A2A 시스템 테스트 실행"
echo "========================="

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 환경 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TESTING=true

# 테스트 의존성 설치 확인
echo -e "${BLUE}테스트 의존성 확인...${NC}"
pip install -q -r test_requirements.txt

# 코드 품질 검사
echo -e "\n${BLUE}코드 품질 검사...${NC}"
echo "1. Black (코드 포맷팅)"
black --check a2a_core agents tests

echo -e "\n2. isort (import 정렬)"
isort --check-only a2a_core agents tests

echo -e "\n3. Flake8 (코드 스타일)"
flake8 a2a_core agents tests --max-line-length=100 --exclude=__pycache__

# 단위 테스트 실행
echo -e "\n${BLUE}단위 테스트 실행...${NC}"
pytest tests/unit -v -m "not slow" --tb=short

# 통합 테스트 실행
echo -e "\n${BLUE}통합 테스트 실행...${NC}"
pytest tests/integration -v -m "not slow" --tb=short

# 전체 테스트 커버리지
echo -e "\n${BLUE}전체 테스트 및 커버리지 분석...${NC}"
pytest tests --cov=a2a_core --cov=agents --cov-report=term-missing --cov-report=html

# 결과 요약
echo -e "\n${GREEN}테스트 완료!${NC}"
echo "커버리지 리포트: htmlcov/index.html"

# 옵션: 특정 테스트만 실행
if [ "$1" = "unit" ]; then
    echo -e "\n${BLUE}단위 테스트만 실행${NC}"
    pytest tests/unit -v
elif [ "$1" = "integration" ]; then
    echo -e "\n${BLUE}통합 테스트만 실행${NC}"
    pytest tests/integration -v
elif [ "$1" = "coverage" ]; then
    echo -e "\n${BLUE}커버리지 리포트 생성${NC}"
    pytest --cov=a2a_core --cov=agents --cov-report=html
    open htmlcov/index.html
elif [ "$1" = "watch" ]; then
    echo -e "\n${BLUE}테스트 감시 모드${NC}"
    pytest-watch tests
fi