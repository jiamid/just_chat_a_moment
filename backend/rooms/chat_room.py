"""纯聊天房间服务 - 只支持聊天和音乐功能"""
from typing import Dict, Set, Optional
import time
import asyncio

from fastapi import WebSocket
from protos import chat_pb2


class ChatRoomManager:
    """纯聊天房间管理器"""
    
    def __init__(self) -> None:
        self.room_id_to_connections: Dict[int, Set[WebSocket]] = {}
        self.room_tasks: Dict[int, asyncio.Task] = {}
        self.websocket_to_username: Dict[WebSocket, str] = {}
        self.websocket_to_user_id: Dict[WebSocket, Optional[int]] = {}
        self.room_id_to_websocket_to_username: Dict[int, Dict[WebSocket, str]] = {}

    async def connect(self, room_id: int, websocket: WebSocket, username: str, user_id: Optional[int]) -> None:
        """连接房间"""
        await websocket.accept()
        self.room_id_to_connections.setdefault(room_id, set()).add(websocket)
        self.websocket_to_username[websocket] = username
        self.websocket_to_user_id[websocket] = user_id
        self.room_id_to_websocket_to_username.setdefault(room_id, {})[websocket] = username
        
        # 如果是第一个连接，启动定时广播任务
        if len(self.room_id_to_connections[room_id]) == 1:
            self.room_tasks[room_id] = asyncio.create_task(self._broadcast_room_count_periodically(room_id))

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        """断开连接"""
        connections = self.room_id_to_connections.get(room_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            
            # 清理用户名映射
            self.websocket_to_username.pop(websocket, None)
            self.websocket_to_user_id.pop(websocket, None)
            if room_id in self.room_id_to_websocket_to_username:
                self.room_id_to_websocket_to_username[room_id].pop(websocket, None)
            
            if not connections:
                # 房间为空时清理
                if room_id in self.room_tasks:
                    self.room_tasks[room_id].cancel()
                    del self.room_tasks[room_id]
                self.room_id_to_connections.pop(room_id, None)
                self.room_id_to_websocket_to_username.pop(room_id, None)

    async def _send_to_connection(self, room_id: int, websocket: WebSocket, data: bytes) -> None:
        """向单个连接发送数据，处理错误"""
        try:
            await websocket.send_bytes(data)
        except Exception:
            try:
                await websocket.close()
            except Exception:
                pass
            self.disconnect(room_id, websocket)

    async def broadcast(self, room_id: int, data: bytes) -> None:
        """广播消息到房间所有连接"""
        connections = list(self.room_id_to_connections.get(room_id, set()))
        if not connections:
            return
        
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

    async def handle_message(self, room_id: int, websocket: WebSocket, message: chat_pb2.ChatMessage) -> None:
        """处理聊天消息"""
        username = self.websocket_to_username.get(websocket, "Anonymous")
        
        if message.type == chat_pb2.MessageType.USER_TEXT:
            # 用户文本消息
            outgoing = chat_pb2.ChatMessage(
                user=username,
                room_id=room_id,
                content=message.content,
                timestamp=int(time.time() * 1000),
                type=chat_pb2.MessageType.USER_TEXT,
            )
            await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())
        elif message.type == chat_pb2.MessageType.MUSIC:
            # 音乐消息
            delayed_timestamp = int((time.time() + 0.5) * 1000)
            outgoing = chat_pb2.ChatMessage(
                user=username,
                room_id=room_id,
                content=message.content,
                timestamp=delayed_timestamp,
                type=chat_pb2.MessageType.MUSIC,
            )
            await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=outgoing).SerializeToString())


# 全局实例
chat_room_manager = ChatRoomManager()
