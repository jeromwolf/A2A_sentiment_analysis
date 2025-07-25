# 🔧 A2A 투자 분석 시스템 - 트러블슈팅 가이드

## 🚨 일반적인 문제와 해결 방법

### 1. 설치 관련 문제

#### ❌ `pip install -r requirements.txt` 실패
```bash
# 해결방법 1: pip 업그레이드
python -m pip install --upgrade pip

# 해결방법 2: 캐시 삭제 후 재설치
pip cache purge
pip install -r requirements.txt

# 해결방법 3: 개별 패키지 설치
pip install fastapi uvicorn aiohttp beautifulsoup4 yfinance
```

#### ❌ Python 버전 오류
```bash
# Python 버전 확인
python --version

# Python 3.8 이상이 필요합니다
# pyenv 사용자의 경우
pyenv install 3.8.10
pyenv local 3.8.10
```

### 2. 실행 관련 문제

#### ❌ "포트가 이미 사용 중입니다" 오류
```bash
# Windows
netstat -ano | findstr :8100
taskkill /PID [프로세스ID] /F

# macOS/Linux
lsof -i :8100
kill -9 [프로세스ID]

# 모든 관련 포트 확인 (8001, 8100, 8108, 8202 등)
lsof -i :8001,8100,8108,8202,8203,8204,8209,8210,8211,8212
```

#### ❌ "에이전트를 찾을 수 없습니다" 오류
```bash
# Registry Server가 실행 중인지 확인
curl http://localhost:8001/agents

# 개별 에이전트 상태 확인
curl http://localhost:8108/health  # NLU Agent
curl http://localhost:8202/health  # Sentiment Agent
```

#### ❌ WebSocket 연결 실패
```javascript
// 브라우저 콘솔에서 확인
// F12 → Console 탭
WebSocket connection to 'ws://localhost:8100/ws' failed

// 해결방법:
// 1. 방화벽/보안 소프트웨어 확인
// 2. 브라우저 확장 프로그램 비활성화
// 3. 다른 브라우저로 시도
```

### 3. API 관련 문제

#### ❌ "Invalid API Key" 오류
```bash
# .env 파일 확인
cat .env

# 올바른 형식 예시:
GEMINI_API_KEY='AIzaSy...'  # 따옴표 포함
FINNHUB_API_KEY='c8n3...'   # 따옴표 포함

# 환경변수 직접 확인
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

#### ❌ API Rate Limit 초과
```python
# 증상: 429 Too Many Requests 오류

# 해결방법:
# 1. .env 파일에서 수집 데이터 수 줄이기
MAX_NEWS_PER_SOURCE=3  # 5에서 3으로 감소
MAX_TOTAL_NEWS=5       # 10에서 5로 감소

# 2. Mock 데이터 모드 사용
USE_MOCK_DATA=true
```

#### ❌ SEC API 오류
```bash
# SEC는 User-Agent를 요구합니다
# .env 파일에 다음 형식으로 설정:
SEC_API_USER_AGENT='John Doe john.doe@email.com'
```

### 4. 분석 관련 문제

#### ❌ "NLU 에이전트가 티커를 인식하지 못합니다"
```python
# 지원되는 형식:
"애플 주가 어때?"        # ✅ 한국어 기업명
"AAPL 분석해줘"         # ✅ 티커 심볼
"Apple 투자 전망"       # ✅ 영어 기업명

# 지원되지 않는 형식:
"과일 회사 분석"        # ❌ 모호한 표현
"빅테크 전망"          # ❌ 구체적 기업명 없음
```

#### ❌ 감성 분석 타임아웃
```bash
# 증상: "Sentiment analysis timed out" 메시지

# 해결방법:
# 1. Gemini API 상태 확인
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'

# 2. 타임아웃 설정 증가 (agents/sentiment_analysis_agent_v2.py)
timeout = aiohttp.ClientTimeout(total=60)  # 30에서 60으로 증가
```

### 5. UI/UX 관련 문제

#### ❌ 차트가 표시되지 않음
```javascript
// 브라우저 콘솔 확인 (F12)
// Chart.js 관련 오류 확인

// 해결방법:
// 1. 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
// 2. 하드 리프레시 (Ctrl+Shift+R)
// 3. 광고 차단기 비활성화
```

#### ❌ PDF 저장 실패
```bash
# 브라우저 팝업 차단 확인
# Chrome: 주소창 오른쪽 팝업 차단 아이콘 클릭 → 허용

# 대안: 브라우저 인쇄 기능 사용
# Ctrl+P → PDF로 저장 선택
```

### 6. 성능 관련 문제

#### ❌ 분석이 너무 느림
```bash
# 1. 동시 실행 에이전트 수 확인
ps aux | grep python | grep agent | wc -l

# 2. Redis 캐싱 활성화 (.env)
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379

# 3. Redis 설치 및 실행
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

#### ❌ 메모리 사용량 과다
```bash
# 프로세스별 메모리 확인
ps aux | grep python | sort -k4 -r | head -10

# 불필요한 에이전트 종료
./scripts/stop_all.sh
./scripts/start_minimal_agents.sh  # 최소 구성으로 실행
```

## 🆘 긴급 복구

### 전체 시스템 초기화
```bash
# 1. 모든 프로세스 종료
./scripts/stop_all.sh
pkill -f uvicorn
pkill -f python

# 2. 포트 정리
lsof -ti:8001,8100,8108,8202,8203,8204,8209,8210,8211,8212 | xargs kill -9

# 3. 캐시 삭제
rm -rf __pycache__
rm -rf .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# 4. 가상환경 재생성
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. 시스템 재시작
./scripts/start_v2_complete.sh
```

## 📝 로그 확인 방법

### 실시간 로그 모니터링
```bash
# 메인 오케스트레이터 로그
tail -f orchestrator.log

# 특정 에이전트 로그 (예시)
tail -f nlu_agent.log
tail -f sentiment_analysis.log

# 모든 로그 동시 확인
tail -f *.log
```

### 디버그 모드 실행
```python
# main_orchestrator_v2.py 수정
import logging
logging.basicConfig(level=logging.DEBUG)

# 또는 환경변수 설정
export LOG_LEVEL=DEBUG
```

## 🔍 추가 진단 도구

### 시스템 상태 체크 스크립트
```bash
# check_system.py 생성
import requests
import asyncio

async def check_agents():
    agents = {
        "Registry": "http://localhost:8001/health",
        "Orchestrator": "http://localhost:8100/health",
        "NLU": "http://localhost:8108/health",
        "Sentiment": "http://localhost:8202/health",
    }
    
    for name, url in agents.items():
        try:
            resp = requests.get(url, timeout=5)
            status = "✅ OK" if resp.status_code == 200 else f"❌ {resp.status_code}"
        except:
            status = "❌ Offline"
        print(f"{name}: {status}")

asyncio.run(check_agents())
```

## 💡 예방 조치

1. **정기적인 백업**
   ```bash
   # .env 파일 백업
   cp .env .env.backup
   ```

2. **API 키 로테이션**
   - 3개월마다 API 키 갱신
   - 여러 API 키 준비 (폴백용)

3. **리소스 모니터링**
   ```bash
   # 시스템 리소스 확인
   htop  # 또는 top
   ```

## 📞 추가 지원

해결되지 않는 문제가 있다면:

1. [GitHub Issues](https://github.com/jeromwolf/A2A_sentiment_analysis/issues)에 문제 보고
2. 다음 정보 포함:
   - 오류 메시지 전체
   - Python 버전 (`python --version`)
   - OS 정보
   - .env 설정 (API 키 제외)
   - 재현 단계

---

**💡 팁**: 대부분의 문제는 API 키 설정이나 포트 충돌로 인해 발생합니다. 이 두 가지를 먼저 확인하세요!