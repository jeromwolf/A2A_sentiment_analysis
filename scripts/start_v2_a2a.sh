#!/bin/bash

echo "🚀 A2A Sentiment Analysis System V2 (실제 A2A 프로토콜 사용) 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# 기존 프로세스 종료 함수
cleanup() {
    echo -e "\n${YELLOW}🛑 시스템 종료 중...${NC}"
    
    # 모든 uvicorn 프로세스 종료
    pkill -f "uvicorn.*8001" 2>/dev/null
    pkill -f "uvicorn.*8100" 2>/dev/null
    pkill -f "uvicorn.*8108" 2>/dev/null
    pkill -f "uvicorn.*8307" 2>/dev/null
    pkill -f "uvicorn.*8209" 2>/dev/null
    pkill -f "uvicorn.*8210" 2>/dev/null
    pkill -f "uvicorn.*8213" 2>/dev/null
    pkill -f "uvicorn.*8202" 2>/dev/null
    pkill -f "uvicorn.*8211" 2>/dev/null
    pkill -f "uvicorn.*8203" 2>/dev/null
    pkill -f "uvicorn.*8212" 2>/dev/null
    pkill -f "uvicorn.*8204" 2>/dev/null
    pkill -f "uvicorn.*8215" 2>/dev/null
    
    sleep 2
    echo -e "${GREEN}✅ 모든 프로세스 종료 완료${NC}"
}

# Ctrl+C 처리
trap cleanup EXIT

# 기존 프로세스 정리
echo -e "${YELLOW}🧹 기존 프로세스 정리 중...${NC}"
cleanup

# 환경 변수 체크
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 파일이 없습니다. .env.example을 참고하여 생성해주세요.${NC}"
    exit 1
fi

# 필수 API 키 체크
source .env
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY가 설정되지 않았습니다.${NC}"
    exit 1
fi

# Python 환경 체크
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# 패키지 설치 체크
echo -e "${BLUE}📦 필수 패키지 확인 중...${NC}"
pip3 install -q -r requirements.txt

# 서비스 시작 함수
start_service() {
    local name=$1
    local module=$2
    local port=$3
    
    echo -e "${BLUE}🚀 $name 시작 (포트: $port)...${NC}"
    uvicorn $module --port $port --log-level error > /dev/null 2>&1 &
    sleep 2
    
    # 프로세스 확인
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name 시작 완료${NC}"
    else
        echo -e "${RED}❌ $name 시작 실패${NC}"
        return 1
    fi
}

# 1. Registry Server 시작
start_service "Registry Server" "a2a_core.registry.registry_server:app" 8001

# 2. Main Orchestrator V2 (A2A 버전) 시작
start_service "Main Orchestrator V2 (A2A)" "main_orchestrator_v2_a2a:app" 8100

# 3. NLU Agent V2 시작
start_service "NLU Agent V2" "agents.nlu_agent_v2:app" 8108

# 4. 데이터 수집 에이전트들 시작
start_service "News Agent V2" "agents.news_agent_v2:app" 8307
start_service "Twitter Agent V2" "agents.twitter_agent_v2:app" 8209
start_service "SEC Agent V2" "agents.sec_agent_v2_pure:app" 8210
start_service "DART Agent V2" "agents.dart_agent_v2:app" 8213
start_service "MCP Data Agent" "agents.mcp_data_agent:app" 8215

# 5. 분석 에이전트들 시작
start_service "Sentiment Analysis Agent V2" "agents.sentiment_analysis_agent_v2:app" 8202
start_service "Quantitative Analysis Agent V2" "agents.quantitative_analysis_agent_v2:app" 8211
start_service "Score Calculation Agent V2" "agents.score_calculation_agent_v2:app" 8203
start_service "Risk Analysis Agent V2" "agents.risk_analysis_agent_v2:app" 8212
start_service "Report Generation Agent V2" "agents.report_generation_agent_v2:app" 8204

echo -e "\n${GREEN}✨ A2A Sentiment Analysis System V2 시작 완료!${NC}"
echo -e "${YELLOW}📌 웹 인터페이스: http://localhost:8100${NC}"
echo -e "${YELLOW}📌 Registry 상태: http://localhost:8001/agents${NC}"
echo -e "${YELLOW}📌 이제 실제 A2A 프로토콜을 사용합니다!${NC}"
echo ""
echo -e "${BLUE}종료하려면 Ctrl+C를 누르세요.${NC}"

# 프로세스 유지
wait