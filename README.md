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
| Registry Server | 8001 | A2A 서비스 레지스트리 |
| Main Orchestrator | 8100 | 전체 시스템 조율 및 UI 제공 |
| NLU Agent | 8108 | 자연어 처리 및 티커 추출 |
| News Agent | 8307 | Finnhub/NewsAPI를 통한 뉴스 데이터 수집 |
| Twitter Agent | 8209 | 트위터 감정 데이터 수집 |
| SEC Agent | 8210 | SEC EDGAR API를 통한 공시 데이터 수집 |
| Sentiment Analysis | 8202 | Gemini AI를 활용한 감정 분석 |
| Quantitative Agent | 8211 | 정량적 데이터 분석 (가격, 기술적 지표) |
| Score Calculation | 8203 | 가중치 기반 점수 계산 |
| Risk Analysis Agent | 8212 | 리스크 평가 |
| Report Generation | 8204 | HTML 형식의 전문 투자 보고서 생성 |

## 📂 디렉토리 구조

### 🏗️ 핵심 시스템 파일
```
/a2a_sentiment_analysis
├── main_orchestrator_v2.py  # 메인 조율자 (포트 8100) - A2A 프로토콜 기반
├── index_v2.html           # 웹 UI
├── index_with_pdf.html     # PDF 내보내기 지원 UI
├── requirements.txt        # Python 패키지 목록
├── .env                    # API 키 설정 (git에서 제외)
└── agents.json            # 에이전트 설정 파일
```

### 🤖 시스템 에이전트 (A2A 프로토콜 기반)
```
agents/
├── nlu_agent_v2.py                 # 자연어 이해 (포트 8108)
├── news_agent_v2_pure.py           # 뉴스 데이터 수집 (포트 8307)
├── twitter_agent_v2_pure.py        # 트위터 데이터 수집 (포트 8209)
├── sec_agent_v2_pure.py            # SEC 공시 데이터 수집 (포트 8210)
├── sentiment_analysis_agent_v2.py  # 감정 분석 (포트 8202)
├── quantitative_agent_v2.py        # 정량적 분석 (포트 8211)
├── score_calculation_agent_v2.py   # 점수 계산 (포트 8203)
├── risk_analysis_agent_v2.py       # 리스크 분석 (포트 8212)
└── report_generation_agent_v2.py   # 리포트 생성 (포트 8204)
```

### 🔧 A2A 프레임워크 (V2 전용)
```
a2a_core/
├── base/
│   ├── __init__.py
│   └── base_agent.py               # 기본 에이전트 클래스
├── protocols/
│   ├── __init__.py
│   └── message.py                  # A2A 메시지 프로토콜
└── registry/
    ├── __init__.py
    ├── service_registry.py         # 서비스 레지스트리
    └── registry_server.py          # 레지스트리 서버
```

### 🧪 테스트 및 유틸리티
```
├── check_v2_agents.py          # 에이전트 상태 확인
├── test_gemini_api.py          # Gemini API 테스트
├── test_nlu_capability.py      # NLU 기능 테스트
├── test_pdf_export.py          # PDF 내보내기 테스트
├── test_pdf_generation.py      # PDF 생성 테스트
├── test_sec_agent.py           # SEC 에이전트 테스트
├── test_v2_investment.py       # V2 투자 분석 테스트
├── test_v2_system.py           # V2 시스템 테스트
├── test_v2_workflow.py         # V2 워크플로우 테스트
├── test_websocket_v2.py        # WebSocket V2 테스트
├── tests/                      # 단위 테스트 디렉토리
│   ├── unit/                   # 단위 테스트
│   └── integration/            # 통합 테스트
└── run_tests.sh               # 테스트 실행 스크립트
```

### 🚀 실행 스크립트
```
├── start_all.sh              # 시스템 시작 (기본)
├── start_v2_complete.sh       # 완전 시스템 시작 (모든 에이전트)
├── stop_all.sh               # 모든 시스템 종료
└── stop_v2.sh                # 시스템 종료
```

### 📊 로그 및 보고서
```
├── logs/                     # 시스템 로그 파일들
│   ├── orchestrator_v2.log   # 메인 오케스트레이터 로그
│   ├── registry.log          # 레지스트리 서버 로그
│   ├── nlu_v2.log           # NLU 에이전트 로그
│   ├── news_v2_pure.log     # 뉴스 에이전트 로그
│   ├── twitter_v2_pure.log  # 트위터 에이전트 로그
│   ├── sec_v2_pure.log      # SEC 에이전트 로그
│   ├── sentiment_v2.log     # 감정 분석 로그
│   ├── quantitative_v2.log  # 정량적 분석 로그
│   ├── score_calc_v2.log    # 점수 계산 로그
│   ├── risk_v2.log          # 리스크 분석 로그
│   └── report_gen_v2.log    # 리포트 생성 로그
└── reports/pdf/             # PDF 보고서 저장 폴더
```

### 📚 문서
```
├── README.md                # 프로젝트 설명서 (현재 파일)
├── CLAUDE.md               # Claude Code 가이드
├── A2A_PROTOCOL_GUIDE.md   # A2A 프로토콜 가이드
├── PDF_EXPORT_GUIDE.md     # PDF 내보내기 가이드
└── TEST_GUIDE.md           # 테스트 가이드
```

## 🚀 실행 환경 준비

### 1) 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git

### 최근 업데이트 (2025-07-03)
- 데이터 수집 문제 해결: HTTP 직접 호출 방식으로 변경
- UI 개선: 투자 심리 점수 텍스트 가독성 향상
- 불필요한 셸 스크립트 정리

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
chmod +x start_v2_complete.sh stop_all.sh
```

## 💻 시스템 실행 및 종료

### 실행 방법

#### 시스템 시작
```bash
# 실행 권한 부여 (최초 1회)
chmod +x start_v2_complete.sh stop_all.sh

# 시스템 시작
./start_v2_complete.sh

# 웹 브라우저에서 접속
http://localhost:8100
```

#### 사용 방법
채팅창에 분석하고 싶은 종목에 대해 질문합니다:
- 예시: "애플 주가 어때?", "테슬라 투자 심리 분석해줘", "NVDA 리스크 분석해줘"

### 종료 방법
터미널에서 `./stop_all.sh` 명령어를 실행하면 모든 에이전트가 종료됩니다.

## 🔧 개발자를 위한 정보

### 개별 에이전트 테스트
```bash
# 특정 에이전트만 실행 (예: NLU 에이전트)
uvicorn agents.nlu_agent_v2:app --port 8108 --reload

# API 테스트
curl -X POST http://localhost:8108/extract_ticker \
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
- **PDF 저장 기능**: 브라우저 인쇄 기능을 통한 PDF 저장 지원

### 개선 사항
- 병렬 처리 최적화로 분석 속도 30% 향상
- 에러 처리 강화 및 폴백 메커니즘 추가
- 실시간 진행 상황 업데이트 개선
- 한글 번역 기능 강화 (키워드 기반)
- V2 에이전트 안정성 개선 (빈 데이터 처리 로직 강화)
- UI 개선: 점수 표시 색상 구분 및 프린트 스타일 최적화

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