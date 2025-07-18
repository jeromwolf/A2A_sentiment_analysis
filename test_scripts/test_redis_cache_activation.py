#!/usr/bin/env python3
"""
Redis 캐싱 시스템 활성화 테스트 스크립트
"""

import asyncio
import json
import time
from utils.cache_manager import cache_manager
import aiohttp
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

async def test_cache_basic():
    """기본 캐시 기능 테스트"""
    print("\n=== 기본 캐시 기능 테스트 ===")
    
    # 캐시 활성화 확인
    print(f"캐시 활성화 상태: {cache_manager.enabled}")
    print(f"Redis URL: {cache_manager.redis_url}")
    print(f"기본 TTL: {cache_manager.default_ttl}초")
    
    # 테스트 데이터
    test_namespace = "test"
    test_params = {"ticker": "AAPL", "query": "애플 주가 분석"}
    test_data = {"result": "긍정적", "score": 0.85, "timestamp": time.time()}
    
    # 동기 테스트
    print("\n--- 동기 메서드 테스트 ---")
    
    # 캐시 저장
    success = cache_manager.set(test_namespace, test_params, test_data)
    print(f"캐시 저장: {success}")
    
    # 캐시 읽기
    cached = cache_manager.get(test_namespace, test_params)
    print(f"캐시 읽기: {cached}")
    
    # 캐시 삭제
    deleted = cache_manager.delete(test_namespace, test_params)
    print(f"캐시 삭제: {deleted}")
    
    # 삭제 후 읽기
    cached_after_delete = cache_manager.get(test_namespace, test_params)
    print(f"삭제 후 읽기: {cached_after_delete}")
    
    # 비동기 테스트
    print("\n--- 비동기 메서드 테스트 ---")
    
    # 캐시 저장
    success = await cache_manager.set_async(test_namespace, test_params, test_data)
    print(f"비동기 캐시 저장: {success}")
    
    # 캐시 읽기
    cached = await cache_manager.get_async(test_namespace, test_params)
    print(f"비동기 캐시 읽기: {cached}")
    
    # 캐시 통계
    stats = await cache_manager.get_stats()
    print(f"\n캐시 통계:\n{json.dumps(stats, indent=2, ensure_ascii=False)}")

async def test_agent_caching():
    """실제 에이전트에서 캐싱 테스트"""
    print("\n=== 에이전트 캐싱 테스트 ===")
    
    api_key = os.getenv("A2A_API_KEY", "a2a-secure-api-key-2025")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    # NLU Agent 테스트 (티커 추출)
    print("\n--- NLU Agent 캐싱 테스트 ---")
    async with aiohttp.ClientSession() as session:
        query = "애플 주가 어때?"
        
        # 첫 번째 요청 (캐시 미스)
        start_time = time.time()
        async with session.post(
            "http://localhost:8108/extract_ticker",
            json={"query": query},
            headers=headers
        ) as response:
            result1 = await response.json()
            time1 = time.time() - start_time
        print(f"첫 번째 요청 (캐시 미스): {time1:.3f}초")
        print(f"결과: {result1}")
        
        # 두 번째 요청 (캐시 히트)
        start_time = time.time()
        async with session.post(
            "http://localhost:8108/extract_ticker",
            json={"query": query},
            headers=headers
        ) as response:
            result2 = await response.json()
            time2 = time.time() - start_time
        print(f"\n두 번째 요청 (캐시 히트): {time2:.3f}초")
        print(f"결과: {result2}")
        print(f"속도 향상: {time1/time2:.1f}배")

async def test_cache_ttl():
    """캐시 TTL 테스트"""
    print("\n=== 캐시 TTL 테스트 ===")
    
    # 각 네임스페이스별 TTL 확인
    print("네임스페이스별 TTL 설정:")
    for namespace, ttl in cache_manager.ttl_settings.items():
        print(f"  - {namespace}: {ttl}초 ({ttl/60:.1f}분)")
    
    # 짧은 TTL 테스트
    test_namespace = "ticker_extraction"
    test_params = {"test": "ttl"}
    test_data = {"result": "TTL 테스트"}
    
    # 캐시 저장
    await cache_manager.set_async(test_namespace, test_params, test_data)
    print(f"\n캐시 저장 완료 (TTL: {cache_manager._get_ttl(test_namespace)}초)")
    
    # 즉시 읽기
    cached = await cache_manager.get_async(test_namespace, test_params)
    print(f"즉시 읽기: {cached}")
    
    # TTL 확인을 위한 키 정보
    key = cache_manager._generate_key(test_namespace, test_params)
    client = await cache_manager.async_client
    ttl_remaining = await client.ttl(key)
    print(f"남은 TTL: {ttl_remaining}초")

async def test_cache_invalidation():
    """캐시 무효화 테스트"""
    print("\n=== 캐시 무효화 테스트 ===")
    
    # 여러 티커 관련 데이터 저장
    tickers = ["AAPL", "TSLA", "NVDA"]
    namespaces = ["ticker_extraction", "news_data", "sentiment_analysis"]
    
    print("테스트 데이터 저장 중...")
    for ticker in tickers:
        for namespace in namespaces:
            params = {"ticker": ticker, "type": namespace}
            data = {"ticker": ticker, "namespace": namespace}
            await cache_manager.set_async(namespace, params, data)
    
    # 통계 확인
    stats = await cache_manager.get_stats()
    print(f"저장 후 캐시 통계: {stats['namespace_counts']}")
    
    # AAPL 관련 캐시 무효화
    print("\nAAPL 관련 캐시 무효화 중...")
    await cache_manager.invalidate_ticker("AAPL")
    
    # 무효화 후 통계
    stats = await cache_manager.get_stats()
    print(f"무효화 후 캐시 통계: {stats['namespace_counts']}")
    
    # 전체 캐시 삭제
    print("\n전체 캐시 삭제 중...")
    await cache_manager.clear_all()
    
    # 삭제 후 통계
    stats = await cache_manager.get_stats()
    print(f"삭제 후 캐시 통계: {stats}")

async def main():
    """메인 테스트 함수"""
    print("🚀 Redis 캐싱 시스템 활성화 테스트 시작")
    
    # 캐시 활성화 상태 확인
    if not cache_manager.enabled:
        print("❌ 캐시가 비활성화되어 있습니다. .env 파일에서 CACHE_ENABLED=true로 설정하세요.")
        return
    
    # Redis 연결 테스트
    try:
        client = await cache_manager.async_client
        await client.ping()
        print("✅ Redis 연결 성공!")
    except Exception as e:
        print(f"❌ Redis 연결 실패: {e}")
        print("Redis 서버가 실행 중인지 확인하세요: redis-server")
        return
    
    # 각 테스트 실행
    await test_cache_basic()
    await test_cache_ttl()
    await test_cache_invalidation()
    
    # 실제 에이전트 테스트 (에이전트가 실행 중인 경우)
    try:
        await test_agent_caching()
    except Exception as e:
        print(f"\n⚠️  에이전트 테스트 스킵 (에이전트가 실행되지 않음): {e}")
    
    print("\n✅ 모든 테스트 완료!")
    
    # 최종 통계
    final_stats = await cache_manager.get_stats()
    print(f"\n최종 캐시 통계:\n{json.dumps(final_stats, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())