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
        # 画图功能：房间ID -> 当前画画人的用户名
        self.room_id_to_drawer: Dict[int, str] = {}
        # 画图功能：房间ID -> 当前画布内容（base64图片数据）
        self.room_id_to_canvas_data: Dict[int, str] = {}
        # 画图功能：房间ID -> 画画人开始时间（秒时间戳）
        self.room_id_to_drawer_start_time: Dict[int, float] = {}
        # 画图功能：房间ID -> 申请列表（Set[用户名]）
        self.room_id_to_requests: Dict[int, set] = {}
        # 画图功能：房间ID -> 自动退出任务
        self.room_id_to_auto_stop_tasks: Dict[int, asyncio.Task] = {}
        # WebSocket -> 用户名映射（用于断开连接时清理）
        self.websocket_to_username: Dict[WebSocket, str] = {}
        # 房间ID -> WebSocket -> 用户名映射
        self.room_id_to_websocket_to_username: Dict[int, Dict[WebSocket, str]] = {}

    async def connect(self, room_id: int, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self.room_id_to_connections.setdefault(room_id, set()).add(websocket)
        self.websocket_to_username[websocket] = username
        self.room_id_to_websocket_to_username.setdefault(room_id, {})[websocket] = username
        
        # 如果是第一个连接，启动定时广播任务
        if len(self.room_id_to_connections[room_id]) == 1:
            self.room_tasks[room_id] = asyncio.create_task(self._broadcast_room_count_periodically(room_id))

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        connections = self.room_id_to_connections.get(room_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            
            # 清理用户名映射
            username = self.websocket_to_username.pop(websocket, None)
            if room_id in self.room_id_to_websocket_to_username:
                self.room_id_to_websocket_to_username[room_id].pop(websocket, None)
            
            # 如果断开连接的是当前画画人，清除画画人状态和画布内容
            if room_id in self.room_id_to_drawer and self.room_id_to_drawer[room_id] == username:
                self.room_id_to_drawer.pop(room_id, None)
                self.room_id_to_canvas_data.pop(room_id, None)
                self.room_id_to_drawer_start_time.pop(room_id, None)
                # 取消自动退出任务
                if room_id in self.room_id_to_auto_stop_tasks:
                    self.room_id_to_auto_stop_tasks[room_id].cancel()
                    del self.room_id_to_auto_stop_tasks[room_id]
            
            # 清理申请列表中的该用户
            if room_id in self.room_id_to_requests:
                self.room_id_to_requests[room_id].discard(username)
            
            if not connections:
                # 房间为空时，取消定时任务并清理所有状态
                if room_id in self.room_tasks:
                    self.room_tasks[room_id].cancel()
                    del self.room_tasks[room_id]
                self.room_id_to_connections.pop(room_id, None)
                self.room_id_to_drawer.pop(room_id, None)
                self.room_id_to_canvas_data.pop(room_id, None)
                self.room_id_to_drawer_start_time.pop(room_id, None)
                self.room_id_to_requests.pop(room_id, None)
                self.room_id_to_websocket_to_username.pop(room_id, None)
                # 取消自动退出任务
                if room_id in self.room_id_to_auto_stop_tasks:
                    self.room_id_to_auto_stop_tasks[room_id].cancel()
                    del self.room_id_to_auto_stop_tasks[room_id]

    async def _send_to_connection(self, room_id: int, websocket: WebSocket, data: bytes) -> None:
        """向单个连接发送数据，处理错误"""
        try:
            await websocket.send_bytes(data)
        except Exception:
            # 广播失败时主动断开连接
            try:
                await websocket.close()
            except Exception:
                pass
            # 从连接列表中移除
            self.disconnect(room_id, websocket)

    async def broadcast(self, room_id: int, data: bytes) -> None:
        connections = list(self.room_id_to_connections.get(room_id, set()))
        if not connections:
            return
        
        # 使用 asyncio.gather() 并发发送给所有连接
        tasks = [self._send_to_connection(room_id, ws, data) for ws in connections]
        await asyncio.gather(*tasks, return_exceptions=True)

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

    async def _auto_stop_drawing(self, room_id: int) -> None:
        """10分钟后自动退出画画"""
        try:
            await asyncio.sleep(600)  # 10分钟 = 600秒
            # 检查是否仍然是同一个画画人
            if room_id in self.room_id_to_drawer:
                # 清除画画人状态和画布内容
                self.room_id_to_drawer.pop(room_id, None)
                self.room_id_to_canvas_data.pop(room_id, None)
                self.room_id_to_drawer_start_time.pop(room_id, None)
                # 广播退出画画消息
                drawer_state_msg = chat_pb2.ChatMessage(
                    user="System",
                    room_id=room_id,
                    content="",  # 空内容表示没有画画人
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING_STATE,
                )
                await self.broadcast(room_id, drawer_state_msg.SerializeToString())
        except asyncio.CancelledError:
            pass
        finally:
            # 清理任务
            if room_id in self.room_id_to_auto_stop_tasks:
                del self.room_id_to_auto_stop_tasks[room_id]

    async def _set_drawer(self, room_id: int, username: str) -> None:
        """设置画画人并启动10分钟倒计时"""
        # 取消之前的自动退出任务
        if room_id in self.room_id_to_auto_stop_tasks:
            self.room_id_to_auto_stop_tasks[room_id].cancel()
        
        # 设置画画人
        self.room_id_to_drawer[room_id] = username
        self.room_id_to_drawer_start_time[room_id] = time.time()
        
        # 启动10分钟自动退出任务
        self.room_id_to_auto_stop_tasks[room_id] = asyncio.create_task(self._auto_stop_drawing(room_id))
        
        # 广播画画人状态变更
        drawer_state_msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=username,
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.DRAWING_STATE,
        )
        await self.broadcast(room_id, drawer_state_msg.SerializeToString())


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

    await room_manager.connect(room_id, websocket, username)

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
        
        # 发送当前画画人状态和画布内容给新加入的用户
        current_drawer = room_manager.room_id_to_drawer.get(room_id)
        if current_drawer:
            # 发送画画人状态
            drawer_state_msg = chat_pb2.ChatMessage(
                user="System",
                room_id=room_id,
                content=current_drawer,
                timestamp=int(time.time() * 1000),
                type=chat_pb2.MessageType.DRAWING_STATE,
            )
            await room_manager._send_to_connection(room_id, websocket, drawer_state_msg.SerializeToString())
            
            # 如果有画布内容，发送给新用户
            canvas_data = room_manager.room_id_to_canvas_data.get(room_id)
            if canvas_data:
                canvas_msg = chat_pb2.ChatMessage(
                    user=current_drawer,
                    room_id=room_id,
                    content=canvas_data,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING,
                )
                await room_manager._send_to_connection(room_id, websocket, canvas_msg.SerializeToString())

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
                # 设置音乐消息的延迟播放时间戳（0.5秒后）
                delayed_timestamp = int((time.time() + 0.5) * 1000)
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=incoming.content,
                    timestamp=delayed_timestamp,
                    type=chat_pb2.MessageType.MUSIC,
                )
                await room_manager.broadcast(room_id, outgoing.SerializeToString())
            elif incoming.type == chat_pb2.MessageType.DRAWING_REQUEST:
                # 申请成为画画人
                current_drawer = room_manager.room_id_to_drawer.get(room_id)
                if not current_drawer:
                    # 如果没有画画人，直接允许申请
                    await room_manager._set_drawer(room_id, username)
                elif current_drawer == username:
                    # 如果申请者就是当前画画人，忽略
                    pass
                else:
                    # 如果有当前画画人，将申请添加到申请列表
                    if room_id not in room_manager.room_id_to_requests:
                        room_manager.room_id_to_requests[room_id] = set()
                    room_manager.room_id_to_requests[room_id].add(username)
                    # 通知当前画画人有新的申请（通过广播申请消息）
                    request_msg = chat_pb2.ChatMessage(
                        user=username,
                        room_id=room_id,
                        content=username,  # content包含申请者用户名
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.DRAWING_REQUEST,
                    )
                    await room_manager.broadcast(room_id, request_msg.SerializeToString())
            elif incoming.type == chat_pb2.MessageType.DRAWING_REQUEST_APPROVE:
                # 同意画画申请：只有当前画画人可以同意
                current_drawer = room_manager.room_id_to_drawer.get(room_id)
                if current_drawer == username:
                    # incoming.content 包含被同意的用户名
                    approved_user = incoming.content
                    # 检查用户是否还在房间
                    if room_id in room_manager.room_id_to_websocket_to_username:
                        users_in_room = set(room_manager.room_id_to_websocket_to_username[room_id].values())
                        if approved_user in users_in_room:
                            # 检查是否在申请列表中
                            if room_id in room_manager.room_id_to_requests and approved_user in room_manager.room_id_to_requests[room_id]:
                                # 从申请列表中移除
                                room_manager.room_id_to_requests[room_id].discard(approved_user)
                                # 设置新的画画人
                                await room_manager._set_drawer(room_id, approved_user)
            elif incoming.type == chat_pb2.MessageType.DRAWING:
                # 画图数据：只有当前画画人可以发送
                current_drawer = room_manager.room_id_to_drawer.get(room_id)
                if current_drawer == username:
                    # 保存画布内容
                    room_manager.room_id_to_canvas_data[room_id] = incoming.content
                    # 广播画图数据给所有用户（包括发送者自己，用于同步）
                    outgoing = chat_pb2.ChatMessage(
                        user=username,
                        room_id=room_id,
                        content=incoming.content,
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.DRAWING,
                    )
                    await room_manager.broadcast(room_id, outgoing.SerializeToString())
            elif incoming.type == chat_pb2.MessageType.DRAWING_CLEAR:
                # 清空画布：只有当前画画人可以清空
                current_drawer = room_manager.room_id_to_drawer.get(room_id)
                if current_drawer == username:
                    # 清除保存的画布内容
                    room_manager.room_id_to_canvas_data.pop(room_id, None)
                    # 广播清空画布消息
                    outgoing = chat_pb2.ChatMessage(
                        user=username,
                        room_id=room_id,
                        content="",
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.DRAWING_CLEAR,
                    )
                    await room_manager.broadcast(room_id, outgoing.SerializeToString())
            elif incoming.type == chat_pb2.MessageType.DRAWING_STOP:
                # 退出画画：只有当前画画人可以退出
                current_drawer = room_manager.room_id_to_drawer.get(room_id)
                if current_drawer == username:
                    # 取消自动退出任务
                    if room_id in room_manager.room_id_to_auto_stop_tasks:
                        room_manager.room_id_to_auto_stop_tasks[room_id].cancel()
                        del room_manager.room_id_to_auto_stop_tasks[room_id]
                    # 清除画画人状态和画布内容
                    room_manager.room_id_to_drawer.pop(room_id, None)
                    room_manager.room_id_to_canvas_data.pop(room_id, None)
                    room_manager.room_id_to_drawer_start_time.pop(room_id, None)
                    # 广播退出画画消息（清空画画人状态）
                    drawer_state_msg = chat_pb2.ChatMessage(
                        user="System",
                        room_id=room_id,
                        content="",  # 空内容表示没有画画人
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.DRAWING_STATE,
                    )
                    await room_manager.broadcast(room_id, drawer_state_msg.SerializeToString())

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
