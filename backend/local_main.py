#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: Jiamid
@Contact: JiamidTan@poweronlabs.ai
@file: local_main.py
@time: 2025/9/15 20:03
"""
from app.main import app

if __name__ == '__main__':
    from uvicorn import run
    run(app, host='0.0.0.0', port=8000)