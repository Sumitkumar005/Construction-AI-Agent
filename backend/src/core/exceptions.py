"""Custom exceptions for the application."""

class BaseAppException(Exception):
    """Base exception for application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(BaseAppException):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(BaseAppException):
    """Resource not found error."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ProcessingError(BaseAppException):
    """Processing error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class FileError(BaseAppException):
    """File handling error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


