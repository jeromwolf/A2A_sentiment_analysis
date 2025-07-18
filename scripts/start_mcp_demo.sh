#!/bin/bash

echo "🚀 MCP Demo 시작 스크립트"
echo "=========================="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Docker 실행 확인
echo -e "\n${YELLOW}1. Docker 상태 확인${NC}"
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker가 실행 중입니다${NC}"
else
    echo -e "${RED}❌ Docker가 실행되지 않습니다. Docker Desktop을 시작해주세요${NC}"
    echo "   macOS: open -a Docker"
    exit 1
fi

# 네트워크 생성 (없으면)
echo -e "\n${YELLOW}2. Docker 네트워크 설정${NC}"
if docker network inspect a2a-network >/dev/null 2>&1; then
    echo -e "${GREEN}✅ a2a-network가 이미 존재합니다${NC}"
else
    echo "📌 a2a-network 생성 중..."
    docker network create a2a-network
    echo -e "${GREEN}✅ 네트워크 생성 완료${NC}"
fi

# 레지스트리 확인 및 시작
echo -e "\n${YELLOW}3. 레지스트리 서비스 확인${NC}"
if docker ps | grep -q "a2a-registry"; then
    echo -e "${GREEN}✅ 레지스트리가 이미 실행 중입니다${NC}"
else
    echo "📌 레지스트리 시작 중..."
    # 간단한 레지스트리 모드로 실행
    docker run -d \
        --name a2a-registry \
        --network a2a-network \
        -p 8001:8001 \
        -e PYTHONUNBUFFERED=1 \
        python:3.11-slim \
        bash -c "pip install fastapi uvicorn && python -c '
from fastapi import FastAPI
app = FastAPI()
agents = []

@app.get(\"/agents\")
def get_agents():
    return agents

@app.post(\"/register\")
def register(agent: dict):
    agents.append(agent)
    return {\"status\": \"registered\"}

if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8001)
'"
    
    sleep 5
    echo -e "${GREEN}✅ 레지스트리 시작 완료${NC}"
fi

# MCP 서버 및 에이전트 시작
echo -e "\n${YELLOW}4. MCP 서버 및 에이전트 시작${NC}"
echo "📌 docker-compose로 MCP 컴포넌트 시작 중..."

# .env 파일 확인
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. 기본값으로 생성합니다${NC}"
    echo "ALPHA_VANTAGE_API_KEY=demo" > .env
fi

# Docker Compose 실행
docker-compose -f docker-compose.mcp.yml up -d

# 잠시 대기
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 상태 확인
echo -e "\n${YELLOW}5. 서비스 상태 확인${NC}"
echo "📊 실행 중인 컨테이너:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(registry|mcp|yahoo|alpha)" || echo "컨테이너가 없습니다"

# 포트 확인
echo -e "\n${YELLOW}6. 포트 상태${NC}"
for port in 8001 8213 8214 3001 3002; do
    if nc -z localhost $port 2>/dev/null; then
        case $port in
            8001) echo -e "✅ Port $port: ${GREEN}레지스트리${NC}" ;;
            8213) echo -e "✅ Port $port: ${GREEN}Yahoo Finance Agent${NC}" ;;
            8214) echo -e "✅ Port $port: ${GREEN}Alpha Vantage Agent${NC}" ;;
            3001) echo -e "✅ Port $port: ${GREEN}Yahoo Finance MCP Server${NC}" ;;
            3002) echo -e "✅ Port $port: ${GREEN}Alpha Vantage MCP Server${NC}" ;;
        esac
    else
        echo -e "❌ Port $port: ${RED}닫힘${NC}"
    fi
done

echo -e "\n${GREEN}✅ MCP 데모 환경 준비 완료!${NC}"
echo -e "\n${YELLOW}테스트 방법:${NC}"
echo "1. 빠른 테스트: python quick_test_mcp.py"
echo "2. 전체 테스트: python test_mcp_integration.py"
echo "3. 수동 테스트:"
echo "   curl -X POST http://localhost:8213/analyze -d '{\"ticker\":\"AAPL\"}' -H 'Content-Type: application/json'"
echo ""
echo "종료하려면: docker-compose -f docker-compose.mcp.yml down"