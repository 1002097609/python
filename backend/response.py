"""
统一响应格式模块（response.py）

所有 API 接口统一使用以下响应格式：
  成功: {"code": 200, "message": "ok", "data": ...}
  失败: {"code": <http_status>, "message": "<error_detail>", "data": null}
"""

from typing import Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "ok", code: int = 200) -> dict:
    """构建成功响应"""
    return {"code": code, "message": message, "data": data}


def created(data: Any = None, message: str = "创建成功") -> dict:
    """构建创建成功响应"""
    return {"code": 201, "message": message, "data": data}


def no_content(message: str = "删除成功") -> JSONResponse:
    """构建无内容响应（用于 DELETE）"""
    return JSONResponse(status_code=204, content={"code": 204, "message": message, "data": None})


def error(message: str, code: int = 400) -> dict:
    """构建错误响应"""
    return {"code": code, "message": message, "data": None}


class BusinessException(HTTPException):
    """
    业务异常类，用于在路由处理中抛出带有自定义状态码和错误信息的异常。

    用法：
        raise BusinessException(status_code=400, detail="骨架不存在")
    """

    def __init__(self, status_code: int = 400, detail: str = "业务异常"):
        super().__init__(status_code=status_code, detail=detail)
