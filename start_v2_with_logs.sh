#\!/bin/bash
echo "🚀 A2A V2 시스템을 로그와 함께 시작합니다..."

# 로그 디렉토리 생성
mkdir -p logs

# Registry 시작
echo "📡 Registry Server 시작 중..."
nohup python -m a2a_core.registry.registry_server > logs/registry_new.log 2>&1 &
sleep 3

# Registry 확인
echo "🔍 Registry 상태 확인..."
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "✅ Registry가 정상적으로 시작되었습니다."
else
    echo "❌ Registry 시작 실패. 로그를 확인하세요."
    tail -20 logs/registry_new.log
    exit 1
fi

# Main Orchestrator V2 시작
echo "🎯 Main Orchestrator V2 시작 중..."
nohup uvicorn main_orchestrator_v2:app --port 8100 > logs/orchestrator_v2_full.log 2>&1 &
sleep 3

# NLU Agent V2 시작
echo "🧠 NLU Agent V2 시작 중..."
nohup uvicorn agents.nlu_agent_v2:app --port 8108 > logs/nlu_v2_full.log 2>&1 &
sleep 2

# Data Collection Agents V2 Pure 시작
echo "📊 News Agent V2 Pure 시작 중..."
nohup uvicorn agents.news_agent_v2_pure:app --port 8307 > logs/news_v2_pure.log 2>&1 &
sleep 2

echo "🐦 Twitter Agent V2 Pure 시작 중..."
nohup uvicorn agents.twitter_agent_v2_pure:app --port 8209 > logs/twitter_v2_pure.log 2>&1 &
sleep 2

echo "📄 SEC Agent V2 Pure 시작 중..."
nohup uvicorn agents.sec_agent_v2_pure:app --port 8210 > logs/sec_v2_pure.log 2>&1 &
sleep 2

# Analysis Agents V2 시작
echo "🤖 Sentiment Analysis V2 (Simple) 시작 중..."
nohup uvicorn agents.sentiment_analysis_agent_v2_simple:app --port 8202 > logs/sentiment_v2_full.log 2>&1 &
sleep 2

# 실행 확인
echo ""
echo "🔍 실행 상태 확인 중..."
sleep 3

# 각 포트 확인
PORTS=(8001 8100 8208 8307 8209 8310 8202)
SERVICES=("Registry" "Orchestrator" "NLU" "News" "Twitter" "SEC" "Sentiment")

for i in ${\!PORTS[@]}; do
    if lsof -i :${PORTS[$i]} | grep LISTEN > /dev/null 2>&1; then
        echo "✅ ${SERVICES[$i]} (port ${PORTS[$i]}): 실행 중"
    else
        echo "❌ ${SERVICES[$i]} (port ${PORTS[$i]}): 실행 실패"
        LOG_FILE=""
        case ${SERVICES[$i]} in
            "Registry") LOG_FILE="logs/registry_new.log" ;;
            "Orchestrator") LOG_FILE="logs/orchestrator_v2_full.log" ;;
            "NLU") LOG_FILE="logs/nlu_v2_full.log" ;;
            "News") LOG_FILE="logs/news_v2_pure.log" ;;
            "Twitter") LOG_FILE="logs/twitter_v2_pure.log" ;;
            "SEC") LOG_FILE="logs/sec_v2_pure.log" ;;
            "Sentiment") LOG_FILE="logs/sentiment_v2_full.log" ;;
        esac
        if [ \! -z "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
            echo "   로그 확인: tail $LOG_FILE"
            tail -10 "$LOG_FILE"
        fi
    fi
done

echo ""
echo "🌐 Main UI: http://localhost:8100"
echo "📊 Registry Status: http://localhost:8001/status"
echo ""
echo "💡 시스템 종료: ./stop_v2.sh"
echo "📋 로그 확인: tail -f logs/*_full.log logs/*_pure.log logs/*_new.log"
EOF < /dev/null