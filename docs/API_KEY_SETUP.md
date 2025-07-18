# API 키 발급 및 설정 가이드

## 1. Alpha Vantage (추천 ⭐)

### 발급 절차
1. https://www.alphavantage.co/support/#api-key 접속
2. 양식 작성 (30초):
   - First Name: 이름
   - Last Name: 성
   - Email: 이메일
3. "GET FREE API KEY" 클릭
4. API 키 즉시 발급!

### .env 설정
```bash
# 기존 demo를 실제 키로 교체
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
```

### 테스트
```bash
# API 키 테스트
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

## 2. Twelve Data

### 발급 절차
1. https://twelvedata.com/signup 회원가입
2. 이메일 인증
3. 대시보드 접속: https://twelvedata.com/account/dashboard
4. API Keys 탭에서 키 복사

### .env 설정
```bash
TWELVE_DATA_API_KEY=your_twelve_data_key_here
```

## 3. 추가 무료 대안

### IEX Cloud
- https://iexcloud.io/
- 월 50,000 메시지 무료
- 신용카드 불필요

### Polygon.io
- https://polygon.io/
- 무료 티어 제공
- 실시간 데이터는 15분 지연

## 설정 후 테스트

```bash
# 1. 환경 변수 다시 로드
source .env

# 2. Quantitative Agent 재시작
pkill -f "uvicorn.*8211"
USE_MOCK_DATA=false uvicorn agents.quantitative_agent_v2:app --port 8211

# 3. API 테스트
curl -X POST http://localhost:8211/quantitative_analysis \
  -H "Content-Type: application/json" \
  -H "X-API-Key: a2a-secure-api-key-2025" \
  -d '{"ticker": "AAPL"}'
```

## 문제 해결

### Alpha Vantage 응답이 느린 경우
- 무료 플랜은 응답이 1-2초 걸릴 수 있음
- 캐싱 활용 권장

### API 한도 초과 시
- Redis 캐싱 활성화
- 여러 API 키 로테이션