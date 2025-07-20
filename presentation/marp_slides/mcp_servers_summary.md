# 인기 MCP 서버 요약

## 🛠️ 실무에서 자주 사용하는 MCP 서버들

### 1. **Task Master AI** - 업무 분할 관리
- **용도**: 복잡한 작업을 AI가 작은 단위로 분할하고 관리
- **특징**: Anthropic, OpenAI, Perplexity 멀티 AI 활용
- **GitHub**: [claude-task-master](https://github.com/eyaltoledano/claude-task-master)

### 2. **Desktop Commander** - 데스크톱 제어
- **용도**: 마우스, 키보드, 스크린샷 등 데스크톱 완전 제어
- **특징**: UI 자동화, 반복 작업 자동화
- **Smithery**: [@wonderwhy-er/desktop-commander](https://smithery.ai/server/@wonderwhy-er/desktop-commander)

### 3. **Playwright MCP** - 브라우저 자동화
- **용도**: 웹 브라우저 기반 테스트 자동화
- **특징**: Microsoft 공식, 크로스 브라우저 지원
- **GitHub**: [playwright-mcp](https://github.com/microsoft/playwright-mcp)

### 4. **Context7** - 라이브러리 최신 정보
- **용도**: NPM, PyPI 등 패키지 최신 버전 및 문서 제공
- **특징**: Upstash 제공, 의존성 분석 및 보안 취약점 확인
- **GitHub**: [context7](https://github.com/upstash/context7)

### 5. **Sequential Thinking** - 단계적 사고 구조화
- **용도**: 복잡한 문제를 체계적으로 분석하고 전략 수립
- **특징**: MCP 공식 서버, 논리적 추론 과정 지원
- **GitHub**: [sequential-thinking](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)

## 📋 빠른 설정 가이드

### Claude Desktop config 예시
```json
{
  "mcpServers": {
    "taskmaster-ai": {
      "command": "npx",
      "args": ["-y", "--package=task-master-ai", "task-master-ai"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "OPENAI_API_KEY": "sk-..."
      }
    },
    "desktop-commander": {
      "command": "npx",
      "args": ["-y", "@smithery/cli@latest", "run", 
               "@wonderwhy-er/desktop-commander", "--key", "YOUR_KEY"]
    },
    "playwright-mcp": {
      "command": "npx", 
      "args": ["-y", "@smithery/cli@latest", "run",
               "@microsoft/playwright-mcp", "--key", "YOUR_KEY"]
    }
  }
}
```

## 💡 활용 팁
- **조합 사용**: 여러 MCP를 함께 사용하여 시너지 효과
- **커스텀 개발**: 특수 목적에 맞는 자체 MCP 서버 개발 가능
- **커뮤니티**: Smithery.ai에서 더 많은 MCP 서버 탐색