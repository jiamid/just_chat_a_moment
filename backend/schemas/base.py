# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : base.py
@Date    : 2025/9/18 23:53
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 
"""
from fastapi.responses import JSONResponse
from typing import Any, Optional
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    code: int = Field(default=0, description='服务状态码，0成功')
    message: str = Field(default='success')
    data: Optional[Any] = Field(default=None, description='响应数据')

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            self.model_dump()
        )

    @classmethod
    def forbidden(cls, msg: str):
        return cls(code=403, message=msg).to_response()

    @classmethod
    def error(cls, msg: str):
        return cls(code=500, message=msg).to_response()