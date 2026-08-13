"""Custom exceptions used across the backend so FastAPI can translate them
into clean, user-friendly JSON error responses instead of raw tracebacks."""

from __future__ import annotations


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 500
    detail: str = "Something went wrong. Please try again."

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code
        super().__init__(self.detail)


class InvalidURLError(AppError):
    status_code = 400
    detail = "Please provide a valid product URL."


class WebsiteUnreachableError(AppError):
    status_code = 502
    detail = "Unable to access the product webpage."


class ExtractionFailedError(AppError):
    status_code = 422
    detail = "Product information could not be extracted from this webpage."


class AIServiceUnavailableError(AppError):
    status_code = 503
    detail = "AI extraction is temporarily unavailable. Please try again."


class AIQuotaExceededError(AppError):
    status_code = 429
    detail = "AI service quota has been exceeded. Please try again later."


class InsufficientListingsError(AppError):
    status_code = 400
    detail = "Please provide at least two product URLs to compare."
