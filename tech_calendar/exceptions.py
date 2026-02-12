"""
Custom exceptions for the tech-calendar application.
"""


class ConfigError(Exception):
    """
    Raised when configuration is missing or invalid.
    """


class StorageError(Exception):
    """
    Raised when persistent storage operations fail.
    """


class LLMError(Exception):
    """
    Raised when AI retrieval fails or returns invalid data.
    """


class OrchestrationError(Exception):
    """
    Raised when orchestration encounters an unrecoverable issue.
    """
