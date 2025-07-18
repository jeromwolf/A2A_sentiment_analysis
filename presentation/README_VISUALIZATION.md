# A2A 통신 흐름 시각화 가이드

발표를 위한 시각화 자료를 준비했습니다. 각 파일의 용도와 사용법을 안내합니다.

## 1. visualization.html - 종합 시각화 대시보드

### 특징
- 4개의 탭으로 구성된 종합 대시보드
- Mermaid.js를 사용한 다이어그램
- 인터랙티브한 에이전트 카드

### 탭 구성
1. **전체 구조**: 시스템 아키텍처 다이어그램
2. **처리 흐름**: 시퀀스 다이어그램으로 메시지 흐름 표현
3. **에이전트 상세**: 각 에이전트의 역할과 포트 정보
4. **실행 타임라인**: 단계별 처리 시간 시각화

### 사용법
```bash
# 브라우저에서 직접 열기
open visualization.html
```

## 2. flow_animation.html - 실시간 통신 애니메이션

### 특징
- Canvas 기반 실시간 애니메이션
- 메시지 전송 시각화
- 시뮬레이션 제어 기능

### 주요 기능
- **시뮬레이션 제어**: 시작/일시정지/초기화
- **속도 조절**: 0.5x, 1x, 2x 속도
- **실시간 로그**: 메시지 전송 내역
- **통계 표시**: 메시지 수, 처리 시간

### 사용법
```bash
# 브라우저에서 열기
open flow_animation.html

# 시뮬레이션 시작 버튼 클릭
```

## 3. 발표 시 활용 방법

### 도입부
1. `visualization.html`의 "전체 구조" 탭으로 시스템 아키텍처 설명
2. 13개 에이전트의 역할 소개

### 핵심 설명
1. `flow_animation.html`로 실시간 통신 흐름 시연
2. "애플 주가 분석" 시나리오 실행
3. 병렬 처리의 장점 강조

### 기술 상세
1. `visualization.html`의 "처리 흐름" 탭으로 시퀀스 다이어그램 설명
2. A2A 메시지 프로토콜 구조 설명

### 마무리
1. "실행 타임라인" 탭으로 전체 처리 시간 강조 (2.6초)
2. MCP 통합 비전 제시

## 4. 커스터마이징

### 색상 테마
- Primary: #4fc3f7 (하늘색)
- Secondary: #ab5dee (보라색)
- Success: #66bb6a (초록색)
- Warning: #ff7043 (주황색)

### 에이전트 추가
`flow_animation.html`의 agents 배열에 새 에이전트 추가:
```javascript
agents.push({
    id: 'mcp',
    name: 'MCP Data',
    x: 0,
    y: 0,
    color: '#e91e63',
    type: 'external'
});
```

## 5. 발표 팁

1. **두 화면 사용**: 
   - 메인 화면: 시각화
   - 보조 화면: 실제 시스템 데모

2. **시나리오 준비**:
   - AAPL (애플) - 안정적인 대형주
   - TSLA (테슬라) - 변동성 있는 성장주
   - NVDA (엔비디아) - AI 관련주

3. **강조 포인트**:
   - 병렬 처리로 인한 속도
   - 각 에이전트의 독립성
   - 확장 가능한 구조

## 6. 기술 요구사항

- 최신 웹 브라우저 (Chrome, Firefox, Safari)
- 인터넷 연결 (Mermaid.js, GSAP CDN)
- 1920x1080 이상 해상도 권장

## 7. 트러블슈팅

### 다이어그램이 보이지 않는 경우
- 브라우저 콘솔에서 Mermaid 로드 확인
- 인터넷 연결 상태 확인

### 애니메이션이 느린 경우
- 다른 탭 닫기
- 하드웨어 가속 활성화

---

발표 성공을 기원합니다! 🚀