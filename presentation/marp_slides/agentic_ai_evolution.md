---
marp: true
theme: default
paginate: true
---

# Agentic AI의 진화

## LLM에서 Agentic AI로의 발전 과정

### 다양한 AI 패러다임의 등장과 진화

---

# AI 기술 발전 로드맵

## 각 단계별 핵심 특징

```
┌─────────────────────────────────────────────────┐
│                  Agentic AI 발전                  │
└─────────────────────────────────────────────────┘
                        ↑
    ┌───────────────────┴───────────────────┐
    │                                       │
   LLM                                     A2A
    │                                       │
+ 완투시네이션 보완                      + 다양한 AI Agent간 안전하고
+ 내부 문서 검색                          상호운용 가능한 통신 지원
    │                                       │
    │                                    + 프레임워크나 벤더에 관계없이
    │                                      에이전트 간 연결 가능
    │                                       │
   RAG                                    MCP
    │                                       │
+ 최신 자료 검색                        + 도구들의 표준 프로토콜
  (검색 도구가 필요해)                  + tool calling 라우팅 부분
    │                                      막음 (동적라우팅)
+ 답이 있을때까지 여러번                    │
  프롬프트 loop                            │
  (ReAct 프레임워크)                       │
    └───────────────┬───────────────────────┘
                    ↓
                  Agent
```

---

# LLM: 시작점

## Large Language Model의 한계와 도전

### 강점
- ✅ 자연어 이해 및 생성
- ✅ 광범위한 지식 보유
- ✅ 다양한 작업 수행 가능

### 한계
- ❌ **환루시네이션**: 존재하지 않는 정보 생성
- ❌ **최신 정보 부족**: 학습 데이터 시점 제한
- ❌ **내부 문서 접근 불가**: 조직 특화 지식 부재

### 💡 해결 방안
→ **RAG** (Retrieval-Augmented Generation) 도입

---

# RAG: 검색 강화 생성

## LLM의 한계를 극복하는 첫 단계

### 핵심 개념
```python
# RAG 프로세스
def rag_process(query):
    # 1. 관련 문서 검색
    relevant_docs = vector_db.search(query)
    
    # 2. 컨텍스트 생성
    context = format_context(relevant_docs)
    
    # 3. LLM에 전달
    response = llm.generate(
        prompt=f"Context: {context}\nQuestion: {query}"
    )
    return response
```

### 특징
- 🔍 **최신 자료 검색**: 실시간 정보 접근
- 🔄 **ReAct 프레임워크**: 답을 찾을 때까지 반복
- 📚 **내부 문서 활용**: 조직 지식 통합

---

# Agent: 자율적 AI

## RAG를 넘어선 능동적 AI 시스템

### Agent의 핵심 능력
1. **목표 설정**: 주어진 작업을 스스로 분해
2. **도구 사용**: 필요한 도구를 선택하고 활용
3. **의사 결정**: 상황에 따른 판단
4. **반복 실행**: 목표 달성까지 지속

### 예시: 투자 분석 Agent
```python
class InvestmentAgent:
    async def analyze(self, ticker):
        # 1. 데이터 수집 도구 선택
        tools = self.select_tools(["news", "finance", "social"])
        
        # 2. 병렬로 데이터 수집
        data = await self.collect_data(ticker, tools)
        
        # 3. 분석 및 의사결정
        analysis = await self.analyze_data(data)
        
        # 4. 리포트 생성
        return await self.generate_report(analysis)
```

---

# MCP: 도구의 표준화

## Model Context Protocol - AI와 도구의 연결 고리

### MCP가 해결하는 문제
- ❌ **도구별 다른 인터페이스**
- ❌ **동적 라우팅의 어려움**
- ❌ **통합 관리의 복잡성**

### MCP의 해결책
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "database_query",
    "arguments": {"query": "SELECT * FROM stocks"}
  }
}
```

### 장점
- ✅ **표준 프로토콜**: 모든 도구가 같은 방식
- ✅ **동적 라우팅**: 실시간 도구 선택
- ✅ **쉬운 통합**: 플러그 앤 플레이

---

# A2A: 에이전트 간 협업

## Agent-to-Agent Protocol - 멀티 에이전트의 시대

### A2A가 가능하게 하는 것
- 🤝 **다양한 AI Agent간 안전한 통신**
- 🔄 **상호운용 가능한 통신 지원**
- 🌐 **프레임워크/벤더 독립적**

### 실제 구현 예시
```python
# 여러 전문 에이전트의 협업
async def collaborative_analysis(ticker):
    # 각 에이전트가 전문 분야 담당
    tasks = [
        news_agent.analyze_sentiment(ticker),
        quant_agent.analyze_technicals(ticker),
        risk_agent.assess_risk(ticker)
    ]
    
    # 병렬 실행 후 통합
    results = await asyncio.gather(*tasks)
    return integrate_results(results)
```

### 특징
- ✅ **도시 교통 시스템처럼 자율주행차가 서로 통신**
- ✅ **주차장/충전소 정보 실시간 공유**
- ✅ **전체 시스템 최적화**

---

# 통합 아키텍처

## LLM → RAG → Agent → MCP/A2A

### 진화의 정점: Agentic AI

```
                    Agentic AI
                        │
        ┌───────────────┴───────────────┐
        │                               │
       MCP                             A2A
        │                               │
   도구 표준화                    에이전트 협업
        │                               │
        └───────────────┬───────────────┘
                        │
                     Agent
                        │
                   자율적 실행
                        │
                      RAG
                        │
                   검색 강화
                        │
                      LLM
                        │
                   언어 이해
```

### 🎯 우리 프로젝트
**LLM** (Gemini) + **RAG** (뉴스/SEC) + **Agent** (11개) + **MCP** (금융도구) + **A2A** (협업)

---