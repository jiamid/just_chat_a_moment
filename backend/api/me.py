# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : me.py
@Date    : 2025/9/18 23:47
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 
"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from config.auth import get_current_user


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter( tags=["me"])


@router.get("/me")
async def read_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
    }