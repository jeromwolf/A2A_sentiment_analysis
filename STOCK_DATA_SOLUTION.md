# 주가 데이터 수집 문제 해결 방안

## 현재 문제점
1. **Finnhub API**: 캔들 데이터 접근 권한 없음 (유료 플랜 필요)
2. **Yahoo Finance**: 429 에러 (너무 많은 요청) - Rate Limit 초과
3. **실시간 정확한 데이터 수집 어려움**

## 해결 방안

### 1. 단기 해결책: 캐싱 및 Rate Limiting 강화
```python
# Redis 캐시 활용 (.env에 이미 설정됨)
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600  # 1시간 캐싱
```

### 2. API 대안들

#### A. Alpha Vantage (무료 티어)
- **장점**: 무료로 기본 주가 데이터 제공
- **제한**: 분당 5개 요청, 일일 100개 요청
- **API 키**: https://www.alphavantage.co/support/#api-key

#### B. IEX Cloud (무료 티어)
- **장점**: 월 50,000 메시지 무료
- **제한**: 실시간 데이터는 유료
- **가입**: https://iexcloud.io/

#### C. Polygon.io (무료 티어)
- **장점**: 분당 5개 요청 무료
- **제한**: 15분 지연 데이터
- **가입**: https://polygon.io/

#### D. Twelve Data (무료 티어)
- **장점**: 일일 800개 요청 무료
- **제한**: 분당 8개 요청
- **가입**: https://twelvedata.com/

### 3. 하이브리드 접근법 구현

```python
class StockDataAggregator:
    """여러 데이터 소스를 활용한 주가 데이터 수집"""
    
    def __init__(self):
        self.sources = {
            'finnhub': FinnhubClient(),
            'alpha_vantage': AlphaVantageClient(),
            'yahoo': YahooFinanceClient(),
        }
        self.cache = RedisCache()
    
    async def get_stock_data(self, ticker: str):
        # 1. 캐시 확인
        cached = await self.cache.get(f"stock:{ticker}")
        if cached:
            return cached
            
        # 2. 여러 소스에서 순차적으로 시도
        for source_name, client in self.sources.items():
            try:
                data = await client.get_data(ticker)
                if data:
                    # 캐시 저장
                    await self.cache.set(f"stock:{ticker}", data, ttl=3600)
                    return data
            except RateLimitError:
                continue
                
        # 3. 모든 소스 실패 시 마지막 캐시된 데이터 반환
        return await self.cache.get(f"stock:{ticker}:last")
```

### 4. 추천 구현 순서

1. **즉시 적용 가능**: Redis 캐싱 활성화
   ```bash
   # Redis 설치 및 실행
   brew install redis
   redis-server
   ```

2. **Alpha Vantage 통합** (무료 API 키 필요)
   ```bash
   # .env에 추가
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

3. **폴백 메커니즘 구현**
   - Primary: Yahoo Finance (캐시 활용)
   - Secondary: Alpha Vantage
   - Tertiary: Finnhub (기본 quote 데이터만)

### 5. 장기 해결책

1. **유료 API 구독 검토**
   - Finnhub Pro: $49.99/월 (무제한 요청)
   - IEX Cloud: $9/월 (500만 메시지)
   - Polygon.io: $29.99/월 (무제한)

2. **자체 데이터 수집 인프라**
   - 일일 배치로 데이터 수집 및 저장
   - 실시간 업데이트는 WebSocket 활용

3. **사용자 경험 개선**
   - 로딩 상태 명확히 표시
   - 데이터 지연 시 안내 메시지
   - 캐시된 데이터 사용 시 표시

## 실무 추천사항

보고서의 신뢰성을 위해:

1. **투명성**: 데이터 소스와 업데이트 시간 명시
2. **캐싱 전략**: 주요 지표는 1시간, 기술적 지표는 15분 캐싱
3. **에러 처리**: 데이터 수집 실패 시 명확한 안내
4. **대안 제공**: 수동으로 주가 입력 옵션 제공

## 결론

현재 무료 API의 한계로 실시간 정확한 데이터 수집이 어렵습니다. 
단기적으로는 캐싱과 여러 API 소스를 활용한 하이브리드 접근법을,
장기적으로는 유료 API 구독이나 자체 인프라 구축을 고려해야 합니다.