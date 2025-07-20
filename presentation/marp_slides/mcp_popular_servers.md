---
marp: true
theme: default
paginate: true
---

# 인기 MCP 서버 소개

## 실무에서 자주 사용하는 MCP 서버들

### 다양한 작업을 위한 검증된 MCP 서버 모음

---

# 1. Task Master AI

## 🎯 업무 분할 및 관리 MCP 서버

### 주요 기능
- 복잡한 작업을 작은 단위로 분할
- AI 기반 작업 우선순위 설정
- 멀티 AI 모델 활용 (Anthropic, OpenAI, Perplexity)

### 설치 및 설정
```json
{
  "mcpServers": {
    "taskmaster-ai": {
      "command": "npx",
      "args": ["-y", "--package=task-master-ai", "task-master-ai"],
      "env": {
        "ANTHROPIC_API_KEY": "YOUR_KEY",
        "PERPLEXITY_API_KEY": "YOUR_KEY",
        "OPENAI_API_KEY": "YOUR_KEY"
      }
    }
  }
}
```

### 활용 예시
- 프로젝트 계획 수립
- 복잡한 코딩 작업 분해
- 팀 작업 조정

---

# 2. Desktop Commander

## 🖥️ 데스크톱 제어 MCP 서버

### 주요 기능
- 마우스/키보드 제어
- 스크린샷 캡처
- 애플리케이션 실행 및 관리
- 파일 시스템 접근

### 설치 및 설정
```json
{
  "desktop-commander": {
    "command": "npx",
    "args": [
      "-y",
      "@smithery/cli@latest",
      "run",
      "@wonderwhy-er/desktop-commander",
      "--key",
      "26059252-101c-40de-b2d8-3e81234482d1"
    ]
  }
}
```

### 활용 예시
- 자동화된 UI 테스트
- 반복 작업 자동화
- 원격 데스크톱 작업

---

# 3. Playwright MCP

## 🌐 브라우저 자동화 MCP 서버

### 주요 기능
- 웹 브라우저 자동 제어
- E2E 테스트 자동화
- 웹 스크래핑
- 크로스 브라우저 테스트 (Chrome, Firefox, Safari)

### 설치 및 설정
```json
{
  "playwright-mcp": {
    "command": "npx",
    "args": [
      "-y",
      "@smithery/cli@latest",
      "run",
      "@microsoft/playwright-mcp",
      "--key",
      "b6be39e3-462e-421f-83d1-92253fef3186"
    ]
  }
}
```

### 활용 예시
- 웹 애플리케이션 테스트
- 폼 자동 작성
- 웹사이트 모니터링

---

# 4. Context7

## 📚 라이브러리 최신 정보 MCP 서버

### 주요 기능
- NPM, PyPI 등 패키지 최신 버전 확인
- 라이브러리 문서 접근
- 의존성 분석
- 보안 취약점 확인

### 설치 및 설정
```json
{
  "context7": {
    "command": "npx",
    "args": [
      "-y",
      "@upstash/context7-mcp"
    ]
  }
}
```

### 활용 예시
- 프로젝트 의존성 업데이트
- 최신 API 문서 참조
- 보안 패치 확인

---

# 5. Sequential Thinking

## 🧠 단계적 사고 구조화 MCP 서버

### 주요 기능
- 복잡한 문제를 단계별로 분석
- 전략적 사고 프레임워크 제공
- 의사결정 트리 생성
- 논리적 추론 과정 시각화

### 설치 및 설정
```json
{
  "sequential-thinking": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-sequential-thinking"
    ],
    "env": {}
  }
}
```

### 활용 예시
- 아키텍처 설계 결정
- 알고리즘 최적화
- 문제 해결 전략 수립

---

# MCP 서버 선택 가이드

## 용도별 추천 MCP 서버

| 작업 유형 | 추천 MCP | 주요 이점 |
|----------|---------|----------|
| **프로젝트 관리** | Task Master AI | AI 기반 작업 분할 |
| **UI 자동화** | Desktop Commander | 데스크톱 완전 제어 |
| **웹 테스트** | Playwright | 크로스 브라우저 지원 |
| **개발 정보** | Context7 | 최신 라이브러리 정보 |
| **전략 수립** | Sequential Thinking | 체계적 사고 지원 |

### 💡 선택 팁
1. **목적 명확화**: 해결하려는 문제 정의
2. **통합성 검토**: 기존 워크플로우와 호환성
3. **성능 고려**: 리소스 사용량과 응답 속도
4. **보안 확인**: API 키 관리 및 권한 설정

---

# MCP 생태계 확장

## 더 많은 MCP 서버 찾기

### 공식 리소스
- **MCP 공식 저장소**: github.com/modelcontextprotocol/servers
- **Smithery**: smithery.ai (MCP 서버 마켓플레이스)
- **커뮤니티 포럼**: MCP Discord, Reddit

### 자체 MCP 서버 개발
```python
from mcp.server import Server, stdio_server

server = Server("my-custom-server")

@server.tool()
async def my_custom_tool(param: str):
    # 커스텀 로직 구현
    return result

if __name__ == "__main__":
    stdio_server(server).run()
```

### 🚀 MCP의 미래
- 더 많은 AI 모델 지원
- 표준화된 인터페이스
- 기업용 MCP 서버 증가

---