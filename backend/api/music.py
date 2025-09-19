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
from config.music import MUSIC_MAP
from schemas.base import BaseResponse
from loguru import logger

router = APIRouter(prefix='/music', tags=["music"])


@router.get("/config/{room_id}", response_model=BaseResponse)
async def get_music_config(room_id:int):
    logger.info(f"get_music_config: {room_id}")
    return BaseResponse.success(MUSIC_MAP)