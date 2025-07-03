#!/bin/bash

echo "🚀 A2A V2 에이전트 시작 중..."

# V2 에이전트들 시작
echo "Starting Main Orchestrator V2..."
uvicorn main_orchestrator_v2:app --port 8100 --host 0.0.0.0 &

echo "Starting News Agent V2..."
uvicorn agents.news_agent_v2_pure:app --port 8307 --host 0.0.0.0 &

echo "Starting Twitter Agent V2..."
uvicorn agents.twitter_agent_v2_pure:app --port 8209 --host 0.0.0.0 &

echo "Starting SEC Agent V2..."
uvicorn agents.sec_agent_v2_pure:app --port 8210 --host 0.0.0.0 &

echo "Starting Sentiment Analysis Agent V2..."
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --host 0.0.0.0 &

echo "Starting Report Generation Agent V2..."
uvicorn agents.report_generation_agent_v2:app --port 8004 --host 0.0.0.0 &

echo "Starting Score Calculation Agent V2..."
uvicorn agents.score_calculation_agent_v2:app --port 8003 --host 0.0.0.0 &

echo "Starting Quantitative Agent V2..."
uvicorn agents.quantitative_agent_v2:app --port 8211 --host 0.0.0.0 &

echo "Starting Risk Analysis Agent V2..."
uvicorn agents.risk_analysis_agent_v2:app --port 8212 --host 0.0.0.0 &

# NLU는 V1 사용
echo "Starting NLU Agent..."
uvicorn agents.nlu_agent:app --port 8008 --host 0.0.0.0 &

sleep 5

echo "✅ 모든 V2 에이전트가 시작되었습니다."
echo ""
echo "실행 중인 에이전트:"
echo "- Main Orchestrator V2: http://localhost:8100"
echo "- News Agent V2: http://localhost:8307"
echo "- Twitter Agent V2: http://localhost:8209"
echo "- SEC Agent V2: http://localhost:8210"
echo "- Sentiment Analysis V2: http://localhost:8202"
echo "- Score Calculation V2: http://localhost:8003"
echo "- Report Generation V2: http://localhost:8004"
echo "- Quantitative V2: http://localhost:8211"
echo "- Risk Analysis V2: http://localhost:8212"
echo "- NLU Agent: http://localhost:8008"