"""
커스텀 에러 클래스 정의
투자 분석 시스템에서 발생할 수 있는 다양한 에러를 체계적으로 관리
"""

class A2ABaseError(Exception):
    """A2A 시스템 기본 에러 클래스"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


# API 관련 에러
class APIError(A2ABaseError):
    """외부 API 호출 관련 에러"""
    pass


class APIRateLimitError(APIError):
    """API 요청 제한 초과 에러"""
    def __init__(self, api_name: str, retry_after: int = None):
        message = f"{api_name} API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(
            message=message,
            error_code="API_RATE_LIMIT",
            details={"api": api_name, "retry_after": retry_after}
        )


class APITimeoutError(APIError):
    """API 요청 타임아웃 에러"""
    def __init__(self, api_name: str, timeout: int):
        super().__init__(
            message=f"{api_name} API request timed out after {timeout} seconds",
            error_code="API_TIMEOUT",
            details={"api": api_name, "timeout": timeout}
        )


class APIAuthenticationError(APIError):
    """API 인증 실패 에러"""
    def __init__(self, api_name: str):
        super().__init__(
            message=f"{api_name} API authentication failed. Check your API key",
            error_code="API_AUTH_FAILED",
            details={"api": api_name}
        )


# 데이터 관련 에러
class DataError(A2ABaseError):
    """데이터 처리 관련 에러"""
    pass


class DataValidationError(DataError):
    """데이터 유효성 검증 실패 에러"""
    def __init__(self, field: str, expected_type: str, actual_value: any):
        super().__init__(
            message=f"Invalid data for field '{field}'. Expected {expected_type}, got {type(actual_value).__name__}",
            error_code="DATA_VALIDATION_ERROR",
            details={"field": field, "expected": expected_type, "actual": type(actual_value).__name__}
        )


class DataNotFoundError(DataError):
    """데이터를 찾을 수 없는 에러"""
    def __init__(self, data_type: str, identifier: str):
        super().__init__(
            message=f"{data_type} not found: {identifier}",
            error_code="DATA_NOT_FOUND",
            details={"data_type": data_type, "identifier": identifier}
        )


class InsufficientDataError(DataError):
    """분석에 필요한 데이터가 부족한 에러"""
    def __init__(self, data_type: str, required: int, actual: int):
        super().__init__(
            message=f"Insufficient {data_type} data. Required: {required}, Actual: {actual}",
            error_code="INSUFFICIENT_DATA",
            details={"data_type": data_type, "required": required, "actual": actual}
        )


# 에이전트 관련 에러
class AgentError(A2ABaseError):
    """에이전트 관련 에러"""
    pass


class AgentConnectionError(AgentError):
    """에이전트 연결 실패 에러"""
    def __init__(self, agent_name: str, endpoint: str):
        super().__init__(
            message=f"Failed to connect to {agent_name} at {endpoint}",
            error_code="AGENT_CONNECTION_ERROR",
            details={"agent": agent_name, "endpoint": endpoint}
        )


class AgentTimeoutError(AgentError):
    """에이전트 응답 타임아웃 에러"""
    def __init__(self, agent_name: str, timeout: int):
        super().__init__(
            message=f"{agent_name} agent did not respond within {timeout} seconds",
            error_code="AGENT_TIMEOUT",
            details={"agent": agent_name, "timeout": timeout}
        )


class AgentProcessingError(AgentError):
    """에이전트 처리 중 에러"""
    def __init__(self, agent_name: str, operation: str, reason: str):
        super().__init__(
            message=f"{agent_name} failed to {operation}: {reason}",
            error_code="AGENT_PROCESSING_ERROR",
            details={"agent": agent_name, "operation": operation, "reason": reason}
        )


# LLM 관련 에러
class LLMError(A2ABaseError):
    """LLM (Large Language Model) 관련 에러"""
    pass


class LLMResponseError(LLMError):
    """LLM 응답 형식 에러"""
    def __init__(self, provider: str, expected_format: str):
        super().__init__(
            message=f"{provider} returned invalid response format. Expected: {expected_format}",
            error_code="LLM_RESPONSE_ERROR",
            details={"provider": provider, "expected_format": expected_format}
        )


class LLMQuotaExceededError(LLMError):
    """LLM API 할당량 초과 에러"""
    def __init__(self, provider: str, reset_time: str = None):
        message = f"{provider} API quota exceeded"
        if reset_time:
            message += f". Resets at {reset_time}"
        super().__init__(
            message=message,
            error_code="LLM_QUOTA_EXCEEDED",
            details={"provider": provider, "reset_time": reset_time}
        )


# 설정 관련 에러
class ConfigurationError(A2ABaseError):
    """설정 관련 에러"""
    pass


class MissingConfigError(ConfigurationError):
    """필수 설정 누락 에러"""
    def __init__(self, config_key: str):
        super().__init__(
            message=f"Required configuration missing: {config_key}",
            error_code="MISSING_CONFIG",
            details={"config_key": config_key}
        )


class InvalidConfigError(ConfigurationError):
    """잘못된 설정 값 에러"""
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Invalid configuration for {config_key}: {reason}",
            error_code="INVALID_CONFIG",
            details={"config_key": config_key, "reason": reason}
        )


# 네트워크 관련 에러
class NetworkError(A2ABaseError):
    """네트워크 관련 에러"""
    pass


class WebSocketError(NetworkError):
    """WebSocket 연결 에러"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"WebSocket error: {reason}",
            error_code="WEBSOCKET_ERROR",
            details={"reason": reason}
        )


# 분석 관련 에러
class AnalysisError(A2ABaseError):
    """분석 처리 관련 에러"""
    pass


class SentimentAnalysisError(AnalysisError):
    """감정 분석 에러"""
    def __init__(self, source: str, reason: str):
        super().__init__(
            message=f"Sentiment analysis failed for {source}: {reason}",
            error_code="SENTIMENT_ANALYSIS_ERROR",
            details={"source": source, "reason": reason}
        )


class ScoreCalculationError(AnalysisError):
    """점수 계산 에러"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Score calculation failed: {reason}",
            error_code="SCORE_CALCULATION_ERROR",
            details={"reason": reason}
        )


class RiskAnalysisError(AnalysisError):
    """리스크 분석 에러"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Risk analysis failed: {reason}",
            error_code="RISK_ANALYSIS_ERROR",
            details={"reason": reason}
        )


class ReportGenerationError(AnalysisError):
    """리포트 생성 에러"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Report generation failed: {reason}",
            error_code="REPORT_GENERATION_ERROR",
            details={"reason": reason}
        )