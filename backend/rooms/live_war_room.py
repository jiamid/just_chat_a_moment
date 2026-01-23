"""LiveWar游戏房间服务 - 支持聊天、音乐和游戏功能"""
from typing import Dict, Set, Optional
import time

from fastapi import WebSocket
from protos import chat_pb2, game_pb2
from .chat_room import ChatRoomManager
from service import game_manager as live_war_game_manager


class LiveWarRoomManager(ChatRoomManager):
    """LiveWar游戏房间管理器 - 继承聊天房间功能，增加游戏功能"""
    
    def __init__(self) -> None:
        super().__init__()

    async def handle_message(self, room_id: int, websocket: WebSocket, message: chat_pb2.ChatMessage) -> None:
        """处理消息 - 重写以支持游戏功能"""
        # 处理聊天和音乐消息（继承父类功能）
        if message.type in (chat_pb2.MessageType.USER_TEXT, chat_pb2.MessageType.MUSIC):
            await super().handle_message(room_id, websocket, message)

    async def handle_game_message(self, room_id: int, websocket: WebSocket, game_message: game_pb2.GameMessage) -> None:
        """处理游戏消息"""
        username = self.websocket_to_username.get(websocket, "Anonymous")
        user_id = self.websocket_to_user_id.get(websocket)
        
        # 分发给简化版 LiveWar 管理器
        gm = live_war_game_manager.game_manager

        # 设置广播回调（如果还没有设置）
        if room_id not in gm.broadcast_callbacks:
            async def broadcast_callback(msg: game_pb2.GameMessage):
                """游戏循环的广播回调"""
                connections = list(self.room_id_to_connections.get(room_id, set()))
                for ws in connections:
                    uid_ws = self.websocket_to_user_id.get(ws)
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
            user_id=user_id,
            username=username,
            msg=game_message,
        )

        # 按玩家/观战者裁剪状态并广播
        connections = list(self.room_id_to_connections.get(room_id, set()))
        for ws in connections:
            uid_ws = self.websocket_to_user_id.get(ws)
            for gm_msg in outgoing_msgs:
                # ERROR 消息只发送给触发错误的玩家（uid），不广播给其他人
                if gm_msg.type == game_pb2.GameMessage.ERROR:
                    if uid_ws != user_id:
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

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        """断开连接 - 重写以处理游戏相关清理"""
        super().disconnect(room_id, websocket)
        
        # 如果房间为空，清理游戏状态
        if room_id not in self.room_id_to_connections:
            gm = live_war_game_manager.game_manager
            # 停止游戏循环
            gm._stop_game_loop(room_id)
            # 删除游戏状态
            if room_id in gm.room_states:
                del gm.room_states[room_id]
            # 删除广播回调
            if room_id in gm.broadcast_callbacks:
                del gm.broadcast_callbacks[room_id]

    async def send_initial_state(self, room_id: int, websocket: WebSocket) -> None:
        """发送初始状态给新加入的用户"""
        # 发送当前游戏状态给新加入的用户
        gm = live_war_game_manager.game_manager
        uid = self.websocket_to_user_id.get(websocket)
        state = gm.build_state_for_user(room_id, uid)
        if state:
            game_state_msg = game_pb2.GameMessage(
                type=game_pb2.GameMessage.GAME_STATE,
                game_state=state,
            )
            await self._send_to_connection(
                room_id,
                websocket,
                chat_pb2.WsEnvelope(game=game_state_msg).SerializeToString(),
            )


# 全局实例
live_war_room_manager = LiveWarRoomManager()
