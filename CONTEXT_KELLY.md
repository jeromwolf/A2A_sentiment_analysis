# 켈리님 프로젝트 작업 컨텍스트

## 사용자 정보
- 이름: 켈리 (Kelly)
- 작업 시작일: 2025-07-18
- 최근 작업일: 2025-07-20
- 발표 예정일: 2025-07-24
- 발표 형식: 키노트 (Keynote)

## 프로젝트 개요
- Agent-to-Agent (A2A) 주식 감정 분석 시스템
- 여러 AI 에이전트가 협력하여 투자 분석 수행
- MCP (Model Context Protocol) 통합 진행 중

## 현재 상태 (2025-07-20 업데이트)

### 완료된 작업
1. A2A 통신 문제 해결
   - 에이전트 이름 매칭 문제 수정
   - 메시지 전송 실패 문제 해결
   - 디버깅 로그 추가 완료

2. 프로젝트 구조 정리 완료

3. 프레젠테이션 자료 대량 작성 (2025-07-20)
   - **a2a_mcp_architecture.html** - A2A + MCP 시스템 아키텍처
   - **a2a_core_components.html** - BaseAgent, Registry Server, Message Protocol
   - **a2a_code_example.html** - 코드 예제 (에이전트 정의, 메시지 전송/처리)
   - **a2a_deployment_flow.html** - 배포 플로우 (로컬→Docker→AWS)
   - **a2a_data_flow_updated.html** - 데이터 플로우와 Redis 캐싱
   - **a2a_smithery_style.html** ⭐ - 최종 통신 흐름 시각화 (Smithery.ai 스타일)

4. GIF 제작 가이드 작성
   - **kap_tutorial.html** - Kap 사용법 상세 가이드
   - 현재 Kap으로 애니메이션 녹화 진행 중

### a2a_smithery_style.html 주요 특징
- **7개 에이전트**: NLU, News, Twitter, SEC, Yahoo Finance, Sentiment, Report
- **애니메이션**: 빨간 점이 경로를 따라 이동하며 메시지 표시
- **메시지 예시**: "요청 분석", "AAPL", "뉴스 수집", "15건", "긍정 68%"
- **배경색**: #f8f9fa (밝은 회색)
- **속도**: 느리게 조정 (각 단계 4초, 전체 사이클 약 20-30초)
- **하단 정보**: 실시간 상태 표시 (Active Agents, Messages Sent, 현재 단계 설명)

### 진행 중인 작업
1. Kap으로 a2a_smithery_style.html 애니메이션 GIF 녹화
2. 7/24 발표 준비 최종 점검

### 예정된 작업
1. 실제 A2A 시스템 데모 준비
2. 프레젠테이션 통합 및 발표 순서 정리

## 변경된 파일 목록
- `.claude/settings.local.json`
- `a2a_core/base/base_agent.py`
- `agents/dart_agent_v2.py`
- `agents/mcp_data_agent.py`
- `agents/news_agent_v2_pure.py`
- `agents/sec_agent_v2_pure.py`
- `agents/twitter_agent_v2_pure.py`
- `main_orchestrator_v2.py`
- `presentation/` 폴더에 다수의 HTML 파일 추가

## 주요 포트 정보
- Registry Server: 8001
- Main Orchestrator: 8100
- NLU Agent: 8108
- News Agent: 8307
- Twitter Agent: 8209
- SEC Agent: 8210
- Sentiment Analysis: 8202
- Report Generation: 8204

## 중요 개념 정리
### AI Agent vs Agentic AI
- **AI Agent**: 특정 작업을 수행하는 독립적인 소프트웨어 개체
- **Agentic AI**: 자율성과 목표 지향성을 가진 AI 시스템의 특성/패러다임

### 기술 스택
- **Docker**: 컨테이너 가상화 플랫폼
- **AWS**: 클라우드 컴퓨팅 플랫폼
- **Kubernetes**: 컨테이너 오케스트레이션 (운영/관리)
- **Redis**: 캐싱 (TTL: Time To Live)
- **Gemini AI**: LLM for 감성 분석