# 📊 차트 시각화 기능 가이드

## 개요

A2A 감성 분석 시스템에 실시간 차트 시각화 기능이 추가되었습니다.
Chart.js를 활용하여 투자 분석 결과를 직관적으로 표현합니다.

## 🎯 주요 기능

### 1. 실시간 차트 업데이트
- WebSocket을 통한 실시간 데이터 스트리밍
- 분석 진행 중 각 단계별 차트 업데이트
- 부드러운 애니메이션 효과

### 2. 차트 종류

#### 📈 주가 차트
- 30일간 주가 추이 라인 차트
- 현재가, 일일 변동률 표시
- 이동평균선 오버레이 (계획)

#### 📊 감성 분석 차트
- **파이 차트**: 긍정/부정/중립 비율
- **막대 차트**: 뉴스/트위터/SEC별 감성 점수
- **트렌드 차트**: 시간별 감성 점수 변화 (계획)

#### 📉 기술적 지표
- **RSI 차트**: 과매수/과매도 구간 표시
- **MACD 차트**: 시그널선과 히스토그램 (계획)
- **볼린저 밴드**: 상단/하단 밴드 (계획)

#### 🎯 종합 대시보드
- 주요 지표 카드 (현재가, 변동률, 감성점수, 투자의견)
- 색상 코딩: 긍정(녹색), 부정(빨강), 중립(회색)

## 🔧 기술 구현

### Frontend (index_v2_with_charts.html)

```javascript
// 차트 초기화
const charts = {
    price: new Chart(ctx, { type: 'line', ... }),
    sentimentPie: new Chart(ctx, { type: 'doughnut', ... }),
    sentimentBar: new Chart(ctx, { type: 'bar', ... }),
    rsi: new Chart(ctx, { type: 'line', ... })
};

// WebSocket 메시지 처리
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'chart_update') {
        updateCharts(data.payload);
    }
};
```

### Backend (main_orchestrator_v2.py)

```python
# 차트 데이터 전송
async def _send_chart_update(self, client_id: str, chart_type: str, data: Dict):
    await self._send_to_ui(client_id, "chart_update", {
        "chart_type": chart_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
```

## 📱 UI/UX 특징

### 반응형 레이아웃
- 데스크톱: 2열 그리드 (채팅 + 차트)
- 모바일: 1열 스택 레이아웃
- 자동 크기 조정

### 탭 인터페이스
- **종합**: 주요 지표 대시보드
- **주가**: 가격 차트
- **감성분석**: 감성 점수 시각화
- **기술지표**: RSI, MACD 등

### 실시간 피드백
- 로딩 스피너
- 상태 인디케이터
- 진행률 표시

## 🚀 사용 방법

### 1. 시스템 시작
```bash
./start_v2_complete.sh
```

### 2. 차트 UI 접속
```
http://localhost:8100
```
새로운 차트 기능이 포함된 UI가 표시됩니다.

### 3. 분석 실행
채팅창에 종목 질문 입력 시:
1. 실시간으로 차트가 업데이트됨
2. 각 분석 단계별 결과가 시각화됨
3. 최종 투자 의견이 대시보드에 표시됨

## 📊 차트 데이터 구조

### 주가 데이터
```json
{
    "chart_type": "price_chart",
    "data": {
        "ticker": "AAPL",
        "current_price": 313.51,
        "daily_change": 1.17,
        "dates": ["2025-01-01", ...],
        "closes": [310.0, 312.5, ...]
    }
}
```

### 감성 분석 데이터
```json
{
    "chart_type": "sentiment_analysis",
    "data": {
        "ticker": "AAPL",
        "sentiment_by_source": {
            "news": 0.65,
            "twitter": 0.42,
            "sec": -0.15
        },
        "positive_count": 15,
        "negative_count": 5,
        "neutral_count": 10
    }
}
```

### 기술적 지표
```json
{
    "chart_type": "technical_indicators",
    "data": {
        "ticker": "AAPL",
        "rsi": 50.0,
        "macd": {
            "macd_line": 2.5,
            "signal_line": 2.1,
            "histogram": 0.4
        }
    }
}
```

## 🎨 커스터마이징

### 차트 스타일 변경
```javascript
// Chart.js 옵션 수정
charts.price.options = {
    plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
    },
    scales: {
        y: { grid: { color: 'rgba(0,0,0,0.1)' } }
    }
};
```

### 새로운 차트 추가
1. HTML에 canvas 요소 추가
2. Chart.js 인스턴스 생성
3. WebSocket 핸들러에 업데이트 로직 추가
4. Backend에서 데이터 전송

## 🐛 트러블슈팅

### 차트가 표시되지 않음
- Chart.js CDN 로드 확인
- WebSocket 연결 상태 확인
- 브라우저 콘솔에서 에러 확인

### 데이터 업데이트 안됨
- WebSocket 메시지 형식 확인
- 차트 update() 메서드 호출 확인
- 데이터 구조 일치 여부 확인

## 📈 향후 계획

### Phase 1 (완료)
- ✅ 기본 차트 구조
- ✅ WebSocket 통합
- ✅ 주가, 감성분석 차트

### Phase 2 (진행중)
- 🔄 기술적 지표 차트 완성
- 🔄 캔들스틱 차트
- 🔄 거래량 차트

### Phase 3 (계획)
- 📅 히스토리컬 데이터 비교
- 📅 차트 내보내기 (PNG/PDF)
- 📅 인터랙티브 줌/팬
- 📅 다중 종목 비교

## 💡 팁

1. **성능 최적화**
   - 대량 데이터는 샘플링 처리
   - 불필요한 리렌더링 방지
   - 차트 애니메이션 선택적 사용

2. **사용성 개선**
   - 툴팁으로 상세 정보 제공
   - 색상으로 직관적 표현
   - 모바일 터치 제스처 지원

3. **접근성**
   - 차트 데이터의 텍스트 대안 제공
   - 고대비 모드 지원
   - 키보드 네비게이션

---

차트 시각화 기능은 A2A 시스템의 분석 결과를 더욱 직관적으로 이해할 수 있게 해줍니다.
지속적인 개선을 통해 더 나은 투자 의사결정을 지원하겠습니다!