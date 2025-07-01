#!/bin/bash
echo "🚀 모든 A2A 분석 서버를 시작합니다..."
uvicorn main_orchestrator:app --port 8000 &
uvicorn agents.nlu_agent:app --port 8008 &
# 기존 뉴스 에이전트는 advanced_data_agent.py 파일을 사용합니다.
uvicorn agents.advanced_data_agent:app --port 8007 &
uvicorn agents.twitter_agent:app --port 8009 &
uvicorn agents.sec_agent:app --port 8010 &
uvicorn agents.sentiment_analysis_agent:app --port 8002 &
uvicorn agents.score_calculation_agent:app --port 8003 &
uvicorn agents.report_generation_agent:app --port 8004 &
echo "✅ 모든 서버가 백그라운드에서 실행 중입니다."