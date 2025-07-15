# 데이터 정확성 수정 내역

## 문제점
1. **일일 변동률 표시 오류**: UI에서 일일 변동률이 "값 없음"으로 표시됨
2. **MACD 표시 오류**: MACD 값이 올바르게 표시되지 않음

## 원인 분석
1. **일일 변동률**: 
   - Quantitative Agent는 `price_data.change_1d_percent`로 데이터 전송
   - Frontend는 `daily_change`를 찾고 있었음
   
2. **MACD**:
   - Quantitative Agent는 `macd_signal` 문자열 ("bullish", "bearish", "neutral")로 전송
   - Frontend는 `macd` 객체나 숫자값을 기대하고 있었음

## 해결 방법

### 1. index_v2.html - updateStats 함수 수정
```javascript
// 기존: data.daily_change만 확인
// 수정: 여러 경로에서 일일 변동률 찾기
if (data.daily_change !== undefined) {
    dailyChange = data.daily_change;
} else if (data.price_data && data.price_data.change_1d_percent !== undefined) {
    dailyChange = data.price_data.change_1d_percent;
}
```

### 2. index_v2.html - updateTechnicalIndicators 함수 수정
```javascript
// 기존: indicators.macd 객체 처리
// 수정: indicators.macd_signal 문자열 우선 처리
if (indicators.macd_signal !== undefined) {
    const signal = indicators.macd_signal.toLowerCase();
    if (signal === 'bullish') {
        macdElement.textContent = '상승';
        macdElement.className = 'stat-value positive';
    } else if (signal === 'bearish') {
        macdElement.textContent = '하락';
        macdElement.className = 'stat-value negative';
    } else {
        macdElement.textContent = '중립';
        macdElement.className = 'stat-value neutral';
    }
}
```

## 검증 결과
- Quantitative Agent API 직접 테스트 결과:
  - `change_1d_percent`: -1.2 (정확히 -1.20% 표시)
  - `macd_signal`: "neutral" (중립으로 표시)

## 추가 개선사항
- 캔들 데이터 수집 실패 시 기본값 사용 중 (Finnhub API 제한)
- RSI, 이동평균선 등 기술적 지표는 캔들 데이터가 필요하여 현재 기본값 표시