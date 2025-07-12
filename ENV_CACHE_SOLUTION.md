# 환경 변수 캐싱 문제 해결 가이드

## 문제 상황
uvicorn 프로세스들이 이전에 캐싱된 환경 변수를 사용하여 새로운 API 키가 반영되지 않는 문제

## 해결 방법

### 1. 즉시 해결 (Quick Fix)
```bash
# 모든 프로세스 종료
./stop_all.sh

# 환경 변수 검증 및 프로세스 재시작
python3 verify_env_and_restart.py

# 서비스 재시작
./start_v2_complete.sh
```

### 2. 단계별 해결 방법

#### Step 1: 실행 중인 프로세스 확인 및 종료
```bash
# 프로세스 확인
ps aux | grep -E 'uvicorn|python.*agent' | grep -v grep

# 모든 관련 프로세스 종료
pkill -f uvicorn
pkill -f "python.*agent"
```

#### Step 2: 환경 변수 확인
```bash
# .env 파일 확인
cat .env | grep -E 'GEMINI|FINNHUB|TWITTER|SEC'

# 현재 셸의 환경 변수 확인
echo $GEMINI_API_KEY
```

#### Step 3: 환경 변수 재로드
```bash
# 기존 환경 변수 제거
unset GEMINI_API_KEY FINNHUB_API_KEY TWITTER_BEARER_TOKEN

# 새로 로드
source .env
# 또는 Python에서
python3 -c "from dotenv import load_dotenv; load_dotenv(override=True)"
```

#### Step 4: 서비스 재시작
```bash
# 전체 재시작
./start_v2_complete.sh

# 또는 개별 에이전트 시작
uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --reload
```

## 검증 방법

### 1. 환경 변수 로딩 테스트
```bash
python3 test_env_loading.py
```

### 2. API 키 유효성 확인
```python
# Gemini API 테스트
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Test")
print(response.text)
```

### 3. 에이전트별 환경 변수 확인
각 에이전트에 다음 엔드포인트 추가:
```python
@app.get("/env-check")
def check_env():
    return {
        "gemini_key_loaded": bool(os.getenv('GEMINI_API_KEY')),
        "finnhub_key_loaded": bool(os.getenv('FINNHUB_API_KEY')),
        "twitter_token_loaded": bool(os.getenv('TWITTER_BEARER_TOKEN'))
    }
```

테스트:
```bash
curl http://localhost:8202/env-check
```

## 예방 조치

### 1. 에이전트 시작 시 환경 변수 확인
```python
# 각 에이전트의 시작 부분에 추가
import os
from dotenv import load_dotenv

# 환경 변수 강제 재로드
load_dotenv(override=True)

# 필수 환경 변수 확인
required_vars = ['GEMINI_API_KEY', 'FINNHUB_API_KEY']
for var in required_vars:
    if not os.getenv(var):
        logger.error(f"Required environment variable {var} is not set!")
        raise ValueError(f"Missing required environment variable: {var}")
```

### 2. 로깅 추가
```python
# 환경 변수 로드 상태 로깅
logger.info(f"GEMINI_API_KEY loaded: {bool(os.getenv('GEMINI_API_KEY'))}")
logger.info(f"API key prefix: {os.getenv('GEMINI_API_KEY', '')[:10]}...")
```

### 3. 프로세스 관리 개선
```bash
# stop_all.sh 개선
#!/bin/bash
echo "Stopping all services..."

# 더 강력한 종료
pkill -9 -f uvicorn
pkill -9 -f "python.*agent"

# 포트 확인
lsof -i :8100-8300 | grep LISTEN

echo "All services stopped"
```

## 주의사항

1. **캐싱 문제**: uvicorn의 `--reload` 옵션을 사용해도 환경 변수는 자동으로 재로드되지 않음
2. **프로세스 격리**: 각 uvicorn 프로세스는 독립적인 환경 변수 공간을 가짐
3. **macOS 제한**: macOS에서는 다른 프로세스의 환경 변수를 직접 확인하기 어려움

## 권장 워크플로우

1. `.env` 파일 수정
2. `./stop_all.sh` 실행
3. `python3 verify_env_and_restart.py` 실행
4. `./start_v2_complete.sh` 실행
5. 브라우저에서 http://localhost:8100 접속하여 테스트