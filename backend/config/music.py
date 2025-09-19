# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : music.py
@Date    : 2025/9/20 00:46
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 
"""
from pydantic import BaseModel, Field


class Music(BaseModel):
    id: str = Field(default='')
    name: str = Field(default="")
    url: str = Field(default="")


MUSIC_MAP = {
    'echo': Music(
        id='echo',
        name='Echo',
        url='https://cdn.jiamid.com/music/echo.mp3',
    ),
    'fade': Music(
        id='fade',
        name='Fade',
        url='https://cdn.jiamid.com/music/fade.mp3',
    ),
    'wjdbnsqn': Music(
        id='wjdbnsqn',
        name='我绝对不能失去你',
        url='https://cdn.jiamid.com/music/wojueduibunengshiqvni.mp3',
    ),
    'wtj': Music(
        id='wtj',
        name='无条件',
        url='https://cdn.jiamid.com/music/wutiaojian.mp3',
    ),
    'yimeng': Music(
        id='yimeng',
        name='异梦',
        url='https://cdn.jiamid.com/music/yimeng.mp3',
    )
}
