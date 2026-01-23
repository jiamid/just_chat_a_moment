"""你画我猜房间服务 - 支持聊天、音乐和画图功能"""
from typing import Dict, Set, Optional
import time
import asyncio

from fastapi import WebSocket
from protos import chat_pb2
from .chat_room import ChatRoomManager


class DrawingRoomManager(ChatRoomManager):
    """你画我猜房间管理器 - 继承聊天房间功能，增加画图功能"""
    
    def __init__(self) -> None:
        super().__init__()
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

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        """断开连接 - 重写以处理画图相关清理"""
        username = self.websocket_to_username.get(websocket)
        
        super().disconnect(room_id, websocket)
        
        # 如果断开连接的是当前画画人，清除画画人状态和画布内容
        if username and room_id in self.room_id_to_drawer and self.room_id_to_drawer[room_id] == username:
            self.room_id_to_drawer.pop(room_id, None)
            self.room_id_to_canvas_data.pop(room_id, None)
            self.room_id_to_drawer_start_time.pop(room_id, None)
            # 取消自动退出任务
            if room_id in self.room_id_to_auto_stop_tasks:
                self.room_id_to_auto_stop_tasks[room_id].cancel()
                del self.room_id_to_auto_stop_tasks[room_id]
        
        # 清理申请列表中的该用户
        if username and room_id in self.room_id_to_requests:
            self.room_id_to_requests[room_id].discard(username)
        
        # 如果房间为空，清理画图相关状态
        if room_id not in self.room_id_to_connections:
            self.room_id_to_drawer.pop(room_id, None)
            self.room_id_to_canvas_data.pop(room_id, None)
            self.room_id_to_drawer_start_time.pop(room_id, None)
            self.room_id_to_requests.pop(room_id, None)
            if room_id in self.room_id_to_auto_stop_tasks:
                self.room_id_to_auto_stop_tasks[room_id].cancel()
                del self.room_id_to_auto_stop_tasks[room_id]

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
        envelope = chat_pb2.WsEnvelope(chat=drawer_state_msg)
        await self.broadcast(room_id, envelope.SerializeToString())

    async def handle_message(self, room_id: int, websocket: WebSocket, message: chat_pb2.ChatMessage) -> None:
        """处理消息 - 重写以支持画图功能"""
        username = self.websocket_to_username.get(websocket, "Anonymous")
        
        # 先处理聊天和音乐消息（继承父类功能）
        if message.type in (chat_pb2.MessageType.USER_TEXT, chat_pb2.MessageType.MUSIC):
            await super().handle_message(room_id, websocket, message)
        elif message.type == chat_pb2.MessageType.DRAWING_REQUEST:
            # 申请成为画画人
            current_drawer = self.room_id_to_drawer.get(room_id)
            if not current_drawer:
                # 如果没有画画人，直接允许申请
                await self._set_drawer(room_id, username)
            elif current_drawer == username:
                # 如果申请者就是当前画画人，忽略
                pass
            else:
                # 如果有当前画画人，将申请添加到申请列表
                if room_id not in self.room_id_to_requests:
                    self.room_id_to_requests[room_id] = set()
                self.room_id_to_requests[room_id].add(username)
                # 通知当前画画人有新的申请
                request_msg = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=username,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING_REQUEST,
                )
                await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=request_msg).SerializeToString())
        elif message.type == chat_pb2.MessageType.DRAWING_REQUEST_APPROVE:
            # 同意画画申请：只有当前画画人可以同意
            current_drawer = self.room_id_to_drawer.get(room_id)
            if current_drawer == username:
                approved_user = message.content
                # 检查用户是否还在房间
                if room_id in self.room_id_to_websocket_to_username:
                    users_in_room = set(self.room_id_to_websocket_to_username[room_id].values())
                    if approved_user in users_in_room:
                        # 检查是否在申请列表中
                        if room_id in self.room_id_to_requests and approved_user in self.room_id_to_requests[room_id]:
                            # 从申请列表中移除
                            self.room_id_to_requests[room_id].discard(approved_user)
                            # 设置新的画画人
                            await self._set_drawer(room_id, approved_user)
        elif message.type == chat_pb2.MessageType.DRAWING:
            # 画图数据：只有当前画画人可以发送
            current_drawer = self.room_id_to_drawer.get(room_id)
            if current_drawer == username:
                # 保存画布内容
                self.room_id_to_canvas_data[room_id] = message.content
                # 广播画图数据给所有用户
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content=message.content,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING,
                )
                await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
        elif message.type == chat_pb2.MessageType.DRAWING_CLEAR:
            # 清空画布：只有当前画画人可以清空
            current_drawer = self.room_id_to_drawer.get(room_id)
            if current_drawer == username:
                # 清除保存的画布内容
                self.room_id_to_canvas_data.pop(room_id, None)
                # 广播清空画布消息
                outgoing = chat_pb2.ChatMessage(
                    user=username,
                    room_id=room_id,
                    content="",
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING_CLEAR,
                )
                await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
        elif message.type == chat_pb2.MessageType.DRAWING_STOP:
            # 退出画画：只有当前画画人可以退出
            current_drawer = self.room_id_to_drawer.get(room_id)
            if current_drawer == username:
                # 取消自动退出任务
                if room_id in self.room_id_to_auto_stop_tasks:
                    self.room_id_to_auto_stop_tasks[room_id].cancel()
                    del self.room_id_to_auto_stop_tasks[room_id]
                # 清除画画人状态和画布内容
                self.room_id_to_drawer.pop(room_id, None)
                self.room_id_to_canvas_data.pop(room_id, None)
                self.room_id_to_drawer_start_time.pop(room_id, None)
                # 广播退出画画消息
                drawer_state_msg = chat_pb2.ChatMessage(
                    user="System",
                    room_id=room_id,
                    content="",
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING_STATE,
                )
                await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=drawer_state_msg).SerializeToString())

    async def send_initial_state(self, room_id: int, websocket: WebSocket) -> None:
        """发送初始状态给新加入的用户"""
        # 发送当前画画人状态和画布内容
        current_drawer = self.room_id_to_drawer.get(room_id)
        if current_drawer:
            # 发送画画人状态
            drawer_state_msg = chat_pb2.ChatMessage(
                user="System",
                room_id=room_id,
                content=current_drawer,
                timestamp=int(time.time() * 1000),
                type=chat_pb2.MessageType.DRAWING_STATE,
            )
            await self._send_to_connection(
                room_id,
                websocket,
                chat_pb2.WsEnvelope(chat=drawer_state_msg).SerializeToString(),
            )
            
            # 如果有画布内容，发送给新用户
            canvas_data = self.room_id_to_canvas_data.get(room_id)
            if canvas_data:
                canvas_msg = chat_pb2.ChatMessage(
                    user=current_drawer,
                    room_id=room_id,
                    content=canvas_data,
                    timestamp=int(time.time() * 1000),
                    type=chat_pb2.MessageType.DRAWING,
                )
                await self._send_to_connection(
                    room_id,
                    websocket,
                    chat_pb2.WsEnvelope(chat=canvas_msg).SerializeToString(),
                )


# 全局实例
drawing_room_manager = DrawingRoomManager()
