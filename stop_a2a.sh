#!/bin/bash
echo "🛑 A2A 분석 시스템을 종료합니다..."

# A2A 서비스 종료
pkill -f "service_registry:app"
pkill -f "nlu_agent_v2:app"
pkill -f "main_orchestrator_v2:app"

# 기존 서비스 종료
pkill -f "main_orchestrator:app"
pkill -f "nlu_agent:app"
pkill -f "advanced_data_agent:app"
pkill -f "twitter_agent:app"
pkill -f "sec_agent:app"
pkill -f "sentiment_analysis_agent:app"
pkill -f "score_calculation_agent:app"
pkill -f "report_generation_agent:app"

echo "✅ 모든 서비스가 종료되었습니다."