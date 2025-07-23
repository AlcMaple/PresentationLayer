from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException
import logging
import traceback

from exceptions import (
    NotFoundException,
    DuplicateException,
    ValidationException,
    BaseException,
)
from utils.responses import api_response  # Your custom response utility

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException):
        logger.info(f"Resource not found: {exc.message} for request: {request.url}")
        return api_response(404, exc.message)

    @app.exception_handler(DuplicateException)
    async def duplicate_exception_handler(request: Request, exc: DuplicateException):
        logger.warning(f"Duplicate resource: {exc.message} for request: {request.url}")
        return api_response(400, exc.message)

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        logger.warning(f"Validation failed: {exc.message} for request: {request.url}")
        return api_response(400, exc.message)

    @app.exception_handler(BaseException)
    async def base_exception_handler(request: Request, exc: BaseException):
        logger.warning(
            f"Base business exception: {exc.message} for request: {request.url}"
        )
        return api_response(400, exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return api_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        error_messages = [
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors()
        ]
        logger.warning(f"Pydantic validation failed: {'; '.join(error_messages)}")
        return api_response(400, f"参数验证失败: {'; '.join(error_messages)}")

    @app.exception_handler(IntegrityError)
    async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError):
        error_msg = str(exc.orig).lower() if hasattr(exc, "orig") else str(exc).lower()

        if "unique constraint" in error_msg or "duplicate entry" in error_msg:
            message = "数据重复，请检查唯一性约束"
        elif "foreign key constraint" in error_msg:
            message = "外键约束错误，一个或多个指定的关联资源不存在"
        else:
            message = "数据库完整性错误"

        logger.error(f"Database Integrity Error: {message} | Details: {exc.orig}")
        return api_response(400, message)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled internal server error: {type(exc).__name__}: {exc}")
        logger.error(f"Request URL: {request.url}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return api_response(500, "服务器内部错误")
