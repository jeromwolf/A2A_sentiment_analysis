"""
설정 관리자
YAML 설정 파일과 환경 변수를 통합 관리하는 싱글톤 클래스
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

from .errors import MissingConfigError, InvalidConfigError

logger = logging.getLogger(__name__)

class ConfigManager:
    """설정 관리 싱글톤 클래스"""
    _instance = None
    _config = None
    _env_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """ConfigManager 초기화"""
        if not self._env_loaded:
            # .env 파일 로드
            load_dotenv()
            self._env_loaded = True
            
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """설정 파일 로드"""
        # 설정 파일 경로 찾기
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        if not config_path.exists():
            logger.warning(f"Config file not found at {config_path}. Using defaults.")
            self._config = self._get_default_config()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            self._config = self._get_default_config()
        
        # 환경 변수로 덮어쓰기
        self._override_with_env_vars()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "system": {
                "name": "A2A Investment Analysis System",
                "version": "3.0",
                "debug": False,
                "log_level": "INFO"
            },
            "agents": {
                "news": {"port": 8307, "timeout": 30},
                "twitter": {"port": 8209, "timeout": 30},
                "sec": {"port": 8210, "timeout": 60},
                "sentiment_analysis": {"port": 8202, "timeout": 120},
                "quantitative": {"port": 8211, "timeout": 30},
                "score_calculation": {"port": 8203, "timeout": 30},
                "risk_analysis": {"port": 8212, "timeout": 30},
                "report_generation": {"port": 8204, "timeout": 60}
            },
            "weights": {
                "sec": 1.5,
                "news": 1.0,
                "twitter": 0.7
            }
        }
    
    def _override_with_env_vars(self):
        """환경 변수로 설정 덮어쓰기"""
        # 환경 설정
        env = os.getenv("ENVIRONMENT", "production")
        if env in self._config.get("environments", {}):
            env_config = self._config["environments"][env]
            self._merge_config(self._config, env_config)
        
        # 개별 환경 변수 적용
        if os.getenv("DEBUG", "").lower() == "true":
            self._config["system"]["debug"] = True
            
        if os.getenv("LOG_LEVEL"):
            self._config["system"]["log_level"] = os.getenv("LOG_LEVEL")
            
        # USE_MOCK_DATA 환경 변수 처리 - 환경 설정보다 우선순위 높음
        if os.getenv("USE_MOCK_DATA") is not None:
            use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
            self._config["system"]["use_mock_data"] = use_mock
    
    def _merge_config(self, base: Dict, override: Dict):
        """설정 병합 (override가 base를 덮어씀)"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        점 표기법으로 설정 값 가져오기
        예: config.get("agents.news.port") -> 8307
        """
        keys = key_path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def get_required(self, key_path: str) -> Any:
        """필수 설정 값 가져오기 (없으면 에러)"""
        value = self.get(key_path)
        if value is None:
            raise MissingConfigError(key_path)
        return value
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """특정 에이전트의 설정 가져오기"""
        agent_config = self.get(f"agents.{agent_name}", {})
        
        # 기본값 추가
        defaults = {
            "timeout": 30,
            "max_retries": 3,
            "port": None
        }
        
        return {**defaults, **agent_config}
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """특정 API의 설정 가져오기"""
        return self.get(f"api.{api_name}", {})
    
    def get_weights(self) -> Dict[str, float]:
        """데이터 소스별 가중치 가져오기"""
        return self.get("weights", {})
    
    def get_env(self, key: str, default: str = None) -> Optional[str]:
        """환경 변수 가져오기"""
        return os.getenv(key, default)
    
    def get_env_required(self, key: str) -> str:
        """필수 환경 변수 가져오기"""
        value = os.getenv(key)
        if not value:
            raise MissingConfigError(f"Environment variable: {key}")
        return value
    
    def is_debug(self) -> bool:
        """디버그 모드 여부"""
        return self.get("system.debug", False)
    
    def is_mock_data_enabled(self) -> bool:
        """더미 데이터 사용 여부"""
        return self.get("system.use_mock_data", False)
    
    def get_log_level(self) -> str:
        """로그 레벨 가져오기"""
        return self.get("system.log_level", "INFO")
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """캐시 TTL 가져오기 (초 단위)"""
        return self.get(f"cache.ttl.{cache_type}", 300)
    
    def get_rate_limit(self, api_name: str) -> Dict[str, Any]:
        """API rate limit 설정 가져오기"""
        return self.get(f"api.rate_limits.{api_name}", {})
    
    def validate_config(self):
        """설정 유효성 검증"""
        # 필수 환경 변수 체크
        required_env_vars = [
            "GEMINI_API_KEY",
            "FINNHUB_API_KEY",
            "SEC_API_USER_AGENT"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var) and not self.is_mock_data_enabled():
                logger.warning(f"Missing required environment variable: {var}")
        
        # 포트 번호 중복 체크
        ports = set()
        for agent_name, agent_config in self.get("agents", {}).items():
            port = agent_config.get("port")
            if port:
                if port in ports:
                    raise InvalidConfigError(f"agents.{agent_name}.port", f"Port {port} is already in use")
                ports.add(port)
        
        logger.info("Configuration validation completed")
    
    def reload(self):
        """설정 다시 로드"""
        self._config = None
        self._load_config()
        logger.info("Configuration reloaded")


# 전역 설정 관리자 인스턴스
config = ConfigManager()