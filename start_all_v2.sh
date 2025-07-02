#!/bin/bash
echo "🚀 A2A V2 시스템을 시작합니다..."

# 기존 서비스 레지스트리 사용
echo "📡 Service Registry 시작 중..."
uvicorn a2a_core.registry.service_registry:app --port 8001 &
sleep 2  # Registry가 시작될 때까지 대기

# Orchestrator V2 시작
echo "🎯 Orchestrator V2 시작 중..."
uvicorn main_orchestrator_v2:app --port 8100 &
sleep 1

# NLU Agent V2 시작
echo "🧠 NLU Agent V2 시작 중..."
uvicorn agents.nlu_agent_v2:app --port 8108 &
sleep 1

# Data Collection Agents V2 시작 (나중에 추가)
# echo "📊 News Agent V2 시작 중..."
# uvicorn agents.news_agent_v2:app --port 8107 &
# sleep 1

# echo "🐦 Twitter Agent V2 시작 중..."
# uvicorn agents.twitter_agent_v2:app --port 8109 &
# sleep 1

# echo "📄 SEC Agent V2 시작 중..."
# uvicorn agents.sec_agent_v2:app --port 8110 &
# sleep 1

echo "✅ A2A V2 시스템이 시작되었습니다."
echo ""
echo "🌐 접속 URL: http://localhost:8100"
echo "📊 Registry: http://localhost:8001"
echo ""
echo "💡 시스템 종료: ./stop_all.sh"