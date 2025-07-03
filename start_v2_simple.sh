#!/bin/bash

echo "🚀 A2A V2 시스템 시작..."

# 레지스트리 없이 독립 실행 모드로 시작
export A2A_STANDALONE_MODE=true

# V2 오케스트레이터 시작
echo "1. Starting Main Orchestrator V2 (포트 8100)..."
nohup uvicorn main_orchestrator_v2:app --port 8100 --host 0.0.0.0 > orchestrator_v2.log 2>&1 &
sleep 2

# NLU 에이전트 (V1 사용)
echo "2. Starting NLU Agent (포트 8008)..."
nohup uvicorn agents.nlu_agent:app --port 8008 --host 0.0.0.0 > nlu.log 2>&1 &
sleep 1

# 뉴스 에이전트 V2
echo "3. Starting News Agent V2 (포트 8307)..."
nohup uvicorn agents.news_agent_v2_pure:app --port 8307 --host 0.0.0.0 > news_v2.log 2>&1 &
sleep 1

# 트위터 에이전트 V2
echo "4. Starting Twitter Agent V2 (포트 8209)..."
nohup uvicorn agents.twitter_agent_v2_pure:app --port 8209 --host 0.0.0.0 > twitter_v2.log 2>&1 &
sleep 1

# SEC 에이전트 V2
echo "5. Starting SEC Agent V2 (포트 8210)..."
nohup uvicorn agents.sec_agent_v2_pure:app --port 8210 --host 0.0.0.0 > sec_v2.log 2>&1 &
sleep 1

# 감정 분석 에이전트 V2
echo "6. Starting Sentiment Analysis V2 (포트 8202)..."
nohup uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --host 0.0.0.0 > sentiment_v2.log 2>&1 &
sleep 1

# 점수 계산 에이전트 V2
echo "7. Starting Score Calculation V2 (포트 8003)..."
nohup uvicorn agents.score_calculation_agent_v2:app --port 8003 --host 0.0.0.0 > score_v2.log 2>&1 &
sleep 1

# 리포트 생성 에이전트 V2
echo "8. Starting Report Generation V2 (포트 8004)..."
nohup uvicorn agents.report_generation_agent_v2:app --port 8004 --host 0.0.0.0 > report_v2.log 2>&1 &
sleep 1

# 정량적 분석 에이전트 V2
echo "9. Starting Quantitative Agent V2 (포트 8211)..."
nohup uvicorn agents.quantitative_agent_v2:app --port 8211 --host 0.0.0.0 > quantitative_v2.log 2>&1 &
sleep 1

# 리스크 분석 에이전트 V2
echo "10. Starting Risk Analysis V2 (포트 8212)..."
nohup uvicorn agents.risk_analysis_agent_v2:app --port 8212 --host 0.0.0.0 > risk_v2.log 2>&1 &

echo ""
echo "✅ V2 시스템 시작 완료!"
echo ""
echo "🌐 웹 UI 접속: http://localhost:8100"
echo ""
echo "📊 실행 상태 확인:"
ps aux | grep uvicorn | grep -v grep | wc -l | xargs echo "  - 실행 중인 에이전트 수:"
echo ""
echo "📋 로그 확인 명령어:"
echo "  tail -f orchestrator_v2.log"
echo "  tail -f news_v2.log"
echo "  tail -f sec_v2.log"
echo ""
echo "🛑 종료하려면: ./stop_all.sh"