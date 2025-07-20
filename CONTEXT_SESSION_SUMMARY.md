# 세션 컨텍스트 요약

## 사용자 정보
- 이름: 켈리 (Kelly)
- 발표 일정: 2025년 7월 24일
- 프로젝트: A2A 기반 투자 분석 시스템

## 작업 진행 상황

### 1. 완료된 주요 작업

#### A. A2A 프로토콜 관련 문서
- **A2A 5대 설계 원칙 문서** (`A2A_DESIGN_PRINCIPLES.md`)
  - Embrace Agentic Capabilities
  - Build on Web Standards  
  - Secure by Default
  - Support Long-Running Tasks
  - Modality Agnostic → Modality Independent (수정됨)

- **A2A Discovery 설명 자료** (`a2a_discovery_explained.html`)
  - 3가지 Discovery 방법: Well-Known URI, Curated Registry, Direct Config
  - Agent Registry 작동 방식
  - Ambient Signals 개념 설명

#### B. 프레젠테이션 자료
1. **Agentic AI 진화 설명** (`agentic_ai_evolution_presentation.html`)
   - AI Agent vs Agentic AI 차이점
   - 진화 단계별 설명

2. **Orchestrator-SEC Agent 통신 흐름**
   - Part 1 & 2로 나누어 제작
   - 화살표 위치 및 레이아웃 여러 차례 수정
   - 최종: `orchestrator_sec_flow_side_part1/2.html`

3. **MCP와 A2A 시너지 효과** (`mcp_a2a_synergy_final.html`)
   - 수직적 통합(MCP) vs 수평적 통합(A2A)
   - 벤다이어그램에서 분리형 디자인으로 변경
   - MCP/A2A 아키텍처 비교 다이어그램 추가

4. **A2A 5대 원칙 타임라인** (`a2a_5_principles_timeline.html`)
   - 흰색 배경, 한 페이지 버전
   - 키노트 프레젠테이션용 최적화

#### C. 멀티 에이전트 오케스트레이션 문서
- `MULTI_AGENT_ORCHESTRATION.md`
- Entry Point 선택, Loop 방지, Human Intervention 등

### 2. 기술적 이해 사항

#### A. A2A Protocol
- Google의 2025년 차세대 AI 에이전트 통신 표준
- Agent Discovery: 에이전트 능력 발견 메커니즘
- Remote Agent: Host Agent와 실제 작업 에이전트 사이의 중계 역할
- 양방향 통신 (Client + Server 역할 동시 수행)

#### B. MCP (Model Context Protocol)
- 개별 에이전트의 도구 접근 표준화
- Bloomberg, Refinitiv 등 프리미엄 데이터 소스 연동

#### C. 켈리님 프로젝트 특징
- A2A SDK 없이 FastAPI + asyncio로 직접 구현
- Registry 기반 에이전트 관리 (포트 8001)
- WebSocket 활용 실시간 업데이트
- 기관급 투자 분석을 개인 투자자에게 제공

### 3. 디자인 수정 이력

#### 주요 피드백 및 수정 사항
1. "화살표가 글자 위에 있어서 보기 안 좋아"
   → 화살표 위치를 박스 외부로 이동

2. "5번에 방향이 틀렸어"
   → Step 5 방향을 left에서 right로 수정

3. "바탕 라운드도 짤리고"
   → 컨테이너 패딩 및 border-radius 조정

4. "모달리티 무관 → 모달리티 독립"
   → 용어 변경

5. MCP/A2A 벤다이어그램 겹침 문제
   → 분리형 디자인 (MCP + A2A = SYNERGY)으로 변경

### 4. 현재 파일 구조
```
presentation/
├── agentic_ai_evolution_presentation.html
├── A2A_DESIGN_PRINCIPLES.md
├── MULTI_AGENT_ORCHESTRATION.md
├── orchestrator_sec_flow_side_part1.html
├── orchestrator_sec_flow_side_part2.html
├── a2a_5_principles_timeline.html
├── a2a_5_principles_creative.html
├── a2a_discovery_explained.html
├── mcp_a2a_synergy_final.html
└── [기타 버전들...]
```

### 5. 다음 세션 참고사항
- 모든 프레젠테이션은 키노트용 한 페이지 형식
- 가독성과 시각적 임팩트 중시
- 켈리님 프로젝트 예시 활용하여 설명
- 7/24 발표 준비 완료 필요

## 핵심 키워드
- A2A Protocol, MCP, Agent Discovery
- Orchestrator, Registry, WebSocket
- 수직적 통합 vs 수평적 통합
- Ambient Signals, Agent Card
- 멀티 에이전트 시스템