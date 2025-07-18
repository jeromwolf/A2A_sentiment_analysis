
# A2A 감성 분석 시스템 구성 요소

## 🏗️ 시스템 계층 구조

### 1️⃣ 클라이언트 계층
| 구성 요소 | 포트 | 역할 |
|----------|------|------|
| Web UI | 8100 | 사용자 인터페이스 |

### 2️⃣ 오케스트레이션 계층
| 구성 요소 | 포트 | 역할 |
|----------|------|------|
| Main Orchestrator | 8100 | 전체 워크플로우 조정 |
| Registry Server | 8001 | 에이전트 등록/발견 |

### 3️⃣ 데이터 수집 계층
| 에이전트 | 포트 | 역할 | 외부 API |
|---------|------|------|----------|
| NLU Agent | 8108 | 티커 심볼 추출 | Gemini AI |
| News Agent | 8307 | 뉴스 데이터 수집 | Finnhub |
| Twitter Agent | 8209 | 소셜 데이터 수집 | Twitter API v2 |
| SEC Agent | 8210 | 공시 자료 수집 | SEC EDGAR |

### 4️⃣ 분석 처리 계층
| 에이전트 | 포트 | 역할 | 가중치 |
|---------|------|------|--------|
| Sentiment Analysis | 8202 | 감성 분석 | - |
| Quantitative Analysis | 8211 | 기술적 분석 | - |
| Score Calculation | 8203 | 점수 계산 | SEC: 1.5, News: 1.0, Twitter: 0.7 |
| Risk Analysis | 8212 | 리스크 평가 | - |

### 5️⃣ 출력 계층
| 에이전트 | 포트 | 역할 |
|---------|------|------|
| Report Generation | 8204 | HTML/PDF 보고서 생성 |

## 📊 처리 흐름

1. **사용자 입력** → Web UI
2. **티커 추출** → NLU Agent가 자연어에서 주식 심볼 추출
3. **데이터 수집** → 4개 에이전트가 병렬로 데이터 수집
4. **감성 분석** → 수집된 데이터를 AI로 분석
5. **점수 계산** → 소스별 가중치 적용하여 종합 점수 산출
6. **리스크 평가** → 투자 리스크 분석
7. **보고서 생성** → 최종 투자 분석 보고서 작성

## 🔗 주요 특징

- **병렬 처리**: 데이터 수집 단계에서 모든 에이전트가 동시 실행
- **가중치 시스템**: 데이터 소스의 신뢰도에 따른 차별화된 가중치
- **다중 LLM 지원**: OpenAI, Gemini, Ollama 선택 가능
- **실시간 업데이트**: WebSocket을 통한 진행 상황 실시간 전달
