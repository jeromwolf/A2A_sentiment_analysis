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
- **전문가 수준 리포트 생성**: 수집된 모든 정보와 최종 점수를 바탕으로, AI가 종합 의견, 긍정/부정 요인을 상세히 분석하는 전문가 수준의 리포트를 생성합니다.
- **대화형 인터페이스**: 사용자는 채팅을 통해 "애플 주가 어때?"와 같이 자연어로 질문할 수 있습니다.
- **병렬 데이터 처리**: 각 데이터 수집 에이전트가 동시에 정보를 수집하여 분석 속도를 최적화합니다.
- **안정적인 API 연동**: Finnhub, Twitter 등 신뢰도 높은 외부 API를 사용하여 안정적으로 데이터를 수집합니다.
- **유연한 설정**: `.env` 파일을 통해 모든 API 키와 분석할 기사 개수 등을 손쉽게 조정할 수 있습니다.

### 🆕 v3.0 신규 기능
- **선택 가능한 LLM 지원**: Gemini, Gemma3(로컬), OpenAI 중 선택하여 사용 가능
  - 환경변수 `LLM_PROVIDER`를 통해 런타임에 LLM 선택
  - Ollama를 통한 로컬 모델(Gemma3) 지원
  - 자동 폴백 메커니즘으로 안정성 확보
- **정량적 분석 강화**: 실시간 주가, RSI, MACD 등 기술적 지표 분석
  - yfinance를 통한 무료 실시간 데이터 수집
  - 기술적 지표 자동 계산 및 분석
  - API 장애 시 모의 데이터 폴백
- **리스크 분석 추가**: 시장 리스크, 기업 고유 리스크, 유동성 리스크 등 종합 평가
  - 정량적/정성적 데이터 통합 분석
  - 리스크 점수 및 권고사항 생성
- **SEC 실시간 데이터**: SEC EDGAR API를 통한 실제 공시 데이터 파싱
- **향상된 보고서**: 증권사 수준의 전문적인 투자 분석 보고서 생성

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
├── index_v2.html           # 웹 UI (PDF 내보내기 기능 포함)
├── requirements.txt        # Python 패키지 목록
├── .env                    # API 키 설정 (git에서 제외)
└── agents.json            # 에이전트 설정 파일
```

### 🤖 시스템 에이전트 (A2A 프로토콜 기반)
```
agents/
├── __init__.py
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
├── __init__.py
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

### 🧪 테스트
```
tests/
├── __init__.py
├── conftest.py                     # pytest 설정
├── unit/                           # 단위 테스트
│   ├── __init__.py
│   ├── test_base_agent.py
│   ├── test_message_protocol.py
│   ├── test_nlu_agent_v2.py
│   └── test_service_registry.py
├── integration/                    # 통합 테스트
│   ├── __init__.py
│   └── test_a2a_integration.py
├── test_data_collection.py         # 데이터 수집 테스트
├── test_gemini_api.py              # Gemini API 테스트
├── test_nlu_capability.py          # NLU 에이전트 테스트
├── test_pdf_export.py              # PDF 내보내기 테스트
├── test_pdf_generation.py          # PDF 생성 테스트
├── test_sec_agent.py               # SEC 에이전트 테스트
├── test_v2_investment.py           # 투자 분석 테스트
├── test_v2_system.py               # V2 시스템 통합 테스트
├── test_v2_workflow.py             # 워크플로우 테스트
└── test_websocket_v2.py            # WebSocket 연결 테스트
```

### 🚀 실행 스크립트
```
├── start_v2_complete.sh       # 완전 시스템 시작 (모든 에이전트)
├── stop_all.sh               # 모든 시스템 종료
├── run_tests.sh              # 테스트 실행 스크립트
└── check_v2_agents.py        # 에이전트 상태 확인
```

### 📚 문서
```
├── README.md                # 프로젝트 설명서 (현재 파일)
├── CLAUDE.md               # Claude Code 가이드
├── A2A_PROTOCOL_GUIDE.md   # A2A 프로토콜 가이드
├── A2A_프로토콜_발표자료.md  # A2A 프로토콜 발표 자료
├── PDF_EXPORT_GUIDE.md     # PDF 내보내기 가이드
├── TEST_GUIDE.md           # 테스트 가이드 (정량적 지표 평가 방법 포함)
├── A2A 분석 시스템 상품화 최종 로드맵.txt  # 상품화 로드맵
└── architecture_docs/      # 시스템 아키텍처 문서
    ├── README.md           # 아키텍처 문서 가이드
    ├── architecture_table.md  # 시스템 구조 테이블
    ├── architecture_diagram.html  # 인터랙티브 다이어그램
    └── ...                # 기타 다이어그램 파일들
```

### 🔧 기타 파일
```
├── .gitignore              # Git 무시 파일 목록
├── .claude/                # Claude Code 설정
│   └── settings.local.json
└── htmlcov/                # 코드 커버리지 리포트 (자동 생성)
```

## 🚀 실행 환경 준비

### 1) 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git

### 최근 업데이트 (2025-07-03)
- **데이터 수집 문제 해결**: A2A 메시지 프로토콜에서 HTTP 직접 호출 방식으로 변경
- **UI 개선**: 투자 심리 점수 텍스트 가독성 대폭 향상 (흰색, 굵은 글씨, 그림자 효과)
- **프로젝트 구조 정리**:
  - 불필요한 셸 스크립트 제거 (start_all.sh 등 중복 파일 삭제)
  - 테스트 파일들을 tests/ 폴더로 이동
  - 중복 HTML 파일 제거 (index_with_pdf.html - index_v2.html에 PDF 기능 통합)
- **문서 업데이트**: CLAUDE.md 스크립트 경로 수정

### 2) API 키 발급 및 `.env` 파일 설정

각 서비스의 API 키를 발급받아야 합니다:

- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)에서 키를 발급받습니다.
- **Finnhub API Key**: [Finnhub 사이트](https://finnhub.io/register)에 가입하고, 로그인 후 대시보드에서 API 키를 확인합니다.
- **Twitter(X) Bearer Token**: [Twitter 개발자 포털](https://developer.twitter.com/en/portal/dashboard)에서 앱을 생성하고 'Bearer Token'을 발급받습니다.
- **SEC API User-Agent**: 미국 증권거래위원회(SEC)는 API 요청 시 식별을 위해 `이름 이메일주소` 형식의 User-Agent를 요구합니다.

프로젝트 최상위 폴더에 **`.env`** 파일을 생성하고 아래 내용을 채웁니다:

```env
# A2A API Key for authentication
A2A_API_KEY=your-secure-api-key-here

# LLM 설정
LLM_PROVIDER=gemini  # 옵션: gemini, gemma3, openai
GEMINI_API_KEY='발급받은_Gemini_API_키'
GEMMA3_MODEL_PATH=/path/to/gemma3/model  # Gemma3 로컬 모델 경로
OPENAI_API_KEY=  # OpenAI 사용 시

# Finnhub API (뉴스)
FINNHUB_API_KEY='발급받은_Finnhub_API_키'

# Twitter API v2 (소셜)
TWITTER_BEARER_TOKEN='발급받은_Twitter_Bearer_Token'

# SEC EDGAR API (공시)
SEC_API_USER_AGENT='YourName YourEmail@example.com'

# 데이터 수집 설정
MAX_NEWS_PER_SOURCE=5     # 각 뉴스 소스별 최대 건수
MAX_TOTAL_NEWS=10        # 전체 뉴스 최대 건수
MAX_SEC_FILINGS=20       # SEC 공시 최대 건수

# Redis 캐싱 설정 (선택사항)
CACHE_ENABLED=true        # 캐싱 활성화
REDIS_URL=redis://localhost:6379  # Redis 연결 URL
CACHE_TTL=3600           # 기본 캐시 유효시간 (초)
```

### 3) LLM 설정 (선택사항)

#### Gemini (기본값)
별도 설치 없이 API 키만 설정하면 사용 가능합니다.

#### Gemma3 (로컬 모델)
```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서비스 시작
ollama serve

# Gemma3 모델 다운로드
ollama pull gemma3

# Python 클라이언트 설치
pip install ollama
```

#### OpenAI
```bash
pip install openai
```

### 4) 필요 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 5) 스크립트 실행 권한 부여 (최초 1회)

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
- **LLM 통합 관리**: 다양한 LLM 제공자를 런타임에 선택 가능
  - Gemini (Google AI), Gemma3 (로컬), OpenAI 지원
  - 통합 LLM Manager를 통한 일관된 인터페이스
  - 자동 폴백 메커니즘으로 서비스 안정성 향상
- **정량적 분석 에이전트**: 가격 데이터 및 기술적 지표 분석 추가
  - yfinance를 통한 실시간 주가 데이터 수집
  - RSI, MACD, 볼린저 밴드 등 기술적 지표 계산
  - API 장애 시 모의 데이터로 자동 전환
- **리스크 분석 에이전트**: 종합적인 리스크 평가 및 권고사항 생성
  - 시장 리스크, 기업 리스크, 유동성 리스크 분석
  - 정량적 지표와 정성적 데이터 통합 평가
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
- 오케스트레이터 흐름 개선: 모든 분석 단계가 순차적으로 실행되도록 수정

### 최근 수정 사항 (2025-07-13)
- **프로젝트 구조 정리**
  - 아키텍처 문서를 `architecture_docs/` 폴더로 정리
  - 테스트 관련 파일을 `test_files/` 폴더로 정리
  - 검토가 필요한 파일들을 `files_to_review/` 폴더로 이동
- **TEST_GUIDE.md 업데이트**
  - 정량적 지표 평가 가이드 섹션 추가
  - RSI, MACD, PER, 목표주가 해석 방법 상세 설명
  - 투자 판단 기준 및 실전 활용 예시 포함
### 이전 수정 사항 (2025-07-13)
- **실시간 주가 데이터 연동**
  - Yahoo Finance API 대신 Finnhub API로 전환
  - Tesla 등 실제 주가 데이터 표시 ($313.51)
  - API rate limit 문제 해결
- **목표주가 계산 기능 추가**
  - 증권사 수준의 목표주가 산정 로직 구현
  - PER Multiple (성장주 보정), Technical Analysis 등 다양한 방법론 적용
  - 평균 목표주가, 중간값, 상승여력 계산 및 투자의견 제시
- **UI 개선**
  - 목표주가 섹션 추가 (평균 $357, 상승여력 +14.0%)
  - 산정 방법론별 상세 내역 표시
  - Report Generation Agent의 데이터 매핑 오류 수정

### 이전 수정 사항 (2025-07-12)
- **보안 기능 추가**
  - API Key 기반 인증 시스템 구현
  - 모든 에이전트 엔드포인트에 X-API-Key 헤더 인증 필수
  - .env 파일에 A2A_API_KEY 설정 추가
  - FastAPI Security 의존성을 통한 일관된 인증 처리
- **환경 변수 관리 개선**
  - 중복된 환경 변수 정의 제거
  - ConfigManager를 통한 중앙화된 설정 관리
  - dotenv 로드 프로세스 최적화
- **Redis 캐싱 시스템 구현**
  - 분석 결과 캐싱으로 응답 속도 대폭 개선
  - 티커 추출, 감정 분석 등 주요 작업 캐싱
  - 캐시 관리 API 제공 (통계, 삭제, 무효화)
  - TTL 기반 자동 만료 설정

### 이전 수정 사항 (2025-07-08)
- **감정 분석 타임아웃 처리 개선**
  - AI 분석이 시간 초과되어도 기본 점수(-0.3 ~ -0.5)로 진행
  - 분석 프로세스가 중단되지 않고 계속 진행되도록 개선
- **Yahoo Finance API 429 에러 방지**
  - 정량적 분석 시 2초 지연 추가로 API 요청 제한 회피
  - Too Many Requests 에러 방지
- **Ollama (Gemma3) 연결 오류 수정**
  - generate 메서드 호출 시 키워드 인수 사용으로 수정
  - `self.client.generate(model=self.model_name, prompt=prompt)` 형식으로 변경
- **보고서 표시 개선**
  - 뉴스 항목 표시 개수: 2개 → 5개로 증가
  - 감정 분류: 실제 점수 기반으로 정확히 계산
  - 색상 구분 개선: 중립 색상을 주황색에서 회색으로 변경
  - SEC 공시: 점수 기준으로 정렬 (부정적인 것부터)

### 예정된 업데이트
- SEC 공시 내용 상세 분석 기능
- 전문 번역 API 통합 (Google Translate/DeepL)
- 데이터 출처 URL 및 타임스탬프 표시
- 과거 데이터 기반 트렌드 분석
- Docker 컨테이너화 및 쿠버네티스 배포
- 실시간 데이터 스트리밍 (WebSocket)
- 다중 사용자 지원 및 세션 관리

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