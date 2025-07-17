"""
번역 매니저 - DeepL 및 Google Translate API 통합
"""

import os
import httpx
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
import time
import hashlib
import asyncio

logger = logging.getLogger(__name__)


class TranslationProvider(Enum):
    DEEPL = "deepl"
    GOOGLE = "google"
    NONE = "none"


class TranslationManager:
    """번역 서비스 관리자"""
    
    def __init__(self):
        # API 키 로드
        self.deepl_api_key = os.getenv("DEEPL_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        
        # 우선순위 설정
        self.provider_priority = [TranslationProvider.DEEPL, TranslationProvider.GOOGLE]
        
        # 캐시 설정 (메모리 캐시)
        self.translation_cache: Dict[str, str] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # API 엔드포인트
        self.deepl_endpoint = "https://api-free.deepl.com/v2/translate"
        self.google_endpoint = "https://translation.googleapis.com/language/translate/v2"
        
        # HTTP 클라이언트
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # 사용 가능한 프로바이더 확인
        self.available_providers = self._check_available_providers()
        
    def _check_available_providers(self) -> List[TranslationProvider]:
        """사용 가능한 번역 프로바이더 확인"""
        available = []
        
        if self.deepl_api_key:
            available.append(TranslationProvider.DEEPL)
            logger.info("✅ DeepL 번역 API 활성화")
            
        if self.google_api_key:
            available.append(TranslationProvider.GOOGLE)
            logger.info("✅ Google Translate API 활성화")
            
        if not available:
            logger.warning("⚠️ 번역 API 키가 설정되지 않음 - 번역 기능 비활성화")
            available.append(TranslationProvider.NONE)
            
        return available
    
    def _get_cache_key(self, text: str, target_lang: str) -> str:
        """캐시 키 생성"""
        content = f"{text}:{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def translate(self, text: str, target_lang: str = "ko", source_lang: str = "en") -> str:
        """텍스트 번역 (자동 폴백)"""
        # 빈 텍스트 체크
        if not text or not text.strip():
            return text
            
        # 캐시 확인
        cache_key = self._get_cache_key(text, target_lang)
        if cache_key in self.translation_cache:
            self.cache_hits += 1
            return self.translation_cache[cache_key]
        
        self.cache_misses += 1
        
        # 프로바이더 순서대로 시도
        for provider in self.available_providers:
            if provider == TranslationProvider.NONE:
                return text  # 번역 불가 - 원본 반환
                
            try:
                if provider == TranslationProvider.DEEPL:
                    result = await self._translate_deepl(text, target_lang, source_lang)
                elif provider == TranslationProvider.GOOGLE:
                    result = await self._translate_google(text, target_lang, source_lang)
                else:
                    continue
                    
                # 캐시 저장
                self.translation_cache[cache_key] = result
                return result
                
            except Exception as e:
                logger.warning(f"번역 실패 ({provider.value}): {str(e)}")
                continue
        
        # 모든 번역 실패 시 원본 반환
        return text
    
    async def _translate_deepl(self, text: str, target_lang: str, source_lang: str) -> str:
        """DeepL API를 사용한 번역"""
        # DeepL 언어 코드 매핑
        lang_map = {
            "ko": "KO",
            "en": "EN",
            "ja": "JA",
            "zh": "ZH",
            "es": "ES",
            "fr": "FR",
            "de": "DE"
        }
        
        target_code = lang_map.get(target_lang, target_lang.upper())
        source_code = lang_map.get(source_lang, source_lang.upper()) if source_lang else None
        
        params = {
            "auth_key": self.deepl_api_key,
            "text": text,
            "target_lang": target_code
        }
        
        if source_code:
            params["source_lang"] = source_code
            
        response = await self.client.post(self.deepl_endpoint, data=params)
        response.raise_for_status()
        
        result = response.json()
        return result["translations"][0]["text"]
    
    async def _translate_google(self, text: str, target_lang: str, source_lang: str) -> str:
        """Google Translate API를 사용한 번역"""
        params = {
            "key": self.google_api_key,
            "q": text,
            "target": target_lang,
            "format": "text"
        }
        
        if source_lang:
            params["source"] = source_lang
            
        response = await self.client.post(self.google_endpoint, json=params)
        response.raise_for_status()
        
        result = response.json()
        return result["data"]["translations"][0]["translatedText"]
    
    async def translate_batch(self, texts: List[str], target_lang: str = "ko", 
                            source_lang: str = "en") -> List[str]:
        """여러 텍스트 일괄 번역"""
        # DeepL은 배치 번역 지원
        if TranslationProvider.DEEPL in self.available_providers and self.deepl_api_key:
            try:
                return await self._translate_batch_deepl(texts, target_lang, source_lang)
            except Exception as e:
                logger.warning(f"배치 번역 실패, 개별 번역으로 전환: {str(e)}")
        
        # 개별 번역 폴백
        results = []
        for text in texts:
            translated = await self.translate(text, target_lang, source_lang)
            results.append(translated)
            # Rate limit 방지
            await asyncio.sleep(0.1)
            
        return results
    
    async def _translate_batch_deepl(self, texts: List[str], target_lang: str, 
                                   source_lang: str) -> List[str]:
        """DeepL 배치 번역"""
        lang_map = {
            "ko": "KO",
            "en": "EN",
            "ja": "JA",
            "zh": "ZH"
        }
        
        target_code = lang_map.get(target_lang, target_lang.upper())
        source_code = lang_map.get(source_lang, source_lang.upper()) if source_lang else None
        
        # DeepL은 text 파라미터를 여러 개 보낼 수 있음
        data = {
            "auth_key": self.deepl_api_key,
            "target_lang": target_code
        }
        
        if source_code:
            data["source_lang"] = source_code
            
        # 여러 text 파라미터 추가
        for text in texts:
            data[f"text"] = text
            
        response = await self.client.post(
            self.deepl_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        result = response.json()
        return [t["text"] for t in result["translations"]]
    
    def get_stats(self) -> Dict[str, Any]:
        """번역 통계 반환"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "available_providers": [p.value for p in self.available_providers],
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "cached_translations": len(self.translation_cache)
        }
    
    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()


# 싱글톤 인스턴스
translation_manager = TranslationManager()


# 헬퍼 함수
async def translate_text(text: str, target_lang: str = "ko") -> str:
    """간편 번역 함수"""
    return await translation_manager.translate(text, target_lang)


async def translate_texts(texts: List[str], target_lang: str = "ko") -> List[str]:
    """간편 배치 번역 함수"""
    return await translation_manager.translate_batch(texts, target_lang)