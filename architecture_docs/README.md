# 📁 A2A 시스템 아키텍처 문서

이 폴더는 A2A 감성 분석 시스템의 아키텍처 관련 문서와 다이어그램을 포함하고 있습니다.

## 📊 포함된 파일들

### 1. 다이어그램 파일
- **`architecture_table.md`** ⭐ - 가장 읽기 쉬운 테이블 형식의 구조 설명
- **`architecture_ascii.txt`** - ASCII 아트로 표현된 시스템 구조
- **`architecture_diagram.html`** - 브라우저에서 볼 수 있는 인터랙티브 다이어그램
- **`system_architecture_diagram.md`** - Mermaid 형식의 원본 다이어그램

### 2. 편집 가능한 다이어그램
- **`architecture.drawio`** - Draw.io에서 편집 가능 (https://app.diagrams.net)
- **`architecture.dot`** - Graphviz 형식
- **`architecture.puml`** - PlantUML 형식

### 3. 이미지 파일
- **`system_architecture.png`** - 시스템 구조 이미지 (Mermaid CLI 필요)

### 4. 생성 스크립트
- **`generate_architecture_diagram.py`** - HTML 다이어그램 생성
- **`create_simplified_diagram.py`** - 다양한 형식의 다이어그램 생성

## 🚀 사용 방법

### 빠르게 보기
1. **`architecture_table.md`** - 마크다운 뷰어나 GitHub에서 바로 확인
2. **`architecture_diagram.html`** - 더블클릭하여 브라우저에서 열기

### 다이어그램 편집
- Draw.io: `architecture.drawio` 파일을 https://app.diagrams.net 에서 열기
- VS Code: PlantUML 확장 설치 후 `architecture.puml` 편집

### 이미지 생성
```bash
# Graphviz 이미지 생성
dot -Tpng architecture.dot -o architecture_graphviz.png

# Mermaid 이미지 생성 (mermaid-cli 필요)
npm install -g @mermaid-js/mermaid-cli
python generate_architecture_diagram.py
```

## 📌 시스템 개요

A2A 감성 분석 시스템은 다음과 같은 구조로 이루어져 있습니다:

1. **Web UI** (포트 8100) - 사용자 인터페이스
2. **Main Orchestrator** - 전체 워크플로우 조정
3. **11개의 전문 에이전트** - 각각의 특화된 기능 수행
4. **외부 API 연동** - Gemini, OpenAI, Finnhub, Twitter, SEC, Yahoo Finance

자세한 내용은 각 문서를 참고하세요!