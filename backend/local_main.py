#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: Jiamid
@Contact: JiamidTan@poweronlabs.ai
@file: local_main.py
@time: 2025/9/15 20:03
"""
from main import app

if __name__ == '__main__':
    from uvicorn import run
    run('main:app', host='127.0.0.1', port=8000,reload=True)