# Marp 프레젠테이션 가이드

## 📁 파일 구성
- `marp_presentation.md`: 전체 프레젠테이션 (30장)
- `presentation.html`: HTML 버전 (브라우저에서 바로 열기)
- `convert.sh`: 변환 스크립트

## 🚀 변환 방법

### 1. 터미널에서 이 폴더로 이동
```bash
cd /Users/kelly/Desktop/발표자료.우선순위높은거/agent2agent/source/a2a_sentiment_analysis/presentation/marp_slides
```

### 2. PDF로 변환
```bash
marp marp_presentation.md --pdf -o presentation.pdf
```

### 3. PPTX로 변환 (키노트에서 열기 가능)
```bash
marp marp_presentation.md --pptx -o presentation.pptx
```

### 4. 또는 convert.sh 실행
```bash
bash convert.sh
```

## 🎨 키노트에서 사용하기

1. PPTX 파일 생성 후
2. 키노트 실행
3. 파일 > 열기 > presentation.pptx 선택
4. 키노트 형식으로 저장

## 💡 팁

### HTML 프레젠테이션 사용
- `presentation.html`을 브라우저에서 열기
- 화살표 키로 슬라이드 이동
- F11로 전체화면

### 커스터마이징
- `marp_presentation.md` 상단의 `style:` 섹션에서 디자인 수정
- 폰트, 색상, 레이아웃 조정 가능

### 이미지 추가
```markdown
![이미지 설명](이미지경로.png)
```

### 발표자 노트
```markdown
<!--
여기에 발표자 노트 작성
PDF로 변환 시 노트로 포함됨
-->
```