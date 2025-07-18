#!/bin/bash

echo "🚀 A2A + MCP 전체 시스템 Docker 실행"
echo "===================================="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 기존 프로세스 정리
echo -e "\n${YELLOW}1. 기존 프로세스 정리${NC}"
echo "로컬 Python 프로세스 종료 중..."
pkill -f "start_mock_mcp.py" 2>/dev/null
pkill -f "mcp_yahoo_finance_agent.py" 2>/dev/null
pkill -f "mcp_alpha_vantage_agent.py" 2>/dev/null
echo -e "${GREEN}✅ 정리 완료${NC}"

# 2. Docker 컨테이너 정리
echo -e "\n${YELLOW}2. 기존 Docker 컨테이너 정리${NC}"
docker-compose -f docker-compose.all.yml down 2>/dev/null
docker rm -f a2a-registry 2>/dev/null
echo -e "${GREEN}✅ 컨테이너 정리 완료${NC}"

# 3. 빌드 및 실행
echo -e "\n${YELLOW}3. Docker 이미지 빌드 및 실행${NC}"
echo "📦 필요한 패키지 설치를 위한 이미지 빌드 중..."
docker-compose -f docker-compose.all.yml build

echo -e "\n🚀 전체 시스템 시작..."
docker-compose -f docker-compose.all.yml up -d

# 4. 대기
echo -e "\n⏳ 서비스 시작 대기 중..."
sleep 10

# 5. 상태 확인
echo -e "\n${YELLOW}4. 서비스 상태 확인${NC}"
docker-compose -f docker-compose.all.yml ps

# 6. 포트 확인
echo -e "\n${YELLOW}5. 포트 상태${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "서비스               포트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Registry            8001"
echo "Orchestrator        8100"
echo "Yahoo MCP           3001"
echo "Alpha MCP           3002"
echo "NLU Agent           8108"
echo "News Agent          8307"
echo "Twitter Agent       8209"
echo "SEC Agent           8210"
echo "Sentiment Agent     8202"
echo "MCP Yahoo Agent     8213"
echo "MCP Alpha Agent     8214"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${GREEN}✅ 전체 시스템 실행 완료!${NC}"
echo -e "\n${YELLOW}테스트 방법:${NC}"
echo "1. UI 접속: http://localhost:8100"
echo "2. 빠른 테스트: python demo_test.py"
echo "3. MCP 직접 테스트: python test_mcp_direct.py"
echo ""
echo "로그 보기: docker-compose -f docker-compose.all.yml logs -f [서비스명]"
echo "종료하기: docker-compose -f docker-compose.all.yml down"