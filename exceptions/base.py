class BaseException(Exception):
    """
    异常基类
    """

    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundException(BaseException):
    """资源未找到异常"""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND")


class DuplicateException(BaseException):
    """重复资源异常"""

    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message, "DUPLICATE")


class ValidationException(BaseException):
    """验证异常"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class DatabaseException(BaseException):
    """数据库操作异常"""

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")
