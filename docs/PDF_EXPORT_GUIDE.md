# PDF Export 기능 가이드

## 개요
A2A 투자 분석 시스템의 최종 보고서를 PDF로 저장하는 기능이 추가되었습니다.

## 구현 방식
브라우저의 내장 인쇄 기능을 활용하여 PDF 생성을 구현했습니다. 이 방식의 장점:
- 추가 라이브러리 의존성 없음
- 브라우저의 PDF 렌더링 엔진 활용
- 사용자가 출력 옵션을 직접 제어 가능

## 사용 방법

### 1. UI 접속
```bash
# 메인 UI 열기
open http://localhost:8000
# 또는 PDF 지원 UI
open index_pdf.html
```

### 2. 분석 실행
1. 주식 관련 질문 입력 (예: "애플 주가 어때?")
2. "분석 시작" 버튼 클릭
3. 분석 완료 대기

### 3. PDF 저장
1. 분석 완료 후 "📄 PDF로 저장" 버튼 클릭
2. 브라우저의 인쇄 대화상자에서:
   - 대상: "PDF로 저장" 선택
   - 레이아웃: 세로 방향 권장
   - 여백: 기본값 사용
   - 배경 그래픽: 선택 (색상 포함)
3. "저장" 클릭

## 기술적 세부사항

### CSS 인쇄 스타일
```css
@media print {
    /* 인쇄 시 불필요한 요소 숨김 */
    .input-section, .status-section, #pdfBtn {
        display: none !important;
    }
    /* 보고서만 표시 */
    .report-section {
        box-shadow: none;
        padding: 0;
    }
}
```

### 브라우저 호환성
- Chrome/Edge: 완벽 지원
- Safari: 지원 (일부 스타일 차이 가능)
- Firefox: 지원

## 주의사항
1. PDF 저장 전 페이지가 완전히 로드되었는지 확인
2. 배경 색상을 포함하려면 인쇄 옵션에서 "배경 그래픽" 선택
3. A4 크기로 최적화되어 있음

## 대안 방법
서버 측 PDF 생성이 필요한 경우:
- weasyprint 라이브러리 사용 (Python)
- puppeteer 사용 (Node.js)
- wkhtmltopdf 사용 (시스템 도구)

현재는 브라우저 기반 방식이 가장 간단하고 안정적입니다.