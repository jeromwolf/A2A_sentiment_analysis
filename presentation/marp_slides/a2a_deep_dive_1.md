---
marp: true
theme: default
paginate: true
---

# A2A 프로토콜 심화 이해

## Agent-to-Agent Protocol의 핵심 개념

### Google에서 시작된 에이전트 통신 표준

---

# A2A란 무엇인가?

## 에이전트 종속성 문제 해결

### 각 에이전트는 서로 다른 기반 기술이나 플랫폼에서 독립적으로 작동 가능

**The A2A protocol is launched by Google in April 2025 which enables seamless communication and collaboration across different Agentic Enterprise platforms.**

### A2A Architecture

<div style="text-align: center; background: #f5f5f7; padding: 30px; border-radius: 10px; font-family: monospace;">
<h4>What is A2A Protocol?</h4>
<br/>
<div style="display: flex; justify-content: space-around; align-items: center;">
  <div style="border: 2px solid #007AFF; padding: 20px; border-radius: 8px;">
    <strong>Query</strong>
  </div>
  <div style="display: flex; flex-direction: column; gap: 10px;">
    <span>→ Communication Flow →</span>
    <span>← Task Assignment ←</span>
    <span>← Completion (Artifacts) ←</span>
  </div>
  <div style="border: 2px solid #007AFF; padding: 20px; border-radius: 8px;">
    <strong>Agent<br/>Discovery</strong>
  </div>
</div>
</div>

### 핵심 특징
- **탈중앙화된 환경**을 기반으로 에이전트 간 안전한 메시지 교환 및 능동적인 실시간 협업 환경 제공
- **2025년 4월 구글**에 의해 ai 에이전트 상호운용성을 위한 핵심 프로토콜로 제안

---

# A2A 통신 아키텍처

## 완전한 에이전트 협업 시스템

### A2A Architecture 전체 구조

<div style="text-align: center; background: #f5f5f7; padding: 30px; border-radius: 10px;">
<h4 style="color: #007AFF;">A2A Architecture</h4>
<br/>
<div style="display: flex; justify-content: space-around; margin: 20px 0;">
  <div style="border: 2px solid #FF9500; padding: 20px; border-radius: 8px; background: white;">
    <strong>AI Agent 1</strong><br/>
    <em>(Client)</em>
  </div>
  <div style="border: 2px solid #FF9500; padding: 20px; border-radius: 8px; background: white;">
    <strong>AI Agent 2</strong><br/>
    <em>&nbsp;</em>
  </div>
  <div style="border: 2px solid #FF9500; padding: 20px; border-radius: 8px; background: white;">
    <strong>AI Agent 3</strong><br/>
    <em>(Server)</em>
  </div>
</div>
<div style="margin-top: 20px; padding: 15px; background: #007AFF; color: white; border-radius: 8px;">
  <strong>Framework</strong><br/>
  (Google ACP/LLM)
</div>
</div>

### A2A Communication Demo (Travel Agency)

<div style="text-align: center; background: #f5f5f7; padding: 30px; border-radius: 10px;">
<h4 style="color: #5856D6;">Travel Agency Example</h4>
<br/>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center;">
  <div>
    <div style="border: 2px solid #007AFF; padding: 20px; border-radius: 8px; background: white; margin-bottom: 20px;">
      <strong>Query</strong>
    </div>
    <div style="font-size: 24px;">↓</div>
    <div style="border: 2px solid #5856D6; padding: 20px; border-radius: 8px; background: white;">
      <strong>Travel Agent</strong>
    </div>
  </div>
  <div>
    <div style="border: 2px solid #FF9500; padding: 15px; border-radius: 8px; background: white; margin-bottom: 10px;">
      <strong>Flight Agent</strong>
    </div>
    <div style="border: 2px solid #FF9500; padding: 15px; border-radius: 8px; background: white; margin-bottom: 10px;">
      <strong>Weather Agent</strong>
    </div>
    <div style="border: 2px solid #FF9500; padding: 15px; border-radius: 8px; background: white;">
      <strong>Hotel Agent</strong>
    </div>
  </div>
</div>
<p style="margin-top: 20px; font-style: italic;">Accommodation and Activities</p>
</div>

---

# A2A 핵심 구성 요소

## 지능형 에이전트 협업의 기본 요소

### Agent간 통신 메시지 포맷 공통화!

## A2A Communication Elements

```
┌──────────────────────────────────────────────────────┐
│       A2A Communication Elements and Their            │
│                 Relationships                         │
│                                                       │
│     ┌────────┐                    ┌────────────┐     │
│     │  Part  │                    │ Agent Card │     │
│     │        │                    │            │     │
│     │TextPart│                    │ - Identity │     │
│     │FilePart│      ┌──────┐     │ - Capabil. │     │
│     │DataPart│◄─────│ A2A  │────►│            │     │
│     └────────┘      │Comm. │     └────────────┘     │
│                     │Elem. │                         │
│     ┌────────┐      └──────┘     ┌────────────┐     │
│     │Message │◄─────────────────►│    Task    │     │
│     │        │                    │            │     │
│     │ Role   │                    │- Lifecycle │     │
│     │Content │     ┌──────┐      │- Stateful  │     │
│     └────────┘◄────│Artif.│      └────────────┘     │
│                    │      │                          │
│                    │Output│                          │
│                    │Stream│                          │
│                    └──────┘                          │
└──────────────────────────────────────────────────────┘
```

---

# A2A 구성 요소 상세

## 각 요소의 역할과 기능

### 🎴 **AgentCard**
- **각 에이전트의 신원, 역할, 처리 가능한 작업 종류, 통신 인터페이스를 정의**
- 다른 에이전트들이 이 정보를 통해 적절한 협업 대상을 찾음
- **'프로필'** = 명함 역할

### 📋 **Task**
- **에이전트에 할당되어 수행해야 할 구체적인 작업 또는 목표**
- Lifecycle 관리 (생성 → 진행 → 완료)
- Stateful 상태 추적

### 💬 **Message**
- **에이전트 간 의사소통하기 위해 주고받는 구조화된 데이터 패킷**
- Role (송신자/수신자)
- Content (실제 내용)

### 📦 **Part**
- **메시지 내 특정 데이터에 대한 구성 요소**
- TextPart, FilePart, DataPart

### 🎨 **Artifact**
- **에이전트가 태스크를 수행한 결과로 생성되는 산출물**
- Output 결과물
- Streaming 지원

---

# A2A 작동 방식

## 에이전트 통신의 실제 흐름

### A2A 주요 구성 요소 (Core Actors)

```
┌──────────────────────────────────────────────────────┐
│                   Remote Agent                        │
│  ┌─────────┐                              ┌────────┐ │
│  │End-User │                              │        │ │
│  │   👤   │                              │   AI   │ │
│  └────┬────┘                              │ Agent  │ │
│       │                                   │   🤖   │ │
│       ▼                                   └────────┘ │
│  ┌─────────┐         ┌─────────┐                    │
│  │ Client  │◄───────►│ A2A     │                    │
│  │   💻   │         │ Server  │                    │
│  └─────────┘         └─────────┘                    │
└──────────────────────────────────────────────────────┘
```

### 역할 정의
- **End-User**: 에이전트 요청을 시작하는 주체
- **A2A Client**: 사용자를 대신해 작업을 요청
- **A2A Server**: remote agent

### A2A 실행 흐름

```
에이전트 탐색    →    작업 할당    →    작업 완료 전달    →    작업 완료 전달
(A2A Client)         (A2A Client)        (A2A Server)         (A2A Server)

    🔍                   📋                  ⚙️                  ✅
```

---

# A2A 프로토콜의 핵심 특징

## 차세대 에이전트 통신 표준의 강점

### 1️⃣ **기본적으로 안전한 설계**
- 엔터프라이즈급 인증 및 권한 부여 지원을 목표로 설계
- 출시 시점부터 OpenAPI 인증과 등록한 수준의 보안 기능 제공

### 2️⃣ **장기 실행 작업 지원**
- 사람이 개입하여 수 시간 또는 수일이 소요될 수 있는 실증연구까지 유연하게 지원
- **실시간 피드백, 알림, 상태 업데이트 제공**

### 3️⃣ **에이전트 본연의 능력 포용**
- 다양한 에이전트간 협업할 수 있도록 지원하는데 초점
- 에이전트를 단순 "도구"로 제한하지 않고, 진정한 멀티 에이전트 시나리오 구현 가능

### 4️⃣ **기존 표준 기반 구축**
- JSON-RPC, HTTPS 등 널리 사용되는 기존 표준 기반 구축

```
┌────────────────────────────────────────┐
│        A2A Protocol Features            │
│                                        │
│   Build on existing     Secure         │
│     standards          by default      │
│         🏗️                🔒          │
│                                        │
│   Embrace agentic    Support for       │
│    capabilities    long-running tasks  │
│         🤖                ⏱️          │
└────────────────────────────────────────┘
```

---

# A2A 에이전트 검색 (Discovery)

## 적절한 에이전트를 찾는 3가지 방법

```
┌──────────────────────────────────────────────────────┐
│                클라이언트 에이전트                      │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────┴────────────┬────────────────┐
        ▼                         ▼                ▼
┌──────────────┐        ┌──────────────┐   ┌──────────────┐
│ Well-Known   │        │  Curated     │   │   Direct     │
│     URI      │        │  Registry    │   │   Config     │
├──────────────┤        ├──────────────┤   ├──────────────┤
│ /.well-known │        │ 중앙         │   │ 직접 구성    │
│ /agent.json  │        │ 레지스트리   │   │              │
├──────────────┤        ├──────────────┤   ├──────────────┤
│ • 공개 에이전트│        │ • 기업 환경  │   │ • 사내 시스템│
│ • 자동 발견 지원│       │ • 기능 기반  │   │ • 개발 환경  │
│ • 도메인 기반  │        │   검색       │   │ • 고정 관계  │
│               │        │ • 접근 제어   │   │              │
└──────────────┘        └──────────────┘   └──────────────┘
```

### 💡 핵심 포인트
바로, **앰비언트 신호(ambient signals)**에 반응하고, 중요한 기회가 감지되거나 피드백이 필요할 때만 사용자 입력을 요구하는 에이전트입니다.

---