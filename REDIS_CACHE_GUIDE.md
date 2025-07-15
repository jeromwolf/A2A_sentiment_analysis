# Redis 캐싱 시스템 가이드

## 📋 개요

A2A 감성 분석 시스템은 Redis를 활용한 캐싱 시스템을 통해 성능을 대폭 향상시킵니다.
반복적인 요청에 대해 캐시된 결과를 제공하여 응답 속도를 최대 6-7배 향상시킬 수 있습니다.

## 🚀 캐싱 활성화

### 1. Redis 설치 및 실행

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Redis 상태 확인
redis-cli ping
# 응답: PONG
```

### 2. 환경 변수 설정

`.env` 파일에서 캐싱 관련 설정:

```env
# Redis 캐싱 설정
CACHE_ENABLED=true              # 캐싱 활성화
REDIS_URL=redis://localhost:6379 # Redis 연결 URL
CACHE_TTL=3600                  # 기본 캐시 유효시간 (초)
```

## 📊 캐시 TTL 설정

각 데이터 유형별로 다른 TTL(Time To Live)이 적용됩니다:

| 데이터 유형 | TTL | 설명 |
|------------|-----|------|
| ticker_extraction | 24시간 | 티커 심볼은 변경되지 않음 |
| news_data | 5분 | 뉴스는 자주 업데이트됨 |
| twitter_data | 3분 | 트위터는 실시간성이 중요 |
| sec_data | 1시간 | 공시는 자주 변경되지 않음 |
| sentiment_analysis | 10분 | 감정 분석 결과 캐싱 |
| quantitative_data | 1분 | 주가는 실시간 변동 |
| risk_analysis | 10분 | 리스크 분석 결과 |
| final_report | 30분 | 최종 보고서 |

## 🧪 캐싱 테스트

### 테스트 스크립트 실행

```bash
python test_redis_cache_activation.py
```

### 테스트 결과 예시

```
=== 에이전트 캐싱 테스트 ===
첫 번째 요청 (캐시 미스): 0.830초
두 번째 요청 (캐시 히트): 0.123초
속도 향상: 6.7배
```

## 📈 성능 개선 효과

### 1. 응답 속도 향상
- 티커 추출: 830ms → 123ms (6.7배 향상)
- 감정 분석: 2-3초 → 0.5초 이하
- 전체 분석: 10-15초 → 3-5초

### 2. API 호출 감소
- 외부 API 호출 횟수 대폭 감소
- API Rate Limit 문제 해결
- 비용 절감

### 3. 시스템 안정성
- 외부 서비스 장애 시에도 캐시된 데이터 제공
- 부하 분산 효과

## 🔧 캐시 관리

### 캐시 통계 확인

```python
# Python 코드에서
stats = await cache_manager.get_stats()
print(stats)
```

출력 예시:
```json
{
  "enabled": true,
  "connected": true,
  "memory_used": "1.03M",
  "total_keys": 25,
  "namespace_counts": {
    "ticker_extraction": 10,
    "news_data": 5,
    "sentiment_analysis": 10
  },
  "hit_rate": "65.12%"
}
```

### 캐시 무효화

특정 티커의 모든 캐시 삭제:
```python
await cache_manager.invalidate_ticker("AAPL")
```

전체 캐시 삭제:
```python
await cache_manager.clear_all()
```

## 🛠️ 트러블슈팅

### Redis 연결 실패
```bash
# Redis 서비스 상태 확인
brew services list | grep redis

# Redis 재시작
brew services restart redis
```

### 캐시가 작동하지 않음
1. `CACHE_ENABLED=true` 확인
2. Redis 서버 실행 확인: `redis-cli ping`
3. 방화벽/네트워크 설정 확인

### 메모리 부족
```bash
# Redis 메모리 사용량 확인
redis-cli info memory

# 최대 메모리 설정 (redis.conf)
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## 💡 베스트 프랙티스

1. **적절한 TTL 설정**
   - 실시간성이 중요한 데이터는 짧게
   - 변경이 적은 데이터는 길게

2. **캐시 키 설계**
   - 파라미터 기반 자동 키 생성
   - 일관된 키 네이밍 규칙

3. **캐시 워밍업**
   - 시스템 시작 시 주요 데이터 미리 캐싱
   - 인기 티커 사전 로드

4. **모니터링**
   - Hit Rate 모니터링
   - 메모리 사용량 추적
   - 성능 지표 분석

## 📝 추가 설정 (선택사항)

### Redis 영구 저장 설정

`redis.conf`:
```
save 900 1
save 300 10
save 60 10000
```

### 캐시 클러스터링

대규모 서비스를 위한 Redis Cluster 구성:
```bash
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 \
  127.0.0.1:7002 127.0.0.1:7003 \
  --cluster-replicas 1
```

---

캐싱 시스템은 A2A 감성 분석 시스템의 성능을 크게 향상시킵니다.
적절한 설정과 관리로 최적의 성능을 유지하세요!