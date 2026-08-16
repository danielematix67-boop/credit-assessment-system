class LLMError(Exception):
    """Base exception for LLM-related failures."""


class LLMServiceUnavailableError(LLMError):
    """Raised when the LLM service is temporarily unavailable."""


class LLMRateLimitError(LLMError):
    """Raised when the LLM service rate limit or quota is exceeded."""


class LLMAuthenticationError(LLMError):
    """Raised when LLM authentication fails."""


class LLMPermissionError(LLMError):
    """Raised when access to the LLM service is denied."""


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""


class LLMResponseError(LLMError):
    """Raised when the LLM returns an invalid or unusable response."""