"""Custom exceptions for AgentFormer

This module defines the exception hierarchy used throughout AgentFormer.
All custom exceptions inherit from AgentFormerException, which allows for:

1. Consistent error handling across the system
2. Easy identification of AgentFormer-specific errors
3. Hierarchical error categorization

Exception Categories:
- ConfigurationError: Configuration and setup errors
- InitializationError: Component initialization failures
- OperationError: Runtime operation errors
- MemoryError: Memory and storage related errors
- ModelError: ML model related errors
- APIError: External API communication errors

Usage:
    try:
        # Some AgentFormer operation
        raise ConfigurationError("Invalid model configuration")
    except AgentFormerException as e:
        # Handle any AgentFormer error
        logger.error(f"AgentFormer error: {str(e)}")
"""


class AgentFormerException(Exception):
    """Base exception for all AgentFormer errors"""

    pass


class ConfigurationError(AgentFormerException):
    """Configuration related errors"""

    pass


class InitializationError(AgentFormerException):
    """Error during initialization"""

    pass


class OperationError(AgentFormerException):
    """Error during operation"""

    pass


class MemoryError(AgentFormerException):
    """Memory related errors"""

    pass


class ModelError(AgentFormerException):
    """Model related errors"""

    pass


class APIError(AgentFormerException):
    """API related errors"""

    pass
