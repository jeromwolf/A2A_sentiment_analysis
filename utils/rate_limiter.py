"""
API Rate Limit 관리 및 재시도 로직
각 API 서비스별 요청 제한을 관리하고 자동 재시도 기능 제공
"""
import asyncio
import time
from typing import Dict, Optional, Callable, Any
from functools import wraps
import logging
from datetime import datetime, timedelta
import httpx

from utils.config_manager import config
from utils.errors import APIRateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class RateLimiter:
    """API별 요청 제한 관리 클래스"""
    
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.config = config.get(f"api.rate_limits.{api_name}", {})
        
        # 기본값 설정
        self.calls_per_minute = self.config.get("calls_per_minute", 60)
        self.calls_per_window = self.config.get("calls_per_window")
        self.window_minutes = self.config.get("window_minutes", 1)
        self.retry_delay = self.config.get("retry_delay", 2)
        self.max_retries = self.config.get("max_retries", 3)
        
        # 요청 추적
        self.request_times = []
        self.window_start = time.time()
        
        # 통계
        self.total_requests = 0
        self.rate_limited_count = 0
        
    def _clean_old_requests(self):
        """오래된 요청 기록 정리"""
        current_time = time.time()
        window_size = self.window_minutes * 60
        
        # 윈도우 크기보다 오래된 요청 제거
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < window_size
        ]
    
    async def check_rate_limit(self) -> bool:
        """요청 가능 여부 확인"""
        self._clean_old_requests()
        
        current_time = time.time()
        
        # 분당 요청 제한 확인
        if self.calls_per_minute:
            recent_requests = [
                t for t in self.request_times 
                if current_time - t < 60
            ]
            if len(recent_requests) >= self.calls_per_minute:
                return False
        
        # 윈도우별 요청 제한 확인
        if self.calls_per_window:
            if len(self.request_times) >= self.calls_per_window:
                return False
        
        return True
    
    async def wait_if_needed(self):
        """필요시 대기"""
        while not await self.check_rate_limit():
            self.rate_limited_count += 1
            wait_time = self.retry_delay
            
            # 다음 가능 시간 계산
            if self.request_times:
                oldest_request = min(self.request_times)
                next_available = oldest_request + (self.window_minutes * 60)
                wait_time = max(wait_time, next_available - time.time() + 1)
            
            logger.warning(
                f"🚦 {self.api_name} Rate limit reached. "
                f"Waiting {wait_time:.1f} seconds..."
            )
            
            await asyncio.sleep(wait_time)
            self._clean_old_requests()
    
    def record_request(self):
        """요청 기록"""
        self.request_times.append(time.time())
        self.total_requests += 1
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        return {
            "api": self.api_name,
            "total_requests": self.total_requests,
            "rate_limited_count": self.rate_limited_count,
            "current_window_requests": len(self.request_times),
            "calls_per_minute": self.calls_per_minute,
            "calls_per_window": self.calls_per_window
        }


class APIClient:
    """Rate Limit이 적용된 API 클라이언트"""
    
    def __init__(self, api_name: str, base_url: str = None, headers: Dict = None):
        self.api_name = api_name
        self.base_url = base_url
        self.headers = headers or {}
        self.rate_limiter = RateLimiter(api_name)
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def request(
        self,
        method: str,
        url: str,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> httpx.Response:
        """Rate limit과 재시도 로직이 적용된 요청"""
        if max_retries is None:
            max_retries = self.rate_limiter.max_retries
        
        # URL 구성
        if self.base_url and not url.startswith("http"):
            url = f"{self.base_url}/{url.lstrip('/')}"
        
        # 헤더 병합
        headers = {**self.headers, **kwargs.get("headers", {})}
        kwargs["headers"] = headers
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limit 확인 및 대기
                await self.rate_limiter.wait_if_needed()
                
                # 요청 실행
                logger.debug(f"🌐 {self.api_name} {method} {url} (Attempt {attempt + 1})")
                response = await self.client.request(method, url, **kwargs)
                
                # 요청 기록
                self.rate_limiter.record_request()
                
                # 429 (Too Many Requests) 처리
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.rate_limiter.retry_delay))
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ {self.api_name} returned 429. "
                            f"Retrying after {retry_after} seconds..."
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise APIRateLimitError(self.api_name, retry_after)
                
                # 5xx 에러는 재시도
                if 500 <= response.status_code < 600 and attempt < max_retries:
                    wait_time = self.rate_limiter.retry_delay * (attempt + 1)
                    logger.warning(
                        f"⚠️ {self.api_name} returned {response.status_code}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                # 성공 또는 4xx 에러는 그대로 반환
                response.raise_for_status()
                return response
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = self.rate_limiter.retry_delay * (attempt + 1)
                    logger.warning(
                        f"⏱️ {self.api_name} timeout. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise APITimeoutError(self.api_name, 30)
                    
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = self.rate_limiter.retry_delay * (attempt + 1)
                    logger.error(
                        f"❌ {self.api_name} error: {str(e)}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        # 모든 재시도 실패
        if last_error:
            raise last_error
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET 요청"""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST 요청"""
        return await self.request("POST", url, **kwargs)
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def rate_limited(api_name: str):
    """Rate limit 데코레이터"""
    rate_limiter = RateLimiter(api_name)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limit 확인 및 대기
            await rate_limiter.wait_if_needed()
            
            try:
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 요청 기록
                rate_limiter.record_request()
                
                return result
                
            except Exception as e:
                # 429 에러 처리
                if hasattr(e, "response") and e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", rate_limiter.retry_delay))
                    raise APIRateLimitError(api_name, retry_after)
                raise
        
        return wrapper
    return decorator


# 전역 Rate Limiter 인스턴스
rate_limiters = {}

def get_rate_limiter(api_name: str) -> RateLimiter:
    """Rate Limiter 인스턴스 가져오기"""
    if api_name not in rate_limiters:
        rate_limiters[api_name] = RateLimiter(api_name)
    return rate_limiters[api_name]


# 통계 수집
def get_all_stats() -> Dict[str, Dict]:
    """모든 API의 통계 반환"""
    return {
        api_name: limiter.get_stats()
        for api_name, limiter in rate_limiters.items()
    }