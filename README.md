# A2A 기반 AI 투자 분석 시스템 (v3.0)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.0-4285F4.svg)](https://ai.google.dev/)

## 📋 프로젝트 개요

본 시스템은 다수의 전문 AI 에이전트가 서로 협력(Agent-to-Agent)하여, 사용자의 자연어 질문을 이해하고, **뉴스, 트위터(X), 기업 공시 자료** 등 여러 데이터 소스에서 실시간 정보를 종합적으로 수집한 뒤, 각 정보의 중요도에 따라 **가중치를 적용**하여 최종 투자 심리 점수를 산출하고, 이를 바탕으로 전문가 수준의 종합 분석 리포트를 생성하는 대화형 분석 시스템입니다.

## 🌟 핵심 기능

### 주요 특징
- **다중 소스 교차 분석**: 뉴스(Finnhub), 소셜 미디어(Twitter), 기업 공시(SEC) 등 여러 채널의 정보를 종합하여 편향을 줄이고 정확도를 높입니다.
- **가중치 기반 점수 계산**: 각 데이터 소스의 신뢰도와 중요도에 따라 가중치(예: 공시 1.5, 뉴스 1.0, 트위터 0.7)를 적용하여 훨씬 더 정밀하고 현실적인 최종 점수를 산출합니다.
- **전문가 수준 리포트 생성**: 수집된 모든 정보와 최종 점수를 바탕으로, Gemini AI가 종합 의견, 긍정/부정 요인을 상세히 분석하는 전문가 수준의 리포트를 생성합니다.
- **대화형 인터페이스**: 사용자는 채팅을 통해 "애플 주가 어때?"와 같이 자연어로 질문할 수 있습니다.
- **병렬 데이터 처리**: 각 데이터 수집 에이전트가 동시에 정보를 수집하여 분석 속도를 최적화합니다.
- **안정적인 API 연동**: Finnhub, Twitter 등 신뢰도 높은 외부 API를 사용하여 안정적으로 데이터를 수집합니다.
- **유연한 설정**: `.env` 파일을 통해 모든 API 키와 분석할 기사 개수 등을 손쉽게 조정할 수 있습니다.

## 🏗️ 아키텍처

### 시스템 흐름도
```
사용자 질문 ➡ UI ➡ 오케스트레이터 V2 ➡ 1. NLU 에이전트 ⬇︎

오케스트레이터 ➡ 동시 호출 ➡ 2a. 뉴스 에이전트 V2 & 2b. 트위터 에이전트 V2 & 2c. SEC 에이전트 V2 ⬇︎

오케스트레이터 ➡ 3. 감정 분석 에이전트 V2 ➡ 4. 정량적 분석 에이전트 V2 ➡ 5. 점수 계산 에이전트 V2 (가중치 적용) ⬇︎

오케스트레이터 ➡ 6. 리스크 분석 에이전트 V2 ➡ 7. 리포트 생성 에이전트 V2 ➡ UI ➡ 최종 HTML 리포트
```

### 에이전트 포트 구성
| 에이전트 | 포트 | 역할 |
|---------|------|------|
| Main Orchestrator V2 | 8100 | 전체 시스템 조율 및 UI 제공 |
| NLU Agent | 8008 | 자연어 처리 및 티커 추출 |
| News Agent V2 | 8307 | Finnhub/NewsAPI를 통한 뉴스 데이터 수집 |
| Twitter Agent V2 | 8209 | 트위터 감정 데이터 수집 |
| SEC Agent V2 | 8210 | SEC EDGAR API를 통한 공시 데이터 수집 |
| Sentiment Analysis V2 | 8202 | Gemini AI를 활용한 감정 분석 |
| Quantitative Agent V2 | 8211 | 정량적 데이터 분석 (가격, 기술적 지표) |
| Score Calculation V2 | 8003 | 가중치 기반 점수 계산 |
| Risk Analysis Agent V2 | 8212 | 리스크 평가 |
| Report Generation V2 | 8004 | HTML 형식의 전문 투자 보고서 생성 |

## 📂 디렉토리 구조
```
/a2a_sentiment_analysis
├── agents/                    # 전문 AI 에이전트들
│   ├── __init__.py
│   ├── nlu_agent.py          # 자연어 이해 에이전트
│   ├── data_agent_v2_adapter.py    # 데이터 에이전트 어댑터 (V2)
│   ├── news_agent_v2_pure.py       # 뉴스 데이터 수집 (V2)
│   ├── twitter_agent_v2_pure.py    # 트위터 데이터 수집 (V2)
│   ├── sec_agent_v2_pure.py        # SEC 공시 데이터 수집 (V2)
│   ├── sentiment_analysis_agent_v2.py  # 감정 분석 (V2)
│   ├── quantitative_agent_v2.py    # 정량적 분석 (V2)
│   ├── score_calculation_agent_v2.py   # 점수 계산 (V2)
│   ├── risk_analysis_agent_v2.py   # 리스크 분석 (V2)
│   └── report_generation_agent_v2.py   # 리포트 생성 (V2)
├── .env                      # API 키 설정 (git에서 제외)
├── .gitignore               # Git 제외 파일 목록
├── main_orchestrator_v2.py  # 메인 조율자 (V2)
├── index_v2.html           # 웹 UI (V2)
├── requirements.txt        # Python 패키지 목록
├── start_all.sh           # 전체 시스템 시작 스크립트
├── stop_all.sh            # 전체 시스템 종료 스크립트
├── CLAUDE.md              # Claude Code 가이드
├── test_v2_*.py           # 테스트 파일들
└── README.md              # 프로젝트 설명서 (현재 파일)
```

## 🚀 실행 환경 준비

### 1) 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git

### 2) API 키 발급 및 `.env` 파일 설정

각 서비스의 API 키를 발급받아야 합니다:

- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)에서 키를 발급받습니다.
- **Finnhub API Key**: [Finnhub 사이트](https://finnhub.io/register)에 가입하고, 로그인 후 대시보드에서 API 키를 확인합니다.
- **Twitter(X) Bearer Token**: [Twitter 개발자 포털](https://developer.twitter.com/en/portal/dashboard)에서 앱을 생성하고 'Bearer Token'을 발급받습니다.
- **SEC API User-Agent**: 미국 증권거래위원회(SEC)는 API 요청 시 식별을 위해 `이름 이메일주소` 형식의 User-Agent를 요구합니다.

프로젝트 최상위 폴더에 **`.env`** 파일을 생성하고 아래 내용을 채웁니다:

```env
# Gemini API
GEMINI_API_KEY='발급받은_Gemini_API_키'

# Finnhub API (뉴스)
FINNHUB_API_KEY='발급받은_Finnhub_API_키'

# Twitter API v2 (소셜)
TWITTER_BEARER_TOKEN='발급받은_Twitter_Bearer_Token'

# SEC EDGAR API (공시)
SEC_API_USER_AGENT='YourName YourEmail@example.com'

# 분석할 최대 기사/트윗 개수
MAX_ARTICLES_TO_SCRAPE=3
```

### 3) 필요 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 4) 스크립트 실행 권한 부여 (최초 1회)

macOS 또는 Linux 환경에서:
```bash
chmod +x start_all.sh stop_all.sh
```

## 💻 시스템 실행 및 종료

### 실행 방법
1. 터미널에서 `./start_all.sh` 명령어로 모든 에이전트 서버를 실행합니다.
2. 웹 브라우저를 열고 주소창에 `http://127.0.0.1:8100`을 입력하여 접속합니다.
3. 채팅창에 분석하고 싶은 종목에 대해 질문합니다.
   - 예시: "애플 주가 어때?", "테슬라 투자 심리 분석해줘", "NVDA 리스크 분석해줘"

### 종료 방법
터미널에서 `./stop_all.sh` 명령어를 실행하면 모든 에이전트가 종료됩니다.

## 🔧 개발자를 위한 정보

### 개별 에이전트 테스트
```bash
# 특정 에이전트만 실행 (예: NLU 에이전트)
uvicorn agents.nlu_agent:app --port 8008 --reload

# API 테스트
curl -X POST http://localhost:8008/extract_ticker \
  -H "Content-Type: application/json" \
  -d '{"query": "애플 주가 어때?"}'
```

### 로그 확인
각 에이전트는 콘솔에 로그를 출력합니다. 더 자세한 로깅이 필요한 경우 Python의 `logging` 모듈을 활용하여 파일로 저장할 수 있습니다.

## 📊 가중치 시스템

데이터 소스별 신뢰도에 따른 가중치:
- **기업 공시 (SEC)**: 1.5 (가장 신뢰도 높음)
- **뉴스**: 1.0 (표준)
- **트위터**: 0.7 (변동성 높음)

## 📈 버전 3.0 업데이트 내역

### 새로운 기능
- **A2A v2 프로토콜**: 이벤트 기반 비동기 통신으로 성능 향상
- **정량적 분석 에이전트**: 가격 데이터 및 기술적 지표 분석 추가
- **리스크 분석 에이전트**: 종합적인 리스크 평가 및 권고사항 생성
- **향상된 감정 분석**: Gemini 2.0 Flash를 활용한 더 정확한 분석
- **HTML 보고서**: 시각적으로 개선된 전문 투자 분석 보고서

### 개선 사항
- 병렬 처리 최적화로 분석 속도 30% 향상
- 에러 처리 강화 및 폴백 메커니즘 추가
- 실시간 진행 상황 업데이트 개선
- 한글 번역 기능 강화 (키워드 기반)

### 예정된 업데이트
- SEC 공시 내용 상세 분석 기능
- 전문 번역 API 통합 (Google Translate/DeepL)
- 데이터 출처 URL 및 타임스탬프 표시
- 과거 데이터 기반 트렌드 분석

## 🤝 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙏 감사의 말

- Google Gemini AI팀
- Finnhub, Twitter, SEC API 제공팀
- FastAPI 개발팀

---

**문의사항이나 버그 리포트는 [Issues](https://github.com/jeromwolf/A2A_sentiment_analysis/issues) 탭을 이용해주세요.**