#!/bin/bash
echo "🚀 V2 시스템 전체를 시작합니다..."

# 기존 프로세스 종료
echo "🛑 기존 프로세스 종료 중..."
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
ps aux | grep "python.*registry" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
sleep 2

# 로그 디렉토리 생성
mkdir -p logs

# 1. Registry Server 시작
echo "📡 Registry Server 시작..."
uvicorn a2a_core.registry.service_registry:app --port 8001 > logs/registry.log 2>&1 &
sleep 3

# Registry 확인
curl -s http://localhost:8001/discover > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Registry가 정상적으로 시작되었습니다."
else
    echo "❌ Registry 시작 실패. 로그를 확인하세요."
    exit 1
fi

# 2. V1 에이전트들 시작 (V2 어댑터가 사용하므로 sentiment은 제외)
echo "🔧 V1 에이전트들 시작..."
uvicorn agents.data_collection_agent:app --port 8007 > logs/news_v1.log 2>&1 &
sleep 1
uvicorn agents.social_data_agent:app --port 8009 > logs/twitter_v1.log 2>&1 &
sleep 1
uvicorn agents.sec_agent:app --port 8010 > logs/sec_v1.log 2>&1 &
sleep 1
# sentiment_analysis_agent V1은 제외 (V2가 직접 처리)
uvicorn agents.score_calculation_agent:app --port 8003 > logs/score_v1.log 2>&1 &
sleep 1
uvicorn agents.report_generation_agent:app --port 8004 > logs/report_v1.log 2>&1 &
sleep 1

# 3. V2 에이전트들 시작
echo "🤖 V2 에이전트들 시작..."

# NLU V2 (순수 A2A 구현)
echo "  - NLU Agent V2..."
uvicorn agents.nlu_agent_v2:app --port 8108 > logs/nlu_v2.log 2>&1 &
sleep 1

# 데이터 수집 V2 어댑터
echo "  - News Agent V2 어댑터..."
uvicorn agents.news_agent_v2:app --port 8207 > logs/news_v2_adapter.log 2>&1 &
sleep 1

echo "  - Twitter Agent V2 어댑터..."
uvicorn agents.twitter_agent_v2:app --port 8209 > logs/twitter_v2_adapter.log 2>&1 &
sleep 1

echo "  - SEC Agent V2 어댑터..."
uvicorn agents.sec_agent_v2:app --port 8210 > logs/sec_v2_adapter.log 2>&1 &
sleep 1

# 분석 V2 A2A 구현
echo "  - Sentiment Analysis V2 (A2A 구현)..."
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 > logs/sentiment_v2.log 2>&1 &
sleep 1

echo "  - Score Calculation V2 어댑터..."
uvicorn agents.score_calculation_agent_v2:app --port 8203 > logs/score_v2_adapter.log 2>&1 &
sleep 1

echo "  - Report Generation V2 어댑터..."
uvicorn agents.report_generation_agent_v2:app --port 8204 > logs/report_v2_adapter.log 2>&1 &
sleep 1

# 4. 신규 V2 에이전트들 시작
echo "📊 신규 분석 에이전트들 시작..."

echo "  - Quantitative Analysis V2..."
uvicorn agents.quantitative_agent_v2:app --port 8211 > logs/quantitative_v2.log 2>&1 &
sleep 1

echo "  - Risk Analysis V2..."
uvicorn agents.risk_analysis_agent_v2:app --port 8212 > logs/risk_v2.log 2>&1 &
sleep 1

# 5. Main Orchestrator V2 시작
echo "🎯 Main Orchestrator V2 시작..."
uvicorn main_orchestrator_v2:app --port 8100 > logs/orchestrator_v2.log 2>&1 &
sleep 2

echo ""
echo "✅ V2 시스템이 완전히 시작되었습니다!"
echo ""
echo "📊 실행 중인 서비스:"
echo "   - Registry Server (port 8001)"
echo "   - V1 에이전트들 (8003-8010, sentiment 제외)"
echo "   - V2 A2A 에이전트들 (8202-8210)"
echo "   - Main Orchestrator V2 (port 8100)"
echo ""
echo "🌐 접속: http://localhost:8100"
echo ""
echo "📋 상태 확인:"
echo "   python check_v2_agents.py"
echo ""
echo "📜 로그 보기:"
echo "   tail -f logs/*.log"
echo ""
echo "🛑 종료:"
echo "   ./stop_all.sh"