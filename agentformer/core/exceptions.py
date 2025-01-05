"""Custom exceptions for AgentFormer"""


class AgentFormerError(Exception):
    """Base exception for AgentFormer"""

    pass


class MemoryError(AgentFormerError):
    """Memory related errors"""

    pass


class ModelError(AgentFormerError):
    """Model related errors"""

    pass


class APIError(AgentFormerError):
    """API related errors"""

    pass


class ConfigurationError(AgentFormerError):
    """Configuration related errors"""

    pass
