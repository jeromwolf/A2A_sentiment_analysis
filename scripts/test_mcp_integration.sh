#!/bin/bash

echo "🚀 MCP Integration Test Script"
echo "================================"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 상태 확인
echo -e "\n${YELLOW}1. 시스템 상태 확인${NC}"
echo "------------------------"

# Docker 컨테이너 확인
echo "📦 실행 중인 Docker 컨테이너:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(registry|orchestrator|mcp|yahoo|alpha)"

# 2. 레지스트리 테스트
echo -e "\n${YELLOW}2. 레지스트리 상태${NC}"
echo "------------------------"
echo "🔍 등록된 에이전트 확인:"
curl -s http://localhost:8001/agents | jq '.[].name' 2>/dev/null || echo "❌ 레지스트리 연결 실패"

# 3. Yahoo Finance MCP 에이전트 테스트
echo -e "\n${YELLOW}3. Yahoo Finance MCP 에이전트 테스트${NC}"
echo "------------------------"

echo "📊 AAPL 주식 분석 요청:"
curl -s -X POST http://localhost:8213/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' | jq '.ticker, .data_source, .timestamp' 2>/dev/null || echo "❌ Yahoo Finance 에이전트 연결 실패"

# 4. Alpha Vantage MCP 에이전트 테스트
echo -e "\n${YELLOW}4. Alpha Vantage MCP 에이전트 테스트${NC}"
echo "------------------------"

echo "📈 MSFT 주식 분석 요청:"
curl -s -X POST http://localhost:8214/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MSFT"}' | jq '.ticker, .data_source, .timestamp' 2>/dev/null || echo "❌ Alpha Vantage 에이전트 연결 실패"

echo "🔧 고급 기술적 분석 (RSI, MACD):"
curl -s -X POST http://localhost:8214/advanced_analysis \
  -H "Content-Type: application/json" \
  -d '{"ticker": "GOOGL", "indicators": ["RSI", "MACD"]}' | jq '.signal' 2>/dev/null || echo "❌ 고급 분석 실패"

# 5. 포트 확인
echo -e "\n${YELLOW}5. 포트 상태 확인${NC}"
echo "------------------------"
echo "🔌 열린 포트:"
for port in 8001 8100 8213 8214 3001 3002; do
    if nc -z localhost $port 2>/dev/null; then
        echo -e "  ✅ Port $port: ${GREEN}열림${NC}"
    else
        echo -e "  ❌ Port $port: ${RED}닫힘${NC}"
    fi
done

# 6. Python 통합 테스트 실행
echo -e "\n${YELLOW}6. Python 통합 테스트${NC}"
echo "------------------------"
if [ -f "test_mcp_integration.py" ]; then
    echo "🐍 Python 테스트 스크립트 실행:"
    python test_mcp_integration.py
else
    echo "❌ test_mcp_integration.py 파일을 찾을 수 없습니다"
fi

echo -e "\n================================"
echo -e "${GREEN}✅ 테스트 완료!${NC}"
echo -e "================================\n"

# 추가 정보
echo "💡 추가 테스트 방법:"
echo "  1. 브라우저에서 http://localhost:8100 접속하여 UI 테스트"
echo "  2. docker logs <container_name> 으로 로그 확인"
echo "  3. 개별 MCP 서버 상태:"
echo "     - Yahoo Finance MCP: http://localhost:3001"
echo "     - Alpha Vantage MCP: http://localhost:3002"