# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : register.py
@Date    : 2025/7/23 22:06
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 
"""
from fastapi import FastAPI,APIRouter
from api.auth import router as auth_router
from api.rooms import router as ws_router
from api.me import router as me_router

def register_router(app: FastAPI):
    base_router = APIRouter(prefix="/api")
    base_router.include_router(auth_router)
    base_router.include_router(me_router)


    app.include_router(base_router)
    app.include_router(ws_router)
