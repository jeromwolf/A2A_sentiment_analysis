# A2A 기반 AI 투자 분석 시스템 (v2.5 - 최종 고도화 버전)

## 1. 프로젝트 개요

본 시스템은 다수의 전문 AI 에이전트가 서로 협력(Agent-to-Agent)하여, 사용자의 자연어 질문을 이해하고, **뉴스, 트위터(X), 기업 공시 자료** 등 여러 데이터 소스에서 실시간 정보를 종합적으로 수집한 뒤, 각 정보의 중요도에 따라 **가중치를 적용**하여 최종 투자 심리 점수를 산출하고, 이를 바탕으로 전문가 수준의 종합 분석 리포트를 생성하는 대화형 분석 시스템입니다.

---

## 2. 핵심 기능 및 아키텍처

### 주요 기능
- **다중 소스 교차 분석**: 뉴스(Finnhub), 소셜 미디어(Twitter), 기업 공시(SEC) 등 여러 채널의 정보를 종합하여 편향을 줄이고 정확도를 높입니다.
- **가중치 기반 점수 계산**: 각 데이터 소스의 신뢰도와 중요도에 따라 가중치(예: 공시 1.5, 뉴스 1.0, 트위터 0.7)를 적용하여 훨씬 더 정밀하고 현실적인 최종 점수를 산출합니다.
- **전문가 수준 리포트 생성**: 수집된 모든 정보와 최종 점수를 바탕으로, Gemini AI가 종합 의견, 긍정/부정 요인을 상세히 분석하는 전문가 수준의 리포트를 생성합니다.
- **대화형 인터페이스**: 사용자는 채팅을 통해 "애플 주가 어때?"와 같이 자연어로 질문할 수 있습니다.
- **병렬 데이터 처리**: 각 데이터 수집 에이전트가 동시에 정보를 수집하여 분석 속도를 최적화합니다.
- **안정적인 API 연동**: Finnhub, Twitter 등 신뢰도 높은 외부 API를 사용하여 안정적으로 데이터를 수집합니다.
- **유연한 설정**: `.env` 파일을 통해 모든 API 키와 분석할 기사 개수 등을 손쉽게 조정할 수 있습니다.

### 아키텍처 흐름
`사용자 질문` ➡ `UI` ➡ `오케스트레이터` ➡ `1. NLU 에이전트` ⬇︎

`오케스트레이터` ➡ **동시 호출** ➡ `2a. 뉴스 에이전트` & `2b. 트위터 에이전트` & `2c. 공시 에이전트` ⬇︎

`오케스트레이터` ➡ `3. 감정 분석 에이전트` ➡ `4. 점수 계산 에이전트 (가중치 적용)` ➡ `5. 리포트 생성 에이전트` ➡ `UI` ➡ `최종 리포트`

## 📂 디렉토리 구조  
/a2a_sentiment_analysis
├── agents/
│   ├── ... (에이전트 파일들)
├── .env                          (API 키 등 비밀 정보 관리 파일)
├── main_orchestrator.py
├── index.html
├── requirements.txt
├── start_all.sh
├── stop_all.sh
└── README.txt



## 3. 실행 환경 준비

### 1) API 키 발급 및 `.env` 파일 설정

- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey) 에서 키를 발급받습니다.
- **Finnhub API Key**: [Finnhub 사이트](https://finnhub.io/register)에 가입하고, 로그인 후 대시보드에서 API 키를 확인합니다.
- **Twitter(X) Bearer Token**: [Twitter 개발자 포털](https://developer.twitter.com/en/portal/dashboard)에서 앱을 생성하고 'Bearer Token'을 발급받습니다.
- **SEC API User-Agent**: 미국 증권거래위원회(SEC)는 API 요청 시 식별을 위해 `이름 이메일주소` 형식의 User-Agent를 요구합니다. (예: `JohnDoe johndoe@example.com`)

- 프로젝트 최상위 폴더에 **`.env`** 파일을 생성하고 아래 내용을 채웁니다.

Gemini API
GEMINI_API_KEY='발급받은_Gemini_API_키'

Finnhub API (뉴스)
FINNHUB_API_KEY='발급받은_Finnhub_API_키'

Twitter API v2 (소셜)
TWITTER_BEARER_TOKEN='발급받은_Twitter_Bearer_Token'

SEC EDGAR API (공시)
SEC_API_USER_AGENT='YourName YourEmail@example.com'

분석할 최대 기사/트윗 개수
MAX_ARTICLES_TO_SCRAPE=3


### 2) 필요 라이브러리 설치

터미널에서 아래 명령어를 실행합니다.
```bash
pip install -r requirements.txt

3) 스크립트 실행 권한 부여 (최초 1회)
macOS 또는 Linux 환경에서 아래 명령어를 실행합니다.

chmod +x start_all.sh stop_all.sh

4. 시스템 실행 및 종료
실행 방법
터미널에서 ./start_all.sh 명령어로 모든 에이전트 서버를 실행합니다.

웹 브라우저를 열고 주소창에 http://127.0.0.1:8000 을 입력하여 접속합니다.

채팅창에 분석하고 싶은 종목에 대해 질문합니다.

종료 방법
터미널