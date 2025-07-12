"""
Redis 캐시 매니저

분석 결과를 캐싱하여 성능을 향상시킵니다.
"""

import json
import hashlib
from typing import Optional, Any, Dict, Union
from datetime import timedelta
import redis
from redis import asyncio as aioredis
import logging
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis 기반 캐시 매니저"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.redis_url = self.config.get_env("REDIS_URL", "redis://localhost:6379")
        self.enabled = self.config.get_env("CACHE_ENABLED", "true").lower() == "true"
        
        # 캐시가 활성화된 경우에만 TTL 파싱
        if self.enabled:
            cache_ttl = self.config.get_env("CACHE_TTL", "3600")
            # 주석 제거 (만약 있다면)
            if isinstance(cache_ttl, str) and '#' in cache_ttl:
                cache_ttl = cache_ttl.split('#')[0].strip()
            self.default_ttl = int(cache_ttl)
        else:
            self.default_ttl = 3600  # 기본값
        
        # 동기/비동기 클라이언트
        self._sync_client = None
        self._async_client = None
        
        # 캐시 접두사
        self.prefix = "a2a:"
        
        # 캐시 TTL 설정 (초 단위)
        self.ttl_settings = {
            "ticker_extraction": 86400,  # 24시간
            "news_data": 300,           # 5분
            "twitter_data": 180,        # 3분
            "sec_data": 3600,           # 1시간
            "sentiment_analysis": 600,   # 10분
            "quantitative_data": 60,    # 1분
            "risk_analysis": 600,       # 10분
            "final_report": 1800,       # 30분
        }
        
    @property
    def sync_client(self) -> redis.Redis:
        """동기 Redis 클라이언트"""
        if not self._sync_client:
            self._sync_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return self._sync_client
    
    @property
    async def async_client(self) -> aioredis.Redis:
        """비동기 Redis 클라이언트"""
        if not self._async_client:
            self._async_client = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return self._async_client
    
    def _generate_key(self, namespace: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = json.dumps(params, sort_keys=True)
        hash_digest = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{self.prefix}{namespace}:{hash_digest}"
    
    def _get_ttl(self, namespace: str) -> int:
        """네임스페이스별 TTL 반환"""
        return self.ttl_settings.get(namespace, self.default_ttl)
    
    # 동기 메서드들
    def get(self, namespace: str, params: Dict[str, Any]) -> Optional[Any]:
        """캐시에서 데이터 가져오기 (동기)"""
        if not self.enabled:
            return None
            
        try:
            key = self._generate_key(namespace, params)
            data = self.sync_client.get(key)
            
            if data:
                logger.info(f"캐시 히트: {namespace} - {key}")
                return json.loads(data)
            else:
                logger.info(f"캐시 미스: {namespace} - {key}")
                return None
                
        except Exception as e:
            logger.error(f"캐시 읽기 오류: {e}")
            return None
    
    def set(self, namespace: str, params: Dict[str, Any], data: Any) -> bool:
        """캐시에 데이터 저장 (동기)"""
        if not self.enabled:
            return False
            
        try:
            key = self._generate_key(namespace, params)
            ttl = self._get_ttl(namespace)
            
            self.sync_client.setex(
                key,
                ttl,
                json.dumps(data, ensure_ascii=False)
            )
            
            logger.info(f"캐시 저장: {namespace} - {key} (TTL: {ttl}초)")
            return True
            
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
            return False
    
    def delete(self, namespace: str, params: Dict[str, Any]) -> bool:
        """캐시 삭제 (동기)"""
        if not self.enabled:
            return False
            
        try:
            key = self._generate_key(namespace, params)
            result = self.sync_client.delete(key)
            logger.info(f"캐시 삭제: {namespace} - {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"캐시 삭제 오류: {e}")
            return False
    
    # 비동기 메서드들
    async def get_async(self, namespace: str, params: Dict[str, Any]) -> Optional[Any]:
        """캐시에서 데이터 가져오기 (비동기)"""
        if not self.enabled:
            return None
            
        try:
            client = await self.async_client
            key = self._generate_key(namespace, params)
            data = await client.get(key)
            
            if data:
                logger.info(f"캐시 히트: {namespace} - {key}")
                return json.loads(data)
            else:
                logger.info(f"캐시 미스: {namespace} - {key}")
                return None
                
        except Exception as e:
            logger.error(f"캐시 읽기 오류: {e}")
            return None
    
    async def set_async(self, namespace: str, params: Dict[str, Any], data: Any) -> bool:
        """캐시에 데이터 저장 (비동기)"""
        if not self.enabled:
            return False
            
        try:
            client = await self.async_client
            key = self._generate_key(namespace, params)
            ttl = self._get_ttl(namespace)
            
            await client.setex(
                key,
                ttl,
                json.dumps(data, ensure_ascii=False)
            )
            
            logger.info(f"캐시 저장: {namespace} - {key} (TTL: {ttl}초)")
            return True
            
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
            return False
    
    async def delete_async(self, namespace: str, params: Dict[str, Any]) -> bool:
        """캐시 삭제 (비동기)"""
        if not self.enabled:
            return False
            
        try:
            client = await self.async_client
            key = self._generate_key(namespace, params)
            result = await client.delete(key)
            logger.info(f"캐시 삭제: {namespace} - {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"캐시 삭제 오류: {e}")
            return False
    
    async def invalidate_ticker(self, ticker: str):
        """특정 티커 관련 모든 캐시 무효화"""
        if not self.enabled:
            return
            
        try:
            client = await self.async_client
            pattern = f"{self.prefix}*:*{ticker}*"
            
            # 패턴에 맞는 모든 키 찾기
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                    logger.info(f"티커 {ticker} 관련 {len(keys)}개 캐시 삭제")
                
                if cursor == 0:
                    break
                    
        except Exception as e:
            logger.error(f"티커 캐시 무효화 오류: {e}")
    
    async def clear_all(self):
        """모든 캐시 삭제"""
        if not self.enabled:
            return
            
        try:
            client = await self.async_client
            pattern = f"{self.prefix}*"
            
            # 패턴에 맞는 모든 키 찾기
            cursor = 0
            total_deleted = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                    total_deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"전체 캐시 삭제 완료: {total_deleted}개")
            
        except Exception as e:
            logger.error(f"전체 캐시 삭제 오류: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            client = await self.async_client
            info = await client.info()
            
            # 각 네임스페이스별 키 개수 계산
            namespace_counts = {}
            for namespace in self.ttl_settings.keys():
                pattern = f"{self.prefix}{namespace}:*"
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await client.scan(cursor, match=pattern, count=100)
                    count += len(keys)
                    if cursor == 0:
                        break
                namespace_counts[namespace] = count
            
            return {
                "enabled": True,
                "connected": True,
                "memory_used": info.get("used_memory_human", "N/A"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "namespace_counts": namespace_counts,
                "hit_rate": f"{info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1) * 100:.2f}%"
            }
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 오류: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}

# 싱글톤 인스턴스
cache_manager = CacheManager()