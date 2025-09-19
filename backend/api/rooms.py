from typing import Dict, Set
import time
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt
from sqlalchemy import select

from config.settings import settings
from db.db import AsyncSessionLocal
from models.models import User
from protos import chat_pb2

router = APIRouter(prefix="/ws", tags=["ws"])


class RoomManager:
    def __init__(self) -> None:
        self.room_id_to_connections: Dict[int, Set[WebSocket]] = {}
        self.room_tasks: Dict[int, asyncio.Task] = {}

    async def connect(self, room_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.room_id_to_connections.setdefault(room_id, set()).add(websocket)
        
        # 如果是第一个连接，启动定时广播任务
        if len(self.room_id_to_connections[room_id]) == 1:
            self.room_tasks[room_id] = asyncio.create_task(self._broadcast_room_count_periodically(room_id))

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        connections = self.room_id_to_connections.get(room_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            if not connections:
                # 房间为空时，取消定时任务
                if room_id in self.room_tasks:
                    self.room_tasks[room_id].cancel()
                    del self.room_tasks[room_id]
                self.room_id_to_connections.pop(room_id, None)

    async def broadcast(self, room_id: int, data: bytes) -> None:
        connections = list(self.room_id_to_connections.get(room_id, set()))
        for ws in connections:
            try:
                await ws.send_bytes(data)
            except Exception:
                # 广播失败时主动断开连接
                try:
                    await ws.close()
                except Exception:
                    pass
                # 从连接列表中移除
                self.disconnect(room_id, ws)

    async def _broadcast_room_count_periodically(self, room_id: int) -> None:
        """每10秒广播一次房间人数"""
        while True:
            try:
                await asyncio.sleep(10)
                if room_id in self.room_id_to_connections:
                    connections = self.room_id_to_connections.get(room_id, set())
                    user_count = len(connections)
                    
                    count_msg = chat_pb2.ChatMessage(
                        user="System",
                        room_id=room_id,
                        content=f"当前房间人数: {user_count}",
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.ROOM_COUNT,
                    )
                    await self.broadcast(room_id, count_msg.SerializeToString())
            except asyncio.CancelledError:
                break
            except Exception:
                break


room_manager = RoomManager()


@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str | None = Query(default=None),
):
    username = "Anonymous"

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("sub"))
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    username = user.username
        except Exception:
            pass

    await room_manager.connect(room_id, websocket)

    try:
        # 系统提示：加入
        join_msg = chat_pb2.ChatMessage(
            user=username,
            room_id=room_id,
            content=f"{username} joined room {room_id}",
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await room_manager.broadcast(room_id, join_msg.SerializeToString())

        while True:
            data = await websocket.receive_bytes()
            
            # 客户端发来的应为 ChatMessage
            try:
                incoming = chat_pb2.ChatMessage()
                incoming.ParseFromString(data)
            except Exception:
                # 无法解析则忽略
                continue

            # 处理用户文本消息和音乐消息
            if incoming.type == chat_pb2.MessageType.USER_TEXT:
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=incoming.content,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.USER_TEXT,
                )
                await room_manager.broadcast(room_id, outgoing.SerializeToString())
            elif incoming.type == chat_pb2.MessageType.MUSIC:
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=incoming.content,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.MUSIC,
                )
                await room_manager.broadcast(room_id, outgoing.SerializeToString())

    except WebSocketDisconnect:
        pass
    finally:
        room_manager.disconnect(room_id, websocket)
        leave_msg = chat_pb2.ChatMessage(
            user=username,
            room_id=room_id,
            content=f"{username} left room {room_id}",
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await room_manager.broadcast(room_id, leave_msg.SerializeToString())
