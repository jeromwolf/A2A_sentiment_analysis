#!/bin/bash

# 환경 변수 캐싱 모니터링 스크립트

echo "======================================================"
echo "환경 변수 캐싱 모니터링 스크립트"
echo "======================================================"

# 1. 현재 셸의 환경 변수 확인
echo -e "\n[1] 현재 셸의 환경 변수:"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "FINNHUB_API_KEY: ${FINNHUB_API_KEY:0:10}..."
echo "TWITTER_BEARER_TOKEN: ${TWITTER_BEARER_TOKEN:0:10}..."

# 2. 새로운 셸에서 환경 변수 확인
echo -e "\n[2] 새로운 셸에서 환경 변수 (source .env 없이):"
bash -c 'echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."'

# 3. dotenv로 로드된 환경 변수 확인
echo -e "\n[3] Python dotenv로 로드된 환경 변수:"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'GEMINI_API_KEY: {os.getenv(\"GEMINI_API_KEY\", \"NOT SET\")[:10]}...')
print(f'FINNHUB_API_KEY: {os.getenv(\"FINNHUB_API_KEY\", \"NOT SET\")[:10]}...')
print(f'TWITTER_BEARER_TOKEN: {os.getenv(\"TWITTER_BEARER_TOKEN\", \"NOT SET\")[:10]}...')
"

# 4. uvicorn 프로세스 확인
echo -e "\n[4] 실행 중인 uvicorn 프로세스:"
ps aux | grep uvicorn | grep -v grep | wc -l | xargs echo "실행 중인 프로세스 수:"

# 5. 프로세스별 환경 변수 확인 (macOS에서는 제한적)
echo -e "\n[5] 프로세스 환경 변수 확인 팁:"
echo "macOS에서는 다른 프로세스의 환경 변수를 직접 확인하기 어렵습니다."
echo "대신 다음 방법을 사용하세요:"
echo ""
echo "1. 각 에이전트에 환경 변수 확인 엔드포인트 추가:"
echo "   @app.get('/env-check')"
echo "   def check_env():"
echo "       return {'gemini_key_prefix': os.getenv('GEMINI_API_KEY', '')[:10]}"
echo ""
echo "2. 로그에 환경 변수 로드 상태 출력:"
echo "   logger.info(f'GEMINI_API_KEY loaded: {bool(os.getenv(\"GEMINI_API_KEY\"))}')"
echo ""
echo "3. 테스트 요청으로 확인:"
echo "   curl http://localhost:8202/env-check"

echo -e "\n======================================================"