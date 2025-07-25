# 🚀 A2A 투자 분석 시스템 - 빠른 시작 가이드

이 가이드는 A2A 투자 분석 시스템을 5분 안에 실행할 수 있도록 도와드립니다.

## 📋 사전 준비사항

- Python 3.8 이상
- Git
- 웹 브라우저 (Chrome, Firefox, Safari 등)

## 🔧 설치 단계

### 1️⃣ 프로젝트 다운로드
```bash
git clone https://github.com/jeromwolf/A2A_sentiment_analysis.git
cd A2A_sentiment_analysis
```

### 2️⃣ Python 가상환경 설정 (권장)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 4️⃣ 환경 설정 파일 생성
프로젝트 루트 폴더에 `.env` 파일을 생성하고 아래 내용을 입력:

```env
# 최소 필수 설정 (이것만 있어도 실행 가능)
GEMINI_API_KEY=your_gemini_api_key_here
USE_MOCK_DATA=true  # API 키가 없을 때 더미 데이터 사용

# 실제 데이터를 원한다면 아래 API 키들도 추가
FINNHUB_API_KEY=your_finnhub_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
SEC_API_USER_AGENT=YourName your@email.com
```

> 💡 **빠른 테스트를 원한다면**: `USE_MOCK_DATA=true`로 설정하면 API 키 없이도 시스템을 테스트할 수 있습니다.

### 5️⃣ 시스템 실행
```bash
# Windows
python scripts/start_v2_complete.py

# macOS/Linux
chmod +x scripts/start_v2_complete.sh
./scripts/start_v2_complete.sh
```

### 6️⃣ 웹 브라우저에서 접속
브라우저를 열고 다음 주소로 접속:
```
http://localhost:8100
```

## 💬 사용 방법

1. 채팅창에 분석하고 싶은 종목을 자연어로 입력
   - "애플 주가 어때?"
   - "테슬라 투자 전망 분석해줘"
   - "삼성전자 리스크 평가해줘"

2. AI가 다음 정보를 분석합니다:
   - 📰 최신 뉴스
   - 💬 소셜 미디어 반응
   - 📊 기업 공시 자료
   - 📈 기술적 지표

3. 분석 완료 후:
   - 종합 투자 점수 확인
   - 상세 분석 리포트 열람
   - PDF로 저장 가능

## 🛑 시스템 종료

```bash
# Windows
Ctrl + C (터미널에서)

# macOS/Linux
./scripts/stop_all.sh
```

## ❓ 자주 묻는 질문

### Q: "포트가 이미 사용 중입니다" 오류
```bash
# 사용 중인 포트 확인 및 종료
# Windows
netstat -ano | findstr :8100
taskkill /PID [프로세스ID] /F

# macOS/Linux
lsof -i :8100
kill -9 [프로세스ID]
```

### Q: API 키는 어디서 받나요?
- **Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey) (무료)
- **Finnhub**: [Finnhub](https://finnhub.io/register) (무료 플랜 있음)
- **Twitter**: [Twitter Developer](https://developer.twitter.com/) (승인 필요)

### Q: "ModuleNotFoundError" 오류
```bash
# 가상환경이 활성화되었는지 확인
# 의존성 재설치
pip install --upgrade pip
pip install -r requirements.txt
```

### Q: 분석이 느려요
- 여러 AI 에이전트가 동시에 작동하므로 초기 분석은 30-60초 정도 소요됩니다
- 두 번째 분석부터는 캐싱으로 더 빨라집니다

## 📞 도움이 필요하신가요?

- 📖 [전체 문서](README.md)
- 🐛 [이슈 리포트](https://github.com/jeromwolf/A2A_sentiment_analysis/issues)
- 💬 [디스커션](https://github.com/jeromwolf/A2A_sentiment_analysis/discussions)

---

**🎉 축하합니다! 이제 AI 투자 분석 시스템을 사용할 준비가 되었습니다.**