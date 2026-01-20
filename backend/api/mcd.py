#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : mcd.py
@Date    : 2026/1/20
@Author  : JIAMID + AI
@Desc    : 麦当劳 MCP / 优惠券 AI 助手接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from db.db import get_db
from config.auth import get_current_user
from models.models import UserSettings
from schemas.schemas import (
    McdChatRequest,
    McdChatResponse,
    McdChatAnswer,
    McdTokenUpdateRequest,
    McdTokenResponse,
    McdTokenInfo,
)

# LangChain / MCP 相关依赖
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from config.settings import settings

router = APIRouter(prefix="/mcd", tags=["mcd"])


@router.get("/token", response_model=McdTokenResponse)
async def get_mcd_token(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    查询当前登录用户已配置的 MCP Token。
    """
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    token = settings.mcd_mcp_token if settings else None
    return McdTokenResponse(data=McdTokenInfo(token=token))


@router.post("/token", response_model=McdTokenResponse)
async def set_mcd_token(
    body: McdTokenUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    为当前登录用户设置 / 更新 MCP Token。
    """
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="MCP Token 不能为空")

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if user_settings is None:
        user_settings = UserSettings(user_id=current_user.id, mcd_mcp_token=token)
        db.add(user_settings)
    else:
        user_settings.mcd_mcp_token = token

    await db.commit()
    await db.refresh(user_settings)

    return McdTokenResponse(data=McdTokenInfo(token=settings.mcd_mcp_token))


@router.post("/chat", response_model=McdChatResponse)
async def mcd_chat(
    body: McdChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    使用 LangChain + 麦当劳 MCP Server 与 AI 助手对话。

    聊天前要求当前登录用户已经在服务端配置过 MCP Token。
    """
    user_query = body.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # 读取当前用户的 MCP Token
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()
    if user_settings is None or not user_settings.mcd_mcp_token:
        raise HTTPException(
            status_code=400,
            detail="请先在 MCP Token 设置中填写并保存 Token，才能开始聊天",
        )

    mcp_token = user_settings.mcd_mcp_token

    logger.info(f"[MCD] user_id={current_user.id} query={user_query}")

    # 初始化 LLM（这里默认使用 OpenAI，可根据 config.settings 调整）
    llm = ChatOpenAI(model="gemini-2.5-flash", base_url=settings.gemini.base_url,api_key=settings.gemini.api_key, temperature=0)

    # MCP Server 配置
    # langchain-mcp-adapters 需要的是 "transport" 字段，而不是官方 JSON 里的 "type"
    # 这里使用 HTTP 传输，并在 headers 中携带用户的 MCP Token
    mcp_config = {
        "mcd-mcp": {
            "transport": "http",
            "url": "https://mcp.mcd.cn/mcp-servers/mcd-mcp",
            "headers": {
                "Authorization": f"Bearer {mcp_token}",
            },
        }
    }

    try:
        # MultiServerMCPClient 当前版本不能作为 async context manager 使用
        # 参考报错信息建议的用法：直接实例化后调用 get_tools()
        client = MultiServerMCPClient(mcp_config)
        tools = await client.get_tools()
        agent = create_react_agent(llm, tools)

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_query,
                    }
                ]
            }
        )

        # LangGraph create_react_agent 默认把对话历史放在 messages 中
        messages = result.get("messages") or []
        if not messages:
            answer = "麦麦助手暂时没有回复，请稍后重试。"
        else:
            last_msg = messages[-1]
            # 兼容字符串 / ChatMessage 等不同结构
            content = getattr(last_msg, "content", None) or ""
            if isinstance(content, list):
                # 如果是多段内容，拼接为文本
                answer = "\n".join([str(c) for c in content])
            else:
                answer = str(content)

        return McdChatResponse(data=McdChatAnswer(answer=answer))
    except Exception as e:
        logger.exception(f"[MCD] 调用 MCP / LangChain 失败: {e}")
        raise HTTPException(status_code=500, detail="麦当劳 MCP 服务暂时不可用，请稍后重试")

