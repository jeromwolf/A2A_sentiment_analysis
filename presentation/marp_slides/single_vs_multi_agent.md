---
marp: true
theme: default
paginate: true
---

# 단일 에이전트 vs 멀티 에이전트 시스템

## AI 에이전트 아키텍처의 진화

### 복잡성과 성능의 균형점 찾기

---

# 단일 에이전트의 한계와 멀티 에이전트 시스템의 필요성

## 두 가지 접근법 비교

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
  <div style="border: 3px solid #FF9500; padding: 30px; border-radius: 10px; background: #FFF5E6;">
    <h3 style="color: #FF9500; margin-top: 0;">AI 에이전트 기술 발전</h3>
    <ul>
      <li>단일 에이전트의 작업 범위 및 복잡성 → 명확한 한계 직면</li>
    </ul>
  </div>
  
  <div style="border: 3px solid #007AFF; padding: 30px; border-radius: 10px; background: #E6F2FF;">
    <h3 style="color: #007AFF; margin-top: 0;">멀티 에이전트 시스템</h3>
    <ul>
      <li>단일 에이전트 한계 극복 및 복잡·정교한 형상 문제 해결 필요</li>
      <li>멀티 에이전트 시스템 필요성 대두<br/>(MAS: Multi-Agent System)</li>
    </ul>
  </div>
</div>

## 단일 AI 에이전트의 주요 한계점

### 📊 주요 한계 영역

1. **일반화부족** (단일작업에만 최적화, 작업커버리지 한계 및 일반화 어려움)
2. **신뢰성부족** (에이전트 능력이 향상될수록 사용자 신뢰도 업, 예) 의료, 금융, 개인통신, 중요 의사결정 등)
3. **확장성문제** (작업 복잡성 증가 시 컴퓨팅 리소스 기하급수적 증가)
4. **견고성부족** (예상치 못한 상황 직면 시 취약성 노출 및 실패 가능성, 강력한 학습 및 적응 능력 부재)

---

# 멀티 에이전트 시스템이 등장 배경

## 🎯 핵심 동기

### 여러 자율적인 에이전트가 상호작용하고 협력하는 시스템

단일 에이전트로는 해결하기 어렵거나 불가능한 복잡한 문제를 해결하도록 고안한 시스템

### 각 에이전트는 특정 기술이나 전문 지식 보유
공동의 목표를 달성하기 위해 정보 공유 및 협력 수행

### 단일 에이전트의 본질적 한계를 극복
보다 지능적이고 효율적인 문제 해결 접근법 모색

---

# 멀티 에이전트 시스템의 주요 이점

## 🚀 6가지 핵심 장점

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px;">
  <div style="border: 2px solid #007AFF; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #007AFF;">01. 문제 해결 능력 및 효율성</h4>
    <p>복잡한 작업: 관리 가능 단위로 분해<br/>
    → 여러 전문 에이전트에 작업 분산<br/>
    각 에이전트는 할당된 작업에만 집중<br/>
    → 성능 향상 + 병렬 처리 : 해결 시간 단축</p>
  </div>
  
  <div style="border: 2px solid #FF9500; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #FF9500;">02. 유연성 및 적응성</h4>
    <p>변화하는 조건에 신속 적응<br/>
    문제 해결에 대한 미묘한 접근 가능<br/>
    환경이나 업무 변화 시, 시스템 전체적으로<br/>
    약간의 코드 변경/조정을 통해 대응 가능</p>
  </div>
  
  <div style="border: 2px solid #5856D6; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #5856D6;">03. 확장성</h4>
    <p>새로운 에이전트 추가 및<br/>
    기존 에이전트 수정 용이<br/>
    전체 시스템 중단 없이 scale out<br/>
    형태로 확장 가능</p>
  </div>
  
  <div style="border: 2px solid #34C759; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #34C759;">04. 견고성 및 내결함성</h4>
    <p>분산 시스템 특성으로<br/>
    단일 시스템보다 내결함성 우수</p>
  </div>
  
  <div style="border: 2px solid #FF3B30; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #FF3B30;">05. 도메인 특화 에이전트의 전문성 활용</h4>
    <p>다양한 전문 지식을 가진 에이전트<br/>
    강점 결합 → 다면적 문제 효과적 해결</p>
  </div>
  
  <div style="border: 2px solid #AF52DE; padding: 20px; border-radius: 10px; background: white;">
    <h4 style="color: #AF52DE;">06. 향상된 의사결정 구조</h4>
    <p>여러 전문 에이전트 통찰력 결합<br/>
    광범위한 요소/시나리오 고려<br/>
    강력/미묘한 지식 기반의 의사결정</p>
  </div>
</div>

---

# 멀티 에이전트 시스템 활용 분야 및 전망

## 🌍 실제 적용 분야

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
  <div>
    <h3 style="color: #FF3B30;">멀티 에이전트 시스템 활용 분야</h3>
    <h4>광범위한 활용 분야</h4>
    <ul>
      <li>도시 계획, 글로벌 공급망 관리, 금융 시장 분석, 위험 평가</li>
      <li>제조 : 의료 : 국방 등 다양한 산업에서 복잡 문제 해결 도구로 부상</li>
    </ul>
    
    <h4 style="color: #007AFF;">멀티 에이전트 시스템 전망</h4>
    <h4>에이전트 간 협업의 힘</h4>
    <ul>
      <li>여러 지능형 전문 에이전트의 추론 능력 결합과 협업</li>
      <li>더욱 복잡하고 다단계적 워크플로우 처리를 위한 상당한 잠금 방식</li>
    </ul>
  </div>
  
  <div style="text-align: center;">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgNDAwIj4KICAgPGNpcmNsZSBjeD0iMjAwIiBjeT0iNTAiIHI9IjMwIiBmaWxsPSIjMDA3QUZGIiBvcGFjaXR5PSIwLjgiLz4KICAgPGNpcmNsZSBjeD0iMTAwIiBjeT0iMTUwIiByPSIzMCIgZmlsbD0iI0ZGOTUwMCIgb3BhY2l0eT0iMC44Ii8+CiAgIDxjaXJjbGUgY3g9IjMwMCIgY3k9IjE1MCIgcj0iMzAiIGZpbGw9IiNGRkQ2MEEiIG9wYWNpdHk9IjAuOCIvPgogICA8Y2lyY2xlIGN4PSI3MCIgY3k9IjI1MCIgcj0iMjUiIGZpbGw9IiNGRjNDQzciIG9wYWNpdHk9IjAuNiIvPgogICA8Y2lyY2xlIGN4PSIxNTAiIGN5PSIyNTAiIHI9IjI1IiBmaWxsPSIjRkY5Q0NGIiBvcGFjaXR5PSIwLjYiLz4KICAgPGNpcmNsZSBjeD0iMjUwIiBjeT0iMjUwIiByPSIyNSIgZmlsbD0iI0ZGOUNDRiIgb3BhY2l0eT0iMC42Ii8+CiAgIDxjaXJjbGUgY3g9IjMzMCIgY3k9IjI1MCIgcj0iMjUiIGZpbGw9IiNGRkQ2MEEiIG9wYWNpdHk9IjAuNiIvPgogICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjM1MCIgcj0iMjAiIGZpbGw9IiNGRjlDQ0YiIG9wYWNpdHk9IjAuNCIvPgogICA8Y2lyY2xlIGN4PSIxMjAiIGN5PSIzNTAiIHI9IjIwIiBmaWxsPSIjRkY5Q0NGIiBvcGFjaXR5PSIwLjQiLz4KICAgPGNpcmNsZSBjeD0iMjAwIiBjeT0iMzUwIiByPSIyMCIgZmlsbD0iI0ZGOTVBMCIgb3BhY2l0eT0iMC42Ij4KICAgICAgPGltYWdlIHg9IjE4NSIgeT0iMzM1IiB3aWR0aD0iMzAiIGhlaWdodD0iMzAiIGhyZWY9ImRhdGE6aW1hZ2Uvc3ZnK3htbDtiYXNlNjQsUEhOMlp5QjRiV3h1Y3owaWFIUjBjRG92TDNkM2R5NTNNeTV2Y21jdk1qQXdNQzl6ZG1jaUlIWnBaWGRDYjNnOUlqQWdNQ0F4TmpBZ01UWXdJajQ4ZEdWNGRDQjRQU0k0TUNJZ2VUMGlPREFpSUdadmJuUXRjMmw2WlQwaU5EQWlJR1pwYkd3OUlpTXpNek1pSUhSbGVIUXRZVzVqYUc5eVBTSnRhV1JrYkdVaVBzclBvOytqendsMFpYaDBQand2YzNablBnPT0iLz4KICAgPC9jaXJjbGU+CiAgIDxjaXJjbGUgY3g9IjI4MCIgY3k9IjM1MCIgcj0iMjAiIGZpbGw9IiNGRjlDQ0YiIG9wYWNpdHk9IjAuNCIvPgogICA8Y2lyY2xlIGN4PSIzNTAiIGN5PSIzNTAiIHI9IjIwIiBmaWxsPSIjRkY5Q0NGIiBvcGFjaXR5PSIwLjQiLz4KICAgCiAgIDwhLS0gQ29ubmVjdGluZyBsaW5lcyAtLT4KICAgPGxpbmUgeDE9IjIwMCIgeTE9IjgwIiB4Mj0iMTAwIiB5Mj0iMTIwIiBzdHJva2U9IiNGRjNDQzciIHN0cm9rZS13aWR0aD0iMiIgb3BhY2l0eT0iMC42Ii8+CiAgIDxsaW5lIHgxPSIyMDAiIHkxPSI4MCIgeDI9IjMwMCIgeTI9IjEyMCIgc3Ryb2tlPSIjRkZENjBBIiBzdHJva2Utd2lkdGg9IjIiIG9wYWNpdHk9IjAuNiIvPgogICA8bGluZSB4MT0iMTAwIiB5MT0iMTgwIiB4Mj0iNzAiIHkyPSIyMjAiIHN0cm9rZT0iI0ZGM0NDNyIgc3Ryb2tlLXdpZHRoPSIyIiBvcGFjaXR5PSIwLjQiLz4KICAgPGxpbmUgeDE9IjEwMCIgeTE9IjE4MCIgeDI9IjE1MCIgeTI9IjIyMCIgc3Ryb2tlPSIjRkY5Q0NGIiBzdHJva2Utd2lkdGg9IjIiIG9wYWNpdHk9IjAuNCIvPgogICA8bGluZSB4MT0iMzAwIiB5MT0iMTgwIiB4Mj0iMjUwIiB5Mj0iMjIwIiBzdHJva2U9IiNGRkQ2MEEiIHN0cm9rZS13aWR0aD0iMiIgb3BhY2l0eT0iMC40Ii8+CiAgIDxsaW5lIHgxPSIzMDAiIHkxPSIxODAiIHgyPSIzMzAiIHkyPSIyMjAiIHN0cm9rZT0iI0ZGRDYwQSIgc3Ryb2tlLXdpZHRoPSIyIiBvcGFjaXR5PSIwLjQiLz4KPC9zdmc+" alt="Multi-Agent Network" style="max-width: 100%; height: auto;"/>
    <p style="font-style: italic; color: #666;">멀티 에이전트 네트워크 구조</p>
  </div>
</div>

---

# 단일 vs 멀티 에이전트: 실제 사례

## 💼 투자 분석 시스템 비교

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
  <div style="border: 3px solid #FF3B30; padding: 30px; border-radius: 10px; background: #FFF0F0;">
    <h3 style="color: #FF3B30; margin-top: 0;">❌ 단일 에이전트 접근법</h3>
    <pre style="background: #f5f5f7; padding: 15px; border-radius: 8px;">
# 하나의 거대한 AI가 모든 것을 처리
class InvestmentAnalyzer:
    def analyze(self, ticker):
        # 1. 뉴스 수집 (5초)
        news = self.collect_news(ticker)
        
        # 2. 소셜 미디어 분석 (3초)
        social = self.analyze_social(ticker)
        
        # 3. 재무 데이터 (2초)
        financial = self.get_financials(ticker)
        
        # 4. 감성 분석 (4초)
        sentiment = self.analyze_all(
            news, social, financial
        )
        
        # 5. 리포트 생성 (2초)
        return self.generate_report(sentiment)
        
# 총 소요시간: 16초 (순차 처리)
# 문제: 한 부분 실패 시 전체 실패
    </pre>
  </div>
  
  <div style="border: 3px solid #34C759; padding: 30px; border-radius: 10px; background: #F0FFF0;">
    <h3 style="color: #34C759; margin-top: 0;">✅ 멀티 에이전트 접근법</h3>
    <pre style="background: #f5f5f7; padding: 15px; border-radius: 8px;">
# 전문화된 에이전트들이 협업
class OrchestratorAgent:
    async def analyze(self, ticker):
        # 병렬로 전문 에이전트 호출
        tasks = await asyncio.gather(
            news_agent.collect(ticker),      # 5초
            social_agent.analyze(ticker),     # 3초
            financial_agent.fetch(ticker),    # 2초
            return_exceptions=True  # 부분 실패 허용
        )
        
        # 수집된 데이터로 분석
        sentiment = await sentiment_agent.analyze(
            tasks
        )  # 4초
        
        # 최종 리포트
        return await report_agent.generate(
            sentiment
        )  # 2초
        
# 총 소요시간: 11초 (병렬 처리)
# 장점: 부분 실패해도 나머지는 동작
    </pre>
  </div>
</div>

### 🏆 성능 비교
- **처리 시간**: 16초 → 11초 (31% 단축)
- **안정성**: 전체 실패 → 부분 실패 허용
- **확장성**: 어려움 → 새 에이전트 추가 용이

---

# 멀티 에이전트 시스템 구현 패턴

## 🏗️ 주요 아키텍처 패턴

### 1. 계층적 구조 (Hierarchical)
```
         [Orchestrator]
              |
    ┌─────────┼─────────┐
    ↓         ↓         ↓
[Agent A] [Agent B] [Agent C]
```
- **특징**: 중앙 조정자가 작업 분배
- **장점**: 명확한 제어 흐름
- **단점**: 중앙 집중식 병목

### 2. P2P 구조 (Peer-to-Peer)
```
[Agent A] ←→ [Agent B]
    ↑  ↘   ↙  ↑
    ↓    ↗↖    ↓
[Agent C] ←→ [Agent D]
```
- **특징**: 에이전트 간 직접 통신
- **장점**: 유연성, 확장성
- **단점**: 복잡한 조정

### 3. 하이브리드 구조
```
     [Main Orchestrator]
           |
    ┌──────┴──────┐
[Sub-Orch1]   [Sub-Orch2]
    |              |
[Team A]       [Team B]
```
- **특징**: 계층적 + P2P 혼합
- **장점**: 균형잡힌 접근
- **우리 프로젝트**: 이 방식 채택

---

# 멀티 에이전트 시스템의 도전 과제

## ⚠️ 극복해야 할 주요 과제

### 1. 조정 및 통신 복잡성
- **문제**: 에이전트 수 증가 시 통신 오버헤드 기하급수적 증가
- **해결**: 효율적인 메시지 라우팅, 이벤트 기반 통신

### 2. 일관성 및 동기화
- **문제**: 분산 환경에서 데이터 일관성 유지 어려움
- **해결**: 분산 트랜잭션, 이벤트 소싱

### 3. 확장성 관리
- **문제**: 에이전트 증가 시 성능 저하
- **해결**: 로드 밸런싱, 동적 스케일링

### 4. 디버깅 및 모니터링
- **문제**: 분산 시스템 디버깅의 어려움
- **해결**: 분산 추적, 중앙화된 로깅

### 5. 보안 및 신뢰
- **문제**: 에이전트 간 신뢰 관계 구축
- **해결**: 인증/인가 메커니즘, 암호화 통신

---

# 미래 전망: 에이전트 생태계

## 🔮 멀티 에이전트 시스템의 미래

### 2025-2027: 도입기
- **표준화**: A2A, MCP 등 프로토콜 성숙
- **도구 발전**: 개발/운영 도구 생태계 확대
- **초기 채택**: 선도 기업들의 프로덕션 적용

### 2028-2030: 성장기
- **대중화**: 중소기업까지 확산
- **플랫폼화**: Agent-as-a-Service 등장
- **자율성 증가**: 더 똑똑한 에이전트

### 2030년 이후: 성숙기
- **표준 아키텍처**: 멀티 에이전트가 기본
- **초지능 협업**: 인간-AI-AI 협업 일상화
- **새로운 패러다임**: 컴퓨팅의 근본적 변화

### 🎯 핵심 메시지
> **"단일 에이전트의 시대는 끝났다.**
> **미래는 협업하는 AI 에이전트들의 생태계다."**

---