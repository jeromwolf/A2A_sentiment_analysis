#!/bin/bash

echo "🚀 A2A Sentiment Analysis System 안정적 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Registry Server 시작
echo -e "${YELLOW}1. Registry Server 시작...${NC}"
uvicorn a2a_core.registry.registry_server:app --port 8001 --log-level error > /dev/null 2>&1 &
sleep 5
echo -e "${GREEN}✅ Registry Server 시작 완료${NC}"

# 2. Main Orchestrator 시작
echo -e "${YELLOW}2. Main Orchestrator 시작...${NC}"
uvicorn main_orchestrator_v2:app --port 8100 --log-level error > /dev/null 2>&1 &
sleep 5
echo -e "${GREEN}✅ Main Orchestrator 시작 완료${NC}"

# 3. NLU Agent 시작
echo -e "${YELLOW}3. NLU Agent 시작...${NC}"
uvicorn agents.nlu_agent_v2:app --port 8108 --log-level error > /dev/null 2>&1 &
sleep 3
echo -e "${GREEN}✅ NLU Agent 시작 완료${NC}"

# 4. 데이터 수집 에이전트들 시작
echo -e "${YELLOW}4. 데이터 수집 에이전트들 시작...${NC}"
uvicorn agents.news_agent_v2_pure:app --port 8307 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.twitter_agent_v2_pure:app --port 8209 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.sec_agent_v2_pure:app --port 8210 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.mcp_data_agent:app --port 8215 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.dart_agent_v2:app --port 8213 --log-level error > /dev/null 2>&1 &
sleep 2
echo -e "${GREEN}✅ 데이터 수집 에이전트들 시작 완료${NC}"

# 5. 분석 에이전트들 시작
echo -e "${YELLOW}5. 분석 에이전트들 시작...${NC}"
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.quantitative_agent_v2:app --port 8211 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.score_calculation_agent_v2:app --port 8203 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.risk_analysis_agent_v2:app --port 8212 --log-level error > /dev/null 2>&1 &
sleep 2
uvicorn agents.report_generation_agent_v2:app --port 8204 --log-level error > /dev/null 2>&1 &
sleep 2
echo -e "${GREEN}✅ 분석 에이전트들 시작 완료${NC}"

# 6. 등록 확인
echo -e "${YELLOW}6. 에이전트 등록 확인...${NC}"
sleep 5
curl -s http://localhost:8001/discover | python3 -c "import json, sys; data = json.load(sys.stdin); print(f'✅ 총 {len(data[\"agents\"])}개 에이전트 등록됨')"

echo -e "${GREEN}✨ 시스템 시작 완료!${NC}"
echo -e "${YELLOW}📌 웹 인터페이스: http://localhost:8100${NC}"
echo ""
echo "종료하려면: pkill -f uvicorn"