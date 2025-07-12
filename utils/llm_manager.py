"""
LLM Manager - 다중 LLM 프로바이더 관리 및 자동 폴백
토큰/쿼터 관리, 비용 최적화, 작업별 모델 선택
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import httpx
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

# Anthropic
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

# Ollama (Gemma3 등 로컬 모델용)
try:
    import ollama
except ImportError:
    ollama = None

from utils.config_manager import config
from utils.errors import APIError, APIRateLimitError

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# 작업 복잡도 타입
ComplexityLevel = Literal["light", "medium", "heavy"]
TaskType = Literal["sentiment", "summary", "financial_analysis", "report_generation", "general"]


class UsageTracker:
    """API 사용량 추적기"""
    def __init__(self):
        self.usage = {}
        
    def track(self, provider: str, tokens: int, cost: float = 0.0):
        if provider not in self.usage:
            self.usage[provider] = {"tokens": 0, "requests": 0, "cost": 0.0}
        self.usage[provider]["tokens"] += tokens
        self.usage[provider]["requests"] += 1
        self.usage[provider]["cost"] += cost
        
    def get_usage(self, provider: str) -> Dict:
        return self.usage.get(provider, {"tokens": 0, "requests": 0, "cost": 0.0})


class LLMProvider(ABC):
    """LLM 제공자 추상 클래스"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.priority = 0  # 낮을수록 우선순위 높음
        self.last_error_time = None
        self.error_count = 0
        self.max_retries = 3
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """토큰 수 추정"""
        pass
    
    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        if self.last_error_time:
            # 5분 이내 3회 이상 오류 시 사용 중단
            if (datetime.now() - self.last_error_time).seconds < 300:
                return self.error_count < self.max_retries
        return True
    
    def record_error(self):
        """오류 기록"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
    def reset_errors(self):
        """오류 카운터 리셋"""
        self.error_count = 0
        self.last_error_time = None


class GeminiProvider(LLMProvider):
    """Google Gemini 제공자"""
    
    def __init__(self, api_key: str):
        super().__init__()
        if not genai:
            raise ImportError("google-generativeai 패키지가 설치되지 않았습니다")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.priority = 0  # 최우선
        
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        from google.api_core import exceptions
        
        try:
            # generate_content is synchronous, so we run it in a thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            self.reset_errors()  # 성공 시 에러 카운터 리셋
            return response.text
        except exceptions.ResourceExhausted as e:
            logger.error(f"Gemini API 할당량 초과: {e}")
            self.record_error()
            raise APIRateLimitError("Gemini", str(e))
        except Exception as e:
            logger.error(f"Gemini 생성 오류: {e}")
            self.record_error()
            raise APIError("Gemini", str(e))
    
    def is_available(self) -> bool:
        return genai is not None and os.getenv("GEMINI_API_KEY") and self.can_retry()
    
    def estimate_tokens(self, text: str) -> int:
        # 대략적인 추정 (평균 4자 = 1토큰)
        return len(text) // 4


class Gemma3Provider(LLMProvider):
    """Gemma3 로컬 모델 제공자 (Ollama 사용)"""
    
    def __init__(self, model_name: str = "gemma3:latest"):
        super().__init__()
        if not ollama:
            raise ImportError("ollama 패키지가 설치되지 않았습니다. pip install ollama")
        
        self.model_name = model_name
        self.client = ollama.Client()
        self.priority = 3  # 로컬 모델은 낮은 우선순위
        
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        try:
            # ollama client.generate is synchronous, so run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.generate(model=self.model_name, prompt=prompt)
            )
            self.reset_errors()
            return response['response']
        except Exception as e:
            logger.error(f"Gemma3 생성 오류: {e}")
            self.record_error()
            raise APIError("Gemma3", str(e))
    
    def is_available(self) -> bool:
        if not ollama:
            return False
        
        try:
            # Ollama가 실행 중이고 모델이 있는지 확인
            models = self.client.list()
            return any(self.model_name in model['name'] for model in models['models']) and self.can_retry()
        except:
            return False
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 제공자"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        super().__init__()
        if not openai:
            raise ImportError("openai 패키지가 설치되지 않았습니다")
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.priority = 1  # Gemini 다음 우선순위
        
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            self.reset_errors()
            return response.choices[0].message.content
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API 할당량 초과: {e}")
            self.record_error()
            raise APIRateLimitError("OpenAI", str(e))
        except Exception as e:
            logger.error(f"OpenAI 생성 오류: {e}")
            self.record_error()
            raise APIError("OpenAI", str(e))
    
    def is_available(self) -> bool:
        return openai is not None and os.getenv("OPENAI_API_KEY") and self.can_retry()
    
    def estimate_tokens(self, text: str) -> int:
        # tiktoken을 사용한 정확한 계산도 가능하지만 간단히 추정
        return len(text) // 4


class AnthropicProvider(LLMProvider):
    """Anthropic Claude 제공자"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__()
        if not AsyncAnthropic:
            raise ImportError("anthropic 패키지가 설치되지 않았습니다")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.priority = 2  # OpenAI 다음 우선순위
        
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            # Anthropic API 형식에 맞게 변환
            max_tokens = kwargs.pop("max_tokens", 4096)
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            self.reset_errors()
            return response.content[0].text
        except Exception as e:
            if "rate_limit" in str(e).lower():
                logger.error(f"Anthropic API 할당량 초과: {e}")
                self.record_error()
                raise APIRateLimitError("Anthropic", str(e))
            else:
                logger.error(f"Anthropic 생성 오류: {e}")
                self.record_error()
                raise APIError("Anthropic", str(e))
    
    def is_available(self) -> bool:
        return AsyncAnthropic is not None and os.getenv("ANTHROPIC_API_KEY") and self.can_retry()
    
    def estimate_tokens(self, text: str) -> int:
        # Claude의 토큰 계산 방식
        return len(text) // 4


class LLMManager:
    """멀티 프로바이더 LLM 관리자 - 자동 폴백 지원"""
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.usage_tracker = UsageTracker()
        self._initialize_providers()
        
    def _initialize_providers(self):
        """사용 가능한 모든 프로바이더 초기화"""
        
        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                self.providers.append(GeminiProvider(gemini_key))
                logger.info("✅ Gemini 프로바이더 활성화")
            except Exception as e:
                logger.warning(f"⚠️ Gemini 프로바이더 초기화 실패: {e}")
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.providers.append(OpenAIProvider(openai_key))
                logger.info("✅ OpenAI 프로바이더 활성화")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI 프로바이더 초기화 실패: {e}")
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                self.providers.append(AnthropicProvider(anthropic_key))
                logger.info("✅ Anthropic 프로바이더 활성화")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic 프로바이더 초기화 실패: {e}")
        
        # Ollama (로컬)
        try:
            provider = Gemma3Provider()
            if provider.is_available():
                self.providers.append(provider)
                logger.info("✅ Ollama 프로바이더 활성화")
        except Exception as e:
            logger.debug(f"Ollama 프로바이더 사용 불가: {e}")
        
        # 우선순위로 정렬
        self.providers.sort(key=lambda p: p.priority)
        
        if not self.providers:
            raise ValueError("사용 가능한 LLM 프로바이더가 없습니다. API 키를 확인해주세요.")
        
        logger.info(f"🤖 총 {len(self.providers)}개의 LLM 프로바이더 활성화됨")
    
    async def generate(self, prompt: str, task_type: TaskType = "general", **kwargs) -> str:
        """텍스트 생성 - 자동 폴백 지원"""
        
        last_error = None
        
        # 현재 사용 가능한 프로바이더 확인 및 변경 감지
        current_provider = None
        for provider in self.providers:
            if provider.is_available():
                current_provider = provider.__class__.__name__
                # 프로바이더가 변경된 경우 로그
                if current_provider != getattr(self, '_last_used_provider', None):
                    provider_model = ""
                    if hasattr(provider, 'model'):
                        provider_model = f" ({provider.model})"
                    logger.info(f"🔄 LLM 프로바이더 변경: {current_provider}{provider_model}")
                    self._last_used_provider = current_provider
                break
        
        for provider in self.providers:
            if not provider.is_available():
                continue
                
            provider_name = provider.__class__.__name__
            logger.debug(f"🔄 {provider_name} 시도 중...")
            
            try:
                # 토큰 추정
                estimated_tokens = provider.estimate_tokens(prompt)
                
                # 생성 실행
                start_time = datetime.now()
                result = await provider.generate(prompt, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # 사용량 추적
                self.usage_tracker.track(
                    provider_name,
                    estimated_tokens,
                    self._estimate_cost(provider_name, estimated_tokens)
                )
                
                logger.debug(f"✅ {provider_name} 성공 (소요 시간: {elapsed:.2f}초)")
                return result
                
            except APIRateLimitError as e:
                logger.warning(f"⚠️ {provider_name} 할당량 초과: {e}")
                last_error = e
                continue
                
            except APIError as e:
                logger.error(f"❌ {provider_name} 오류: {e}")
                last_error = e
                continue
                
            except Exception as e:
                logger.error(f"❌ {provider_name} 예상치 못한 오류: {e}", exc_info=True)
                last_error = e
                continue
        
        # 모든 프로바이더 실패
        error_msg = "모든 LLM 프로바이더가 실패했습니다"
        if last_error:
            error_msg += f": {last_error}"
        
        logger.error(f"💥 {error_msg}")
        
        # 기본 응답 반환 (분석 에이전트를 위해)
        if task_type in ["sentiment", "summary"]:
            return json.dumps({
                "summary": "LLM 서비스를 사용할 수 없습니다",
                "score": 0.0,
                "error": error_msg
            })
        else:
            raise APIError("LLMManager", error_msg)
    
    def _estimate_cost(self, provider_name: str, tokens: int) -> float:
        """토큰당 비용 추정 (USD)"""
        costs_per_1k = {
            "GeminiProvider": 0.0,  # 무료 티어
            "OpenAIProvider": 0.03,  # GPT-4
            "AnthropicProvider": 0.015,  # Claude-3
            "Gemma3Provider": 0.0  # 로컬
        }
        return (tokens / 1000) * costs_per_1k.get(provider_name, 0.0)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """사용 통계 반환"""
        stats = {}
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            usage = self.usage_tracker.get_usage(provider_name)
            stats[provider_name] = {
                "available": provider.is_available(),
                "priority": provider.priority,
                "error_count": provider.error_count,
                "usage": usage
            }
        return stats
    
    def get_available_providers(self) -> List[str]:
        """사용 가능한 프로바이더 목록"""
        return [p.__class__.__name__ for p in self.providers if p.is_available()]
    
    def reset_all_errors(self):
        """모든 프로바이더의 오류 카운터 리셋"""
        for provider in self.providers:
            provider.reset_errors()
        logger.info("🔄 모든 프로바이더 오류 카운터 리셋")


# 싱글톤 인스턴스
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """LLM 관리자 싱글톤 인스턴스 반환"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager