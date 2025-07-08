"""
LLM Manager - 다양한 LLM 제공자를 통합 관리하는 모듈
"""
import os
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# OpenAI
try:
    import openai
except ImportError:
    openai = None

# Ollama (Gemma3 등 로컬 모델용)
try:
    import ollama
except ImportError:
    ollama = None

load_dotenv(override=True)
logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM 제공자 추상 클래스"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini 제공자"""
    
    def __init__(self, api_key: str):
        if not genai:
            raise ImportError("google-generativeai 패키지가 설치되지 않았습니다")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        from google.api_core import exceptions
        
        max_retries = 3
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                # generate_content is synchronous, so we run it in a thread
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, self.model.generate_content, prompt)
                return response.text
            except exceptions.ResourceExhausted as e:
                logger.error(f"Gemini API 할당량 초과 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"{retry_delay}초 후 재시도...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # exponential backoff
                else:
                    # 최종 실패 시 기본 응답 반환
                    logger.error("Gemini API 할당량 초과로 기본 응답 반환")
                    return '{"summary": "API 할당량 초과", "score": 0.0}'
            except Exception as e:
                logger.error(f"Gemini 생성 오류: {e}")
                raise
    
    def is_available(self) -> bool:
        return genai is not None and os.getenv("GEMINI_API_KEY")


class Gemma3Provider(LLMProvider):
    """Gemma3 로컬 모델 제공자 (Ollama 사용)"""
    
    def __init__(self, model_name: str = "gemma3:latest"):
        if not ollama:
            raise ImportError("ollama 패키지가 설치되지 않았습니다. pip install ollama")
        
        self.model_name = model_name
        self.client = ollama.Client()
        
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        try:
            # ollama client.generate is synchronous, so run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.generate(model=self.model_name, prompt=prompt)
            )
            return response['response']
        except Exception as e:
            logger.error(f"Gemma3 생성 오류: {e}")
            raise
    
    def is_available(self) -> bool:
        if not ollama:
            return False
        
        try:
            # Ollama가 실행 중이고 모델이 있는지 확인
            models = self.client.list()
            return any(self.model_name in model['name'] for model in models['models'])
        except:
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 제공자"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        if not openai:
            raise ImportError("openai 패키지가 설치되지 않았습니다")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI 생성 오류: {e}")
            raise
    
    def is_available(self) -> bool:
        return openai is not None and os.getenv("OPENAI_API_KEY")


class LLMManager:
    """LLM 관리자 - 설정에 따라 적절한 LLM 제공자 선택"""
    
    def __init__(self):
        self.provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.provider = self._create_provider()
        
    def _create_provider(self) -> LLMProvider:
        """설정된 제공자 생성"""
        logger.info(f"🤖 LLM 제공자 초기화: {self.provider_name}")
        
        if self.provider_name == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다")
            return GeminiProvider(api_key)
            
        elif self.provider_name == "gemma3":
            return Gemma3Provider()
            
        elif self.provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
            return OpenAIProvider(api_key)
            
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {self.provider_name}")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        return await self.provider.generate(prompt, **kwargs)
    
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        return self.provider.is_available()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """현재 제공자 정보"""
        return {
            "provider": self.provider_name,
            "available": self.is_available(),
            "class": self.provider.__class__.__name__
        }


# 싱글톤 인스턴스
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """LLM 관리자 싱글톤 인스턴스 반환"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager