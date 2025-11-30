from typing import Dict, Set, Optional
import time
import asyncio
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt
from sqlalchemy import select

from config.settings import settings
from db.db import AsyncSessionLocal
from models.models import User
from protos import chat_pb2, game_pb2
from service import game_manager as live_war_game_manager

router = APIRouter(prefix="/room/ws", tags=["ws"])


class RoomMode(str, Enum):
    NONE = "none"
    DRAWING = "drawing"
    GAME = "game"


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
        # WebSocket -> 用户ID映射（用于游戏身份）
        self.websocket_to_user_id: Dict[WebSocket, Optional[int]] = {}
        # 房间ID -> WebSocket -> 用户名映射
        self.room_id_to_websocket_to_username: Dict[int, Dict[WebSocket, str]] = {}
        # 房间模式：none / drawing / game
        self.room_id_to_mode: Dict[int, RoomMode] = {}
        # 游戏房间销毁倒计时任务：房间ID -> 倒计时任务
        self.room_id_to_game_destroy_tasks: Dict[int, asyncio.Task] = {}

    async def connect(self, room_id: int, websocket: WebSocket, username: str, user_id: Optional[int]) -> None:
        await websocket.accept()
        self.room_id_to_connections.setdefault(room_id, set()).add(websocket)
        self.websocket_to_username[websocket] = username
        self.websocket_to_user_id[websocket] = user_id
        self.room_id_to_websocket_to_username.setdefault(room_id, {})[websocket] = username
        
        # 如果是游戏模式，取消销毁倒计时（有人重新连接）
        if room_id in self.room_id_to_mode and self.room_id_to_mode[room_id] == RoomMode.GAME:
            if room_id in self.room_id_to_game_destroy_tasks:
                self.room_id_to_game_destroy_tasks[room_id].cancel()
                del self.room_id_to_game_destroy_tasks[room_id]
                print(f"[RoomManager] Cancelled game destroy countdown for room {room_id} (user reconnected)", flush=True)
        
        # 如果是第一个连接，启动定时广播任务
        if len(self.room_id_to_connections[room_id]) == 1:
            self.room_tasks[room_id] = asyncio.create_task(self._broadcast_room_count_periodically(room_id))

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        connections = self.room_id_to_connections.get(room_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            
            # 清理用户名映射
            username = self.websocket_to_username.pop(websocket, None)
            self.websocket_to_user_id.pop(websocket, None)
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
                # 房间为空时
                # 如果是游戏模式，启动60秒销毁倒计时
                if room_id in self.room_id_to_mode and self.room_id_to_mode[room_id] == RoomMode.GAME:
                    # 取消之前的倒计时（如果存在）
                    if room_id in self.room_id_to_game_destroy_tasks:
                        self.room_id_to_game_destroy_tasks[room_id].cancel()
                    
                    # 启动60秒倒计时
                    async def destroy_game_after_delay():
                        try:
                            await asyncio.sleep(60)  # 等待60秒
                            # 检查是否仍然没有连接
                            if room_id in self.room_id_to_connections:
                                current_connections = self.room_id_to_connections.get(room_id, set())
                                if not current_connections:
                                    # 60秒后仍然没有连接，销毁游戏状态
                                    print(f"[RoomManager] Destroying game state for room {room_id} (no connections for 60s)", flush=True)
                                    gm = live_war_game_manager.game_manager
                                    # 停止游戏循环
                                    gm._stop_game_loop(room_id)
                                    # 删除游戏状态
                                    if room_id in gm.room_states:
                                        del gm.room_states[room_id]
                                    # 删除广播回调
                                    if room_id in gm.broadcast_callbacks:
                                        del gm.broadcast_callbacks[room_id]
                                    # 重置房间模式
                                    self.room_id_to_mode[room_id] = RoomMode.NONE
                                    # 清理倒计时任务记录
                                    if room_id in self.room_id_to_game_destroy_tasks:
                                        del self.room_id_to_game_destroy_tasks[room_id]
                        except asyncio.CancelledError:
                            # 倒计时被取消（有人重新连接）
                            pass
                    
                    self.room_id_to_game_destroy_tasks[room_id] = asyncio.create_task(destroy_game_after_delay())
                    print(f"[RoomManager] Started 60s destroy countdown for room {room_id} game", flush=True)
                else:
                    # 非游戏模式，立即清理
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
        
        # 创建后台任务，完全异步执行，不等待
        asyncio.create_task(self._broadcast_async(room_id, connections, data))
    
    async def _broadcast_async(self, room_id: int, connections: list, data: bytes) -> None:
        """异步广播的内部方法"""
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
                    envelope = chat_pb2.WsEnvelope(chat=count_msg)
                    await self.broadcast(room_id, envelope.SerializeToString())
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
        # 房间模式切换为 DRAWING（如果之前是 NONE 才切，避免覆盖 GAME）
        if self.room_id_to_mode.get(room_id, RoomMode.NONE) == RoomMode.NONE:
            self.room_id_to_mode[room_id] = RoomMode.DRAWING
        
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
        envelope = chat_pb2.WsEnvelope(chat=drawer_state_msg)
        await self.broadcast(room_id, envelope.SerializeToString())


room_manager = RoomManager()


@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str | None = Query(default=None),
):
    username = "Anonymous"
    user_id: Optional[int] = None

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

    await room_manager.connect(room_id, websocket, username, user_id)

    try:
        # 系统提示：加入
        join_msg = chat_pb2.ChatMessage(
            user=username,
            room_id=room_id,
            content=f"{username} joined room {room_id}",
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=join_msg).SerializeToString())
        
        # 检查房间模式，发送相应的状态信息
        mode = room_manager.room_id_to_mode.get(room_id, RoomMode.NONE)
        
        if mode == RoomMode.DRAWING:
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
                await room_manager._send_to_connection(
                    room_id,
                    websocket,
                    chat_pb2.WsEnvelope(chat=drawer_state_msg).SerializeToString(),
                )
                
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
                    await room_manager._send_to_connection(
                        room_id,
                        websocket,
                        chat_pb2.WsEnvelope(chat=canvas_msg).SerializeToString(),
                    )
        elif mode == RoomMode.GAME:
            # 发送当前游戏状态给新加入的用户
            gm = live_war_game_manager.game_manager
            uid = room_manager.websocket_to_user_id.get(websocket)
            state = gm.build_state_for_user(room_id, uid)
            if state:
                game_state_msg = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.GAME_STATE,
                    game_state=state,
                )
                await room_manager._send_to_connection(
                    room_id,
                    websocket,
                    chat_pb2.WsEnvelope(game=game_state_msg).SerializeToString(),
                )
                print(f"[WebSocket] Sent initial game state to user {uid} in room {room_id}", flush=True)
            else:
                print(f"[WebSocket] No game state available for room {room_id}, user {uid}", flush=True)

        while True:
            data = await websocket.receive_bytes()

            # 顶层封包：WsEnvelope
            try:
                envelope = chat_pb2.WsEnvelope()
                envelope.ParseFromString(data)
            except Exception:
                # 无法解析则忽略
                continue

            # 先解析游戏消息（livewar）
            if envelope.HasField("game"):
                # 房间处于 DRAWING 模式时不允许启动游戏
                mode = room_manager.room_id_to_mode.get(room_id, RoomMode.NONE)
                if mode == RoomMode.DRAWING:
                    err = game_pb2.GameMessage(
                        type=game_pb2.GameMessage.ERROR,
                        error=game_pb2.ErrorPayload(message="当前房间正在画画，不能开始游戏"),
                    )
                    await websocket.send_bytes(
                        chat_pb2.WsEnvelope(game=err).SerializeToString()
                    )
                    continue

                # 设置房间模式为 GAME
                room_manager.room_id_to_mode[room_id] = RoomMode.GAME

                # 分发给简化版 LiveWar 管理器
                gm = live_war_game_manager.game_manager
                uid = room_manager.websocket_to_user_id.get(websocket)

                # 设置广播回调（如果还没有设置）
                if room_id not in gm.broadcast_callbacks:
                    async def broadcast_callback(msg: game_pb2.GameMessage):
                        """游戏循环的广播回调"""
                        connections = list(room_manager.room_id_to_connections.get(room_id, set()))
                        for ws in connections:
                            uid_ws = room_manager.websocket_to_user_id.get(ws)
                            if msg.type == game_pb2.GameMessage.GAME_STATE:
                                # 使用裁剪后的状态
                                state = gm.build_state_for_user(room_id, uid_ws)
                                if state is None:
                                    continue
                                msg_to_send = game_pb2.GameMessage(
                                    type=game_pb2.GameMessage.GAME_STATE,
                                    game_state=state,
                                )
                            else:
                                msg_to_send = msg
                            try:
                                await ws.send_bytes(
                                    chat_pb2.WsEnvelope(game=msg_to_send).SerializeToString()
                                )
                            except Exception:
                                pass  # 连接已断开，忽略

                    gm.set_broadcast_callback(room_id, broadcast_callback)

                outgoing_msgs = gm.handle_envelope_from_client(
                    room_id=room_id,
                    user_id=uid,
                    username=username,
                    msg=envelope.game,
                )

                # 按玩家/观战者裁剪状态并广播
                connections = list(room_manager.room_id_to_connections.get(room_id, set()))
                for ws in connections:
                    uid_ws = room_manager.websocket_to_user_id.get(ws)
                    for gm_msg in outgoing_msgs:
                        # ERROR 消息只发送给触发错误的玩家（uid），不广播给其他人
                        if gm_msg.type == game_pb2.GameMessage.ERROR:
                            if uid_ws != uid:
                                continue  # 跳过，不发送给其他玩家
                        
                        if gm_msg.type == game_pb2.GameMessage.GAME_STATE:
                            # 使用裁剪后的状态替换
                            state = gm.build_state_for_user(room_id, uid_ws)
                            if state is None:
                                continue
                            gm_msg_to_send = game_pb2.GameMessage(
                                type=game_pb2.GameMessage.GAME_STATE,
                                game_state=state,
                            )
                        else:
                            gm_msg_to_send = gm_msg

                        await ws.send_bytes(
                            chat_pb2.WsEnvelope(game=gm_msg_to_send).SerializeToString()
                        )

                # 如果游戏房间已无玩家，自动回到 NONE 模式
                if not gm.has_active_players(room_id):
                    room_manager.room_id_to_mode[room_id] = RoomMode.NONE

                continue

            # 目前仅处理聊天/画图消息
            if not envelope.HasField("chat"):
                continue

            incoming = envelope.chat

            # 处理用户文本消息和音乐消息
            if incoming.type == chat_pb2.MessageType.USER_TEXT:
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=incoming.content,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.USER_TEXT,
                )
                await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
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
                await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
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
                    await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=request_msg).SerializeToString())
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
                    await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
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
                    await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
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
                    # 如果没有画画人且没有画布，恢复房间模式为 NONE（避免与游戏冲突）
                    if room_manager.room_id_to_mode.get(room_id) == RoomMode.DRAWING:
                        room_manager.room_id_to_mode[room_id] = RoomMode.NONE
                    # 广播退出画画消息（清空画画人状态）
                    drawer_state_msg = chat_pb2.ChatMessage(
                        user="System",
                        room_id=room_id,
                        content="",  # 空内容表示没有画画人
                        timestamp=int(time.time() * 1000),
                        type=chat_pb2.MessageType.DRAWING_STATE,
                    )
                    await room_manager.broadcast(
                        room_id, chat_pb2.WsEnvelope(chat=drawer_state_msg).SerializeToString()
                    )

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
        await room_manager.broadcast(room_id, chat_pb2.WsEnvelope(chat=leave_msg).SerializeToString())
