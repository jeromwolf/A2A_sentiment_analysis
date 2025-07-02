#!/bin/bash
echo "🚀 A2A V2 완전한 시스템을 시작합니다..."

# Registry 시작
echo "📡 Registry Server 시작 중..."
python -m a2a_core.registry.registry_server &
REGISTRY_PID=$!
sleep 3  # Registry가 완전히 시작될 때까지 대기

# Registry 확인
echo "🔍 Registry 상태 확인..."
curl -s http://localhost:8001/registry/agents > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Registry가 정상적으로 시작되었습니다."
else
    echo "❌ Registry 시작 실패. 로그를 확인하세요."
    exit 1
fi

# Main Orchestrator V2 시작
echo "🎯 Main Orchestrator V2 시작 중..."
uvicorn main_orchestrator_v2:app --port 8100 --reload &
sleep 2

# NLU Agent V2 시작
echo "🧠 NLU Agent V2 시작 중..."
uvicorn agents.nlu_agent_v2:app --port 8108 --reload &
sleep 1

# Data Collection Agents V2 Pure 시작
echo "📊 News Agent V2 Pure 시작 중..."
uvicorn agents.news_agent_v2_pure:app --port 8307 --reload &
sleep 1

echo "🐦 Twitter Agent V2 Pure 시작 중..."
uvicorn agents.twitter_agent_v2_pure:app --port 8209 --reload &
sleep 1

echo "📄 SEC Agent V2 Pure 시작 중..."
uvicorn agents.sec_agent_v2_pure:app --port 8210 --reload &
sleep 1

# Analysis Agents V2 시작
echo "🤖 Sentiment Analysis V2 시작 중..."
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --reload &
sleep 1

echo "📈 Score Calculation V2 시작 중..."
uvicorn agents.score_calculation_agent_v2_adapter:app --port 8203 --reload &
sleep 1

echo "📝 Report Generation V2 시작 중..."
uvicorn agents.report_generation_agent_v2_adapter:app --port 8204 --reload &
sleep 1

echo ""
echo "✅ A2A V2 시스템이 시작되었습니다."
echo ""
echo "🌐 Main UI: http://localhost:8100"
echo "📊 Registry: http://localhost:8001/registry/agents"
echo ""
echo "📋 실행 중인 서비스:"
echo "   - Registry Server (port 8001)"
echo "   - Main Orchestrator V2 (port 8100)"
echo "   - NLU Agent V2 (port 8108)"
echo "   - News Agent V2 Pure (port 8307)"
echo "   - Twitter Agent V2 Pure (port 8209)"
echo "   - SEC Agent V2 Pure (port 8210)"
echo "   - Sentiment Analysis V2 (port 8202)"
echo "   - Score Calculation V2 (port 8203)"
echo "   - Report Generation V2 (port 8204)"
echo ""
echo "💡 시스템 종료: ./stop_all.sh"
echo "🔍 상태 확인: python check_v2_agents.py"