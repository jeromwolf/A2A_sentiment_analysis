#!/bin/bash
echo "🚀 A2A 기반 분석 시스템을 시작합니다..."

# 서비스 레지스트리 시작 (가장 먼저)
echo "📋 서비스 레지스트리 시작..."
uvicorn a2a_core.registry.service_registry:app --port 8001 &
sleep 3  # 레지스트리가 완전히 시작될 때까지 대기

# 새로운 A2A 에이전트들 시작
echo "🤖 A2A 에이전트 시작..."
uvicorn agents.nlu_agent_v2:app --port 8108 &

# V2 데이터 수집 어댑터 시작
echo "📊 V2 데이터 수집 어댑터 시작..."
uvicorn agents.news_agent_v2:app --port 8207 &
sleep 1
uvicorn agents.twitter_agent_v2:app --port 8209 &
sleep 1
uvicorn agents.sec_agent_v2:app --port 8210 &
sleep 1

# 새로운 오케스트레이터 시작
echo "🎯 A2A 오케스트레이터 시작..."
uvicorn main_orchestrator_v2:app --port 8100 &

# 기존 에이전트들도 함께 실행 (호환성을 위해)
echo "📦 기존 에이전트 시작..."
uvicorn main_orchestrator:app --port 8000 &
uvicorn agents.nlu_agent:app --port 8008 &
uvicorn agents.advanced_data_agent:app --port 8007 &
uvicorn agents.twitter_agent:app --port 8009 &
uvicorn agents.sec_agent:app --port 8010 &
uvicorn agents.sentiment_analysis_agent:app --port 8002 &
uvicorn agents.score_calculation_agent:app --port 8003 &
uvicorn agents.report_generation_agent:app --port 8004 &

echo "✅ 모든 서비스가 시작되었습니다."
echo ""
echo "🌐 접속 URL:"
echo "   - 기존 시스템: http://localhost:8000"
echo "   - A2A 시스템: http://localhost:8100"
echo "   - 서비스 레지스트리: http://localhost:8001/docs"
echo ""
echo "종료하려면 ./stop_a2a.sh를 실행하세요."