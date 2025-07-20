---
marp: true
theme: default
paginate: true
---

# MCP로 연결 가능한 도구들

## LLM이 활용할 수 있는 다양한 외부 기능

### AI의 활용 범위 확장

---

# 도구의 확장 (다양한 외부기능)

## LLM + MCP = 무한한 가능성

```
┌─────────────────────────────────────────────────┐
│                    도구들                         │
│                                                 │
│  Figma     GitHub    YouTube   Google Maps      │
│    🎨        🐙        📺         📍            │
│                                                 │
│  Gmail    대한항공    부동산    토스페이          │
│    📧        ✈️        🏠        💳            │
│                                                 │
│  Notion    Slack    Prodia    멜스케어           │
│    📝        💬       🎨        🏥             │
│                                                 │
│  임정             IoT      마인크래프트          │
│   📊              🌐         🎮                │
└─────────────────────────────────────────────────┘
                        ↓
                      LLM
                AI의 활용 범위 확장
```

### 💡 핵심 메시지
**"내가 만들고자 하는 AI 앱에 다 응용 수 있어요"**

---

# MCP가 가능하게 하는 것

## 🛠️ 도구 통합의 표준화

### 이전: 각 도구마다 다른 통합 방식
```python
# Gmail API
gmail_service = build('gmail', 'v1', credentials=creds)
messages = gmail_service.users().messages().list().execute()

# Slack API  
slack_client = WebClient(token=os.environ["SLACK_TOKEN"])
response = slack_client.chat_postMessage(channel="#general")

# Notion API
notion = Client(auth=os.environ["NOTION_TOKEN"])
page = notion.pages.create(parent={"database_id": db_id})
```

### 현재: MCP로 통일된 인터페이스
```python
# 모든 도구를 동일한 방식으로
await mcp_client.call_tool("gmail.send", {"to": "user@email.com"})
await mcp_client.call_tool("slack.post", {"channel": "#general"})
await mcp_client.call_tool("notion.create", {"database": db_id})
```

---

# 카테고리별 도구 활용

## 📊 업무 생산성
- **Notion**: 문서 작성, 데이터베이스 관리
- **Slack**: 팀 커뮤니케이션
- **Gmail**: 이메일 자동화
- **임정**: 일정 관리

## 🎨 크리에이티브
- **Figma**: 디자인 협업
- **YouTube**: 비디오 분석
- **Prodia**: AI 이미지 생성
- **마인크래프트**: 3D 환경 구축

## 🏢 비즈니스
- **토스페이**: 결제 처리
- **대한항공**: 항공 예약
- **부동산**: 매물 검색
- **멜스케어**: 헬스케어 데이터

---

# 실제 활용 시나리오

## 🤖 AI 어시스턴트의 하루

### 오전 9:00 - 업무 시작
```python
# 1. Gmail에서 중요 메일 요약
emails = await mcp.call_tool("gmail.get_important")
summary = await llm.summarize(emails)

# 2. Slack에 일일 브리핑 전송
await mcp.call_tool("slack.post", {
    "channel": "#daily-briefing",
    "message": summary
})
```

### 오후 2:00 - 프로젝트 관리
```python
# 3. GitHub 이슈 확인
issues = await mcp.call_tool("github.list_issues")

# 4. Notion에 진행 상황 업데이트
await mcp.call_tool("notion.update_page", {
    "page_id": project_page,
    "content": progress_report
})
```

---

# MCP 도구 생태계의 장점

## ✅ 개발자 관점

### 1. **빠른 통합**
- 표준화된 인터페이스
- 한 번 배우면 모든 도구에 적용

### 2. **유지보수 용이**
- 도구별 API 변경에 독립적
- MCP 서버만 업데이트

### 3. **확장성**
- 새로운 도구 추가가 간단
- 플러그인 방식의 아키텍처

## ✅ 사용자 관점

### 1. **통합된 경험**
- 하나의 AI로 모든 도구 제어
- 자연어로 복잡한 작업 수행

### 2. **자동화 강화**
- 도구 간 워크플로우 생성
- 반복 작업 제거

---

# IoT와 미래 기술 통합

## 🌐 MCP가 연결하는 물리적 세계

### IoT 디바이스 제어
```python
# 스마트홈 시나리오
async def smart_home_routine():
    # 날씨 확인
    weather = await mcp.call_tool("weather.get_current")
    
    # 온도 조절
    if weather.temperature > 28:
        await mcp.call_tool("iot.ac_control", {
            "action": "turn_on",
            "temperature": 24
        })
    
    # 조명 제어
    await mcp.call_tool("iot.lights", {
        "action": "dim",
        "level": 70
    })
```

### 🔮 미래 가능성
- **자율주행차**: 내비게이션 + IoT 통합
- **스마트시티**: 도시 인프라 최적화
- **산업 자동화**: 공장 설비 AI 제어

---

# MCP 서버 마켓

## 🛍️ Smithery.ai - MCP 서버의 앱스토어

### 특징
- **검색 가능**: 카테고리별 도구 탐색
- **평가 시스템**: 사용자 리뷰 및 평점
- **쉬운 설치**: 원클릭 설정

### 인기 카테고리
1. **개발 도구**: GitHub, GitLab, Jira
2. **생산성**: Notion, Todoist, Calendar
3. **커뮤니케이션**: Slack, Discord, Teams
4. **금융**: 토스, 카카오페이, 은행 API
5. **엔터테인먼트**: YouTube, Spotify, Netflix

### 🚀 성장하는 생태계
- 매주 새로운 MCP 서버 추가
- 커뮤니티 기여 활발
- 기업용 프리미엄 서버 등장

**"내가 만들고자 하는 AI 앱에 다 응용 수 있어요"**

---