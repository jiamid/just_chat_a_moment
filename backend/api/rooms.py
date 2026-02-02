from typing import Optional
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt
from sqlalchemy import select

from config.settings import settings
from db.db import AsyncSessionLocal
from models.models import User
from protos import chat_pb2, game_pb2
from rooms import (
    RoomType,
    chat_room_manager,
    drawing_room_manager,
    live_war_room_manager,
    gobang_room_manager,
)

router = APIRouter(prefix="/room/ws", tags=["ws"])


@router.websocket("/{room_type}/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_type: str,
    room_id: int,
    token: str | None = Query(default=None),
):
    """WebSocket端点 - 根据房间类型路由到不同的处理器"""
    # 验证房间类型
    try:
        room_type_enum = RoomType(room_type)
    except ValueError:
        await websocket.close(code=1008, reason=f"Invalid room type: {room_type}")
        return

    username = "Anonymous"
    user_id: Optional[int] = None

    # 验证token并获取用户信息
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            raw_user_id = payload.get("sub")
            if raw_user_id is not None:
                user_id = int(raw_user_id)
            async with AsyncSessionLocal() as db:
                if user_id is not None:
                    result = await db.execute(select(User).where(User.id == user_id))
                else:
                    result = None
                user = result.scalar_one_or_none()
                if user:
                    username = user.username
        except Exception:
            pass

    # 根据房间类型选择管理器
    if room_type_enum == RoomType.CHAT:
        manager = chat_room_manager
    elif room_type_enum == RoomType.DRAWING:
        manager = drawing_room_manager
    elif room_type_enum == RoomType.LIVE_WAR:
        manager = live_war_room_manager
    elif room_type_enum == RoomType.GOBANG:
        manager = gobang_room_manager
    else:
        await websocket.close(code=1008, reason=f"Unsupported room type: {room_type}")
        return

    # 连接到房间
    await manager.connect(room_id, websocket, username, user_id)

    try:
        # 系统提示：加入
        join_msg = chat_pb2.ChatMessage(
            user=username,
            room_id=room_id,
            content=f"{username} joined room {room_id}",
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=join_msg).SerializeToString())
        
        # 发送初始状态（如果有）
        if hasattr(manager, 'send_initial_state'):
            await manager.send_initial_state(room_id, websocket)

        while True:
            data = await websocket.receive_bytes()

            # 顶层封包：WsEnvelope
            try:
                envelope = chat_pb2.WsEnvelope()
                envelope.ParseFromString(data)
            except Exception:
                # 无法解析则忽略
                continue

            # 处理游戏消息（仅 LiveWar 游戏房间）
            if envelope.HasField("game"):
                if room_type_enum == RoomType.LIVE_WAR:
                    await manager.handle_game_message(room_id, websocket, envelope.game)
                else:
                    # 非游戏房间不允许游戏消息
                    err = game_pb2.GameMessage(
                        type=game_pb2.GameMessage.ERROR,
                        error=game_pb2.ErrorPayload(message="当前房间类型不支持游戏功能"),
                    )
                    await websocket.send_bytes(
                        chat_pb2.WsEnvelope(game=err).SerializeToString()
                    )
                continue

            # 处理聊天消息
            if envelope.HasField("chat"):
                await manager.handle_message(room_id, websocket, envelope.chat)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, websocket)
        leave_msg = chat_pb2.ChatMessage(
            user=username,
            room_id=room_id,
            content=f"{username} left room {room_id}",
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=leave_msg).SerializeToString())
