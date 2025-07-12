#!/usr/bin/env python3
"""
Redis 캐싱 테스트 스크립트

Redis 연결과 캐싱 기능을 테스트합니다.
"""

import asyncio
import time
from utils.cache_manager import cache_manager

async def test_redis_connection():
    """Redis 연결 테스트"""
    print("1. Redis 연결 테스트")
    print("-" * 50)
    
    try:
        # 간단한 값 설정/가져오기
        test_data = {"test": "data", "timestamp": time.time()}
        
        # 캐시에 저장
        success = await cache_manager.set_async("test", {"key": "test1"}, test_data)
        print(f"✅ 캐시 저장 성공: {success}")
        
        # 캐시에서 가져오기
        cached_data = await cache_manager.get_async("test", {"key": "test1"})
        print(f"✅ 캐시 조회 성공: {cached_data}")
        
        # 데이터 비교
        if cached_data and cached_data["test"] == test_data["test"]:
            print("✅ 데이터 무결성 확인됨")
        else:
            print("❌ 데이터 무결성 문제")
            
    except Exception as e:
        print(f"❌ Redis 연결 실패: {e}")
        return False
        
    return True

async def test_ticker_caching():
    """티커 추출 캐싱 테스트"""
    print("\n2. 티커 추출 캐싱 테스트")
    print("-" * 50)
    
    # 테스트 데이터
    test_queries = [
        "애플 주가 어때?",
        "테슬라 투자 전망은?",
        "엔비디아 실적 분석해줘"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: {query}")
        
        # 첫 번째 호출 (캐시 미스)
        start_time = time.time()
        cache_params = {"query": query.lower()}
        
        # 캐시 확인
        cached_result = await cache_manager.get_async("ticker_extraction", cache_params)
        if cached_result:
            print(f"  💾 캐시 히트! 결과: {cached_result}")
        else:
            print(f"  ❌ 캐시 미스")
            
            # 가상의 티커 추출 결과
            result = {
                "ticker": "AAPL" if "애플" in query else "TSLA" if "테슬라" in query else "NVDA",
                "company_name": "애플" if "애플" in query else "테슬라" if "테슬라" in query else "엔비디아",
                "confidence": 0.95
            }
            
            # 캐시에 저장
            await cache_manager.set_async("ticker_extraction", cache_params, result)
            print(f"  ✅ 캐시에 저장됨")
        
        elapsed = time.time() - start_time
        print(f"  ⏱️ 소요 시간: {elapsed:.3f}초")

async def test_sentiment_caching():
    """감정 분석 캐싱 테스트"""
    print("\n3. 감정 분석 캐싱 테스트")
    print("-" * 50)
    
    # 테스트 데이터
    test_data = {
        "ticker": "AAPL",
        "data_hash": "test123"
    }
    
    # 첫 번째 호출
    start_time = time.time()
    cached_result = await cache_manager.get_async("sentiment_analysis", test_data)
    
    if not cached_result:
        print("❌ 캐시 미스 (예상됨)")
        
        # 가상의 분석 결과
        result = {
            "analyzed_results": [
                {"source": "news", "score": 0.7, "summary": "긍정적 뉴스"},
                {"source": "twitter", "score": 0.3, "summary": "중립적 반응"}
            ],
            "success_count": 2,
            "failure_count": 0
        }
        
        # 캐시에 저장
        await cache_manager.set_async("sentiment_analysis", test_data, result)
        print("✅ 분석 결과 캐시에 저장")
    else:
        print(f"💾 캐시 히트! {len(cached_result.get('analyzed_results', []))}개 결과")
    
    elapsed = time.time() - start_time
    print(f"⏱️ 소요 시간: {elapsed:.3f}초")
    
    # 두 번째 호출 (캐시 히트 예상)
    print("\n두 번째 호출 (캐시 히트 예상):")
    start_time = time.time()
    cached_result = await cache_manager.get_async("sentiment_analysis", test_data)
    
    if cached_result:
        print(f"💾 캐시 히트! {len(cached_result.get('analyzed_results', []))}개 결과")
    else:
        print("❌ 캐시 미스 (예상치 못함)")
    
    elapsed = time.time() - start_time
    print(f"⏱️ 소요 시간: {elapsed:.3f}초 (캐시에서 즉시 반환)")

async def test_cache_invalidation():
    """캐시 무효화 테스트"""
    print("\n4. 캐시 무효화 테스트")
    print("-" * 50)
    
    # 테스트 티커
    ticker = "AAPL"
    
    # 여러 종류의 캐시 데이터 생성
    cache_entries = [
        ("ticker_extraction", {"query": f"{ticker} 주가"}),
        ("news_data", {"ticker": ticker}),
        ("sentiment_analysis", {"ticker": ticker, "data_hash": "abc123"}),
        ("final_report", {"ticker": ticker, "date": "2024-01-01"})
    ]
    
    print(f"테스트 데이터 생성 중...")
    for namespace, params in cache_entries:
        test_data = {"namespace": namespace, "ticker": ticker, "timestamp": time.time()}
        await cache_manager.set_async(namespace, params, test_data)
        print(f"  ✅ {namespace} 캐시 생성")
    
    # 통계 확인
    stats = await cache_manager.get_stats()
    print(f"\n캐시 통계:")
    print(f"  - 활성화: {stats.get('enabled', False)}")
    print(f"  - 연결 상태: {stats.get('connected', False)}")
    print(f"  - 메모리 사용: {stats.get('memory_used', 'N/A')}")
    print(f"  - 전체 키 수: {stats.get('total_keys', 0)}")
    
    # 티커 관련 캐시 무효화
    print(f"\n{ticker} 관련 캐시 무효화 중...")
    await cache_manager.invalidate_ticker(ticker)
    
    # 캐시 확인
    print(f"\n무효화 후 캐시 확인:")
    for namespace, params in cache_entries:
        result = await cache_manager.get_async(namespace, params)
        if result:
            print(f"  ❌ {namespace} - 여전히 존재함")
        else:
            print(f"  ✅ {namespace} - 삭제됨")

async def test_cache_ttl():
    """캐시 TTL 테스트"""
    print("\n5. 캐시 TTL 테스트")
    print("-" * 50)
    
    # 짧은 TTL로 임시 설정 변경
    original_ttl = cache_manager.ttl_settings["news_data"]
    cache_manager.ttl_settings["news_data"] = 2  # 2초
    
    try:
        # 데이터 저장
        test_data = {"ticker": "TSLA", "news": "테스트 뉴스"}
        params = {"ticker": "TSLA"}
        
        await cache_manager.set_async("news_data", params, test_data)
        print("✅ 뉴스 데이터 캐시 저장 (TTL: 2초)")
        
        # 즉시 조회
        result = await cache_manager.get_async("news_data", params)
        if result:
            print("✅ 즉시 조회 성공")
        
        # 3초 대기
        print("⏳ 3초 대기 중...")
        await asyncio.sleep(3)
        
        # 만료 후 조회
        result = await cache_manager.get_async("news_data", params)
        if not result:
            print("✅ TTL 만료 후 캐시 자동 삭제 확인")
        else:
            print("❌ TTL이 작동하지 않음")
            
    finally:
        # 원래 TTL로 복원
        cache_manager.ttl_settings["news_data"] = original_ttl

async def main():
    """메인 테스트 함수"""
    print("🚀 Redis 캐싱 시스템 테스트 시작")
    print("=" * 60)
    
    # Redis 연결 테스트
    if not await test_redis_connection():
        print("\n❌ Redis 연결 실패. Redis 서버가 실행 중인지 확인하세요.")
        print("   brew services start redis  # macOS")
        print("   sudo systemctl start redis  # Linux")
        return
    
    # 각 기능 테스트
    await test_ticker_caching()
    await test_sentiment_caching()
    await test_cache_invalidation()
    await test_cache_ttl()
    
    # 최종 통계
    print("\n" + "=" * 60)
    print("📊 최종 캐시 통계")
    stats = await cache_manager.get_stats()
    print(f"  - 캐시 히트율: {stats.get('hit_rate', 'N/A')}")
    print(f"  - 네임스페이스별 키 수:")
    for ns, count in stats.get('namespace_counts', {}).items():
        print(f"    - {ns}: {count}개")
    
    print("\n✅ 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())