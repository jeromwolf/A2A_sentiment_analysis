# Redis 캐싱 시스템 설정 가이드

## 개요
Redis는 인메모리 데이터 구조 저장소로, A2A 시스템의 분석 결과를 캐싱하여 성능을 크게 향상시킵니다.

## Redis 설치

### macOS
```bash
# Homebrew로 설치
brew install redis

# Redis 서비스 시작
brew services start redis

# 또는 수동으로 시작
redis-server
```

### Ubuntu/Debian
```bash
# 패키지 업데이트
sudo apt update

# Redis 설치
sudo apt install redis-server

# Redis 서비스 시작
sudo systemctl start redis
sudo systemctl enable redis
```

### Windows
- WSL2 사용 권장 (Ubuntu 설치 후 위 명령어 사용)
- 또는 [Redis for Windows](https://github.com/microsoftarchive/redis/releases) 다운로드

## Redis 상태 확인
```bash
# Redis 연결 테스트
redis-cli ping
# 응답: PONG

# Redis 정보 확인
redis-cli info server
```

## 환경 설정

`.env` 파일에 다음 설정 추가:
```env
# Redis 캐싱 설정
CACHE_ENABLED=true                    # 캐싱 활성화
REDIS_URL=redis://localhost:6379      # Redis 연결 URL
CACHE_TTL=3600                        # 기본 캐시 유효시간 (초)
```

## 캐싱 시스템 기능

### 1. 자동 캐싱
- **티커 추출**: 동일한 질문에 대해 24시간 캐싱
- **뉴스 데이터**: 5분간 캐싱
- **트위터 데이터**: 3분간 캐싱
- **SEC 공시**: 1시간 캐싱
- **감정 분석**: 10분간 캐싱
- **최종 리포트**: 30분간 캐싱

### 2. 캐시 관리 API
```bash
# 캐시 통계 조회
curl http://localhost:8100/cache/stats

# 모든 캐시 삭제
curl -X DELETE http://localhost:8100/cache/clear

# 특정 티커 관련 캐시 삭제
curl -X DELETE http://localhost:8100/cache/ticker/AAPL
```

## 테스트 실행
```bash
# Redis 캐싱 테스트
python test_redis_cache.py
```

## 성능 향상 효과

### 캐싱 전
- 티커 추출: ~1-2초 (Gemini API 호출)
- 감정 분석: ~10-30초 (AI 분석)
- 전체 분석: ~45-90초

### 캐싱 후
- 티커 추출: ~0.001초 (캐시 히트 시)
- 감정 분석: ~0.001초 (캐시 히트 시)
- 전체 분석: ~5-10초 (데이터 수집만 필요)

## 주의사항

1. **메모리 사용량**: Redis는 모든 데이터를 메모리에 저장합니다
   - 기본 maxmemory: 무제한
   - 권장 설정: `maxmemory 1gb`

2. **데이터 영속성**: 기본적으로 Redis는 재시작 시 데이터가 사라집니다
   - RDB 스냅샷 활성화: `save 60 1000`
   - AOF 활성화: `appendonly yes`

3. **보안**: 프로덕션 환경에서는 비밀번호 설정 필수
   ```bash
   # redis.conf
   requirepass your-secure-password
   
   # .env
   REDIS_URL=redis://:your-secure-password@localhost:6379
   ```

## 문제 해결

### Redis 연결 실패
```bash
# Redis 프로세스 확인
ps aux | grep redis

# Redis 로그 확인
tail -f /usr/local/var/log/redis.log  # macOS
tail -f /var/log/redis/redis-server.log  # Linux

# 포트 사용 확인
lsof -i :6379
```

### 캐시가 작동하지 않음
1. `.env` 파일에서 `CACHE_ENABLED=true` 확인
2. Redis 서버 실행 상태 확인
3. `test_redis_cache.py` 실행하여 연결 테스트

## 모니터링

### Redis CLI로 실시간 모니터링
```bash
# 실시간 명령어 모니터링
redis-cli monitor

# 메모리 사용량 확인
redis-cli info memory

# 키 패턴 검색
redis-cli --scan --pattern "a2a:*"
```

### Redis 대시보드 도구
- [RedisInsight](https://redis.com/redis-enterprise/redis-insight/) - 공식 GUI 도구
- [Redis Commander](https://github.com/joeferner/redis-commander) - 웹 기반 관리 도구

## 최적화 팁

1. **TTL 조정**: 데이터 특성에 맞게 TTL 조정
   - 실시간 데이터: 짧은 TTL (1-5분)
   - 정적 데이터: 긴 TTL (1-24시간)

2. **선택적 캐싱**: 비용이 높은 작업만 캐싱
   - AI 분석 결과: 필수 캐싱
   - 간단한 계산: 캐싱 불필요

3. **캐시 워밍**: 자주 사용되는 데이터 미리 로드
   ```python
   # 인기 종목 미리 캐싱
   popular_tickers = ["AAPL", "TSLA", "NVDA"]
   for ticker in popular_tickers:
       # 데이터 수집 및 캐싱
   ```