from fastapi.responses import JSONResponse
from typing import Any, Optional, List


def api_response(code: int, msg: str, data: Any = None) -> JSONResponse:
    """
    统一API响应格式
    Args:
        code: HTTP状态码 (200成功, 400参数错误, 404未找到, 500服务器错误)
        msg: 响应消息
        data: 响应数据
    """
    return JSONResponse(
        status_code=code, content={"code": code, "msg": msg, "data": data}
    )


def success(data: Any = None, msg: str = "操作成功") -> JSONResponse:
    """查询/更新成功 - 200"""
    return api_response(200, msg, data)


def bad_request(msg: str = "参数错误") -> JSONResponse:
    """参数错误 - 400"""
    return api_response(400, msg, None)


def not_found(msg: str = "资源不存在") -> JSONResponse:
    """资源不存在 - 404"""
    return api_response(404, msg, None)


def server_error(msg: str = "服务器错误") -> JSONResponse:
    """服务器错误 - 500"""
    return api_response(500, msg, None)


def paginated(items: List[Any], total: int, page: int, size: int) -> JSONResponse:
    """分页响应"""
    pages = (total + size - 1) // size
    data = {"items": items, "total": total, "page": page, "size": size, "pages": pages}
    return success(data, "查询成功")
