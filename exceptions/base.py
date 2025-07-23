import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ExceptionType(str, Enum):
    """异常类型枚举"""

    BUSINESS = "BUSINESS"  # 业务异常
    SYSTEM = "SYSTEM"  # 系统异常


class BaseException(Exception):
    """
    异常基类
    """

    def __init__(
        self,
        message: str,
        error_code: str = "BUSINESS_ERROR",
        exception_type: ExceptionType = ExceptionType.BUSINESS,
    ):
        self.message = message
        self.error_code = error_code
        self.exception_type = exception_type
        super().__init__(self.message)


class NotFoundException(BaseException):
    """资源未找到异常"""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND", ExceptionType.BUSINESS)


class DuplicateException(BaseException):
    """重复资源异常"""

    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message, "DUPLICATE", ExceptionType.BUSINESS)


class ValidationException(BaseException):
    """验证异常"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", ExceptionType.BUSINESS)


class DatabaseException(BaseException):
    """数据库操作异常"""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message, "DATABASE_ERROR", ExceptionType.SYSTEM)


class SystemException(BaseException):
    """系统异常"""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message, "SYSTEM_ERROR", ExceptionType.SYSTEM)
