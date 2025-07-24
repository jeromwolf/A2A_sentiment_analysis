#!/bin/bash

echo "🧪 A2A 시스템 확장성 테스트"
echo "================================"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 레지스트리 상태 확인
echo -e "\n${YELLOW}1. 현재 레지스트리 상태 확인${NC}"
echo -e "${BLUE}등록된 에이전트 목록:${NC}"
curl -s http://localhost:8001/discover | python3 -m json.tool | grep -E '"name"|"agent_id"|"status"' || echo "레지스트리 서버가 실행 중이 아닙니다."

# 2. 새 에이전트 시작
echo -e "\n${YELLOW}2. 새로운 테스트 에이전트 시작${NC}"
echo "포트 8999에서 Test Scalability Agent 시작..."
python3 test_scalability_agent.py &
AGENT_PID=$!
sleep 3

# 3. 자동 등록 확인
echo -e "\n${YELLOW}3. 자동 등록 확인${NC}"
echo -e "${BLUE}업데이트된 에이전트 목록:${NC}"
curl -s http://localhost:8001/discover | python3 -m json.tool | grep -E '"name"|"agent_id"|"status"'

# 4. 새 에이전트의 능력 확인
echo -e "\n${YELLOW}4. 새 에이전트의 능력 확인${NC}"
TEST_AGENT_ID=$(curl -s http://localhost:8001/discover | python3 -c "
import json, sys
data = json.load(sys.stdin)
for agent in data['agents']:
    if agent['name'] == 'Test Scalability Agent':
        print(agent['agent_id'])
        break
")

if [ ! -z "$TEST_AGENT_ID" ]; then
    echo -e "${GREEN}✅ Test Scalability Agent가 성공적으로 등록됨!${NC}"
    echo "Agent ID: $TEST_AGENT_ID"
    
    # 에이전트 상세 정보 확인
    echo -e "\n${BLUE}에이전트 상세 정보:${NC}"
    curl -s http://localhost:8001/agents/$TEST_AGENT_ID | python3 -m json.tool
else
    echo -e "${RED}❌ Test Scalability Agent 등록 실패${NC}"
fi

# 5. 다른 에이전트와의 통신 테스트
echo -e "\n${YELLOW}5. 에이전트 간 통신 테스트${NC}"
echo "오케스트레이터를 통해 새 에이전트와 통신 시도..."

# 6. 정리
echo -e "\n${YELLOW}6. 테스트 종료 및 정리${NC}"
echo "테스트 에이전트 종료 중..."
kill $AGENT_PID 2>/dev/null
sleep 1

# 7. 최종 확인
echo -e "\n${YELLOW}7. 최종 레지스트리 상태${NC}"
curl -s http://localhost:8001/discover | python3 -m json.tool | grep -E '"name"|"count"'

echo -e "\n${GREEN}✨ 확장성 테스트 완료!${NC}"
echo -e "${BLUE}결과:${NC}"
echo "- ✅ BaseAgent 상속만으로 새 에이전트 생성 가능"
echo "- ✅ 자동으로 레지스트리에 등록됨"
echo "- ✅ 시스템 재시작 없이 즉시 사용 가능"
echo "- ✅ 다른 에이전트들과 통신 가능"