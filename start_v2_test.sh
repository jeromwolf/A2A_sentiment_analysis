#!/bin/bash

echo "🚀 V2 테스트용 에이전트 시작..."

# 필수 V2 에이전트만 시작
echo "Starting Main Orchestrator V2..."
uvicorn main_orchestrator_v2:app --port 8100 --host 0.0.0.0 > /tmp/orchestrator.log 2>&1 &

echo "Starting News Agent V2 (수정된 버전)..."
uvicorn agents.news_agent_v2_pure:app --port 8307 --host 0.0.0.0 > /tmp/news.log 2>&1 &

echo "Starting Twitter Agent V2..."
uvicorn agents.twitter_agent_v2_pure:app --port 8209 --host 0.0.0.0 > /tmp/twitter.log 2>&1 &

echo "Starting SEC Agent V2..."
uvicorn agents.sec_agent_v2_pure:app --port 8210 --host 0.0.0.0 > /tmp/sec.log 2>&1 &

echo "Starting Sentiment Analysis Agent V2..."
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --host 0.0.0.0 > /tmp/sentiment.log 2>&1 &

echo "Starting Report Generation Agent V2..."
uvicorn agents.report_generation_agent_v2:app --port 8004 --host 0.0.0.0 > /tmp/report.log 2>&1 &

echo "Starting Score Calculation Agent V2..."
uvicorn agents.score_calculation_agent_v2:app --port 8003 --host 0.0.0.0 > /tmp/score.log 2>&1 &

echo "Starting NLU Agent (V1)..."
uvicorn agents.nlu_agent:app --port 8008 --host 0.0.0.0 > /tmp/nlu.log 2>&1 &

# 기타 필요한 에이전트
echo "Starting Quantitative Agent V2..."
uvicorn agents.quantitative_agent_v2:app --port 8211 --host 0.0.0.0 > /tmp/quantitative.log 2>&1 &

echo "Starting Risk Analysis Agent V2..."
uvicorn agents.risk_analysis_agent_v2:app --port 8212 --host 0.0.0.0 > /tmp/risk.log 2>&1 &

sleep 5

echo "✅ V2 에이전트 시작 완료"
echo ""
echo "로그 확인:"
echo "  tail -f /tmp/orchestrator.log"
echo "  tail -f /tmp/sec.log"
echo "  tail -f /tmp/news.log"