#!/bin/bash

echo "🚀 최소 에이전트 세트 시작"
echo "========================="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Mock 데이터를 반환하는 간단한 에이전트들 시작
echo -e "\n${YELLOW}기본 에이전트 시작${NC}"

# News Agent (Mock)
python agents/news_agent_v2_pure.py > news.log 2>&1 & 
echo "📰 News Agent 시작 (PID: $!)"

# Sentiment Agent
python agents/sentiment_analysis_agent_v2.py > sentiment.log 2>&1 &
echo "😊 Sentiment Agent 시작 (PID: $!)"

# Report Agent  
python agents/report_generation_agent_v2.py > report.log 2>&1 &
echo "📄 Report Agent 시작 (PID: $!)"

echo -e "\n${GREEN}✅ 에이전트 시작 완료${NC}"
echo "테스트: 브라우저에서 'AAPL 분석해줘' 입력"