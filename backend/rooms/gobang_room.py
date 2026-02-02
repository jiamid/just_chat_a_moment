"""五子棋游戏房间服务 - 在聊天房间基础上增加简单对战规则

设计目标：
- 每个房间只允许一场对战（进程生命周期内）。
- 一局只允许两名对战玩家：黑子和白子。
- 其他加入房间的用户一律视为观战者。
- 一旦对局开始，之后加入的用户不能再成为对战玩家，只能观战。

协议设计（基于 ChatMessage 自定义类型，走 WsEnvelope.chat 通道）：
- 普通聊天：沿用 USER_TEXT 语义，不做限制。
- 五子棋状态：ChatMessage.type = GOBANG_STATE_TYPE，content 为 JSON：
  {
    "board": [[0,1,0,...], ...],  # 15x15 棋盘，0=空,1=黑,2=白
    "current_turn": 1/2,
    "finished": true/false,
    "winner": "black"|"white"|"",
    "role": "black"|"white"|"spectator"
  }
- 五子棋落子：ChatMessage.type = GOBANG_MOVE_TYPE，content 为 JSON：
  {"x": 7, "y": 7}

注意：这里没有修改 proto 文件，而是复用现有 ChatMessage，
使用自定义的整型 type 值（GOBANG_STATE_TYPE / GOBANG_MOVE_TYPE）。
这对 protobuf 是合法的（proto3 支持未知枚举值），后续如果需要可以在 .proto 中补充枚举名。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, Set
import time
import json
import random

from fastapi import WebSocket

from protos import chat_pb2
from .chat_room import ChatRoomManager


BOARD_SIZE = 15  # 标准 15x15 五子棋
DISCONNECT_TIMEOUT_SECONDS = 300  # 对战玩家断线超时时间（5 分钟）

# 自定义的 ChatMessage.type 数值（前后端需要保持一致）
GOBANG_STATE_TYPE = 20
GOBANG_MOVE_TYPE = 21
GOBANG_JOIN_TYPE = 22
GOBANG_LEAVE_TYPE = 23


@dataclass
class GobangRoomState:
    """单个房间的五子棋状态"""

    # 玩家身份（存 user_id，便于断线重连后识别）
    black_user_id: Optional[int] = None
    white_user_id: Optional[int] = None

    # 已加入本局的玩家（最多 2 人，尚未分配黑白前暂存在这里）
    joined_user_ids: Set[int] = field(default_factory=set)

    # 当前对局是否已经开始 / 是否已经结束
    started: bool = False
    finished: bool = False

    # 棋盘：0=空，1=黑，2=白
    board: List[List[int]] = field(
        default_factory=lambda: [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    )
    # 轮到谁：1=黑，2=白
    current_turn: int = 1

    # 获胜方：0=未结束，1=黑胜，2=白胜
    winner: int = 0

    def reset_board(self) -> None:
        """重置棋盘 - 当前设计中不再被调用，仅预留"""
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_turn = 1
        self.winner = 0


class GobangRoomManager(ChatRoomManager):
    """五子棋房间管理器 - 继承聊天房间功能，增加五子棋对战约束"""

    def __init__(self) -> None:
        super().__init__()
        # room_id -> GobangRoomState
        self.room_states: Dict[int, GobangRoomState] = {}
        # 断线超时：room_id -> (asyncio.Task, 断线的 user_id)
        self._disconnect_tasks: Dict[int, Tuple[asyncio.Task, Optional[int]]] = {}

    # ---- 基本连接逻辑 ----

    async def connect(self, room_id: int, websocket: WebSocket, username: str, user_id: Optional[int]) -> None:
        """连接房间：所有人初始都是观战者，是否参与对局由之后的“加入游戏”控制"""
        # 若该用户是断线重连的对战玩家，取消超时结束任务
        self._cancel_disconnect_task_if_reconnect(room_id, user_id)

        await super().connect(room_id, websocket, username, user_id)

        state = self.room_states.setdefault(room_id, GobangRoomState())

        # 初始身份均为观战者，在发送 GOBANG_JOIN 消息后才决定是否进入对局
        await self._send_role_message(room_id, websocket, "spectator")

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        """断开连接 - 若为对战玩家则启动 5 分钟超时，超时后自动结束对局"""
        # 必须在 super().disconnect 之前获取 user_id，否则会被清理
        user_id = self.websocket_to_user_id.get(websocket)
        state = self.room_states.get(room_id)

        super().disconnect(room_id, websocket)

        # 若对局进行中且断开的是黑/白玩家，启动 5 分钟超时任务
        if (
            state
            and state.started
            and not state.finished
            and user_id is not None
            and (user_id == state.black_user_id or user_id == state.white_user_id)
        ):
            self._start_disconnect_timeout(room_id, user_id)

    # ---- 消息处理 ----

    async def handle_message(self, room_id: int, websocket: WebSocket, message: chat_pb2.ChatMessage) -> None:
        """处理消息：聊天 / 音乐 / 五子棋指令"""
        username = self.websocket_to_username.get(websocket, "Anonymous")
        user_id = self.websocket_to_user_id.get(websocket)

        # 五子棋加入游戏
        if message.type == GOBANG_JOIN_TYPE:
            await self._handle_gobang_join_message(room_id, websocket, username, user_id)
            return

        # 五子棋退出等待队列
        if message.type == GOBANG_LEAVE_TYPE:
            await self._handle_gobang_leave_message(room_id, websocket, username, user_id)
            return

        # 五子棋落子消息
        if message.type == GOBANG_MOVE_TYPE:
            await self._handle_gobang_move_message(room_id, websocket, username, user_id, message.content)
            return

        # 聊天与音乐消息仍然正常处理
        if message.type in (chat_pb2.MessageType.USER_TEXT, chat_pb2.MessageType.MUSIC):
            await super().handle_message(room_id, websocket, message)
        else:
            # 其他类型暂不做扩展，直接沿用父类逻辑
            await super().handle_message(room_id, websocket, message)

    async def send_initial_state(self, room_id: int, websocket: WebSocket) -> None:
        """新加入用户时，发送当前五子棋状态（包含棋盘 + 身份）"""
        state = self.room_states.get(room_id)
        if not state:
            return

        user_id = self.websocket_to_user_id.get(websocket)
        payload = self._build_state_payload(room_id, state, user_id)

        state_msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=json.dumps(payload, ensure_ascii=False),
            timestamp=int(time.time() * 1000),
            type=GOBANG_STATE_TYPE,
        )
        await self._send_to_connection(
            room_id,
            websocket,
            chat_pb2.WsEnvelope(chat=state_msg).SerializeToString(),
        )

    # ---- 内部工具方法 ----

    async def _broadcast_system(self, room_id: int, content: str) -> None:
        """广播系统提示"""
        msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=content,
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=msg).SerializeToString())

    async def _send_role_message(self, room_id: int, websocket: WebSocket, role: str) -> None:
        """单独向某个用户说明其在本房间中的身份"""
        role_desc = {
            "black": "你是本局五子棋的黑子玩家（先手）",
            "white": "你是本局五子棋的白子玩家（后手）",
            "spectator": "你是观战者，本局落子权只属于黑子和白子玩家",
        }.get(role, "你是观战者，本局落子权只属于黑子和白子玩家")

        msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=role_desc,
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await self._send_to_connection(room_id, websocket, chat_pb2.WsEnvelope(chat=msg).SerializeToString())

    async def _handle_gobang_move_message(
        self,
        room_id: int,
        websocket: WebSocket,
        username: str,
        user_id: Optional[int],
        content: str,
    ) -> None:
        """解析并处理五子棋落子指令（content 为 JSON: {"x": int, "y": int}）"""
        state = self.room_states.setdefault(room_id, GobangRoomState())

        # 一局结束后不再接受任何落子（保持“每房间一局”的约束）
        if state.finished:
            await self._send_error(room_id, websocket, "本房间的五子棋对局已经结束，不能再落子。")
            return

        # 对局尚未开始或玩家身份不足
        if not state.started or state.black_user_id is None or state.white_user_id is None:
            await self._send_error(room_id, websocket, "五子棋对局尚未开始或玩家尚未就位。")
            return

        if user_id is None:
            await self._send_error(room_id, websocket, "未登录用户不能参与五子棋对局，只能观战。")
            return

        # 判断当前用户是否为黑/白玩家
        if user_id == state.black_user_id:
            player_color = 1
        elif user_id == state.white_user_id:
            player_color = 2
        else:
            await self._send_error(room_id, websocket, "你不是本局的对战玩家，只能观战。")
            return

        # 轮到谁落子
        if player_color != state.current_turn:
            await self._send_error(room_id, websocket, "还没轮到你落子。")
            return

        # 解析坐标
        try:
            data = json.loads(content or "{}")
            x = int(data.get("x"))
            y = int(data.get("y"))
        except Exception:
            await self._send_error(room_id, websocket, "指令格式错误，应为 JSON: {\"x\": 7, \"y\": 7}")
            return

        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            await self._send_error(room_id, websocket, f"坐标越界，合法范围为 [0, {BOARD_SIZE - 1}]。")
            return

        if state.board[y][x] != 0:
            await self._send_error(room_id, websocket, "该位置已经有棋子了，请选择其他位置。")
            return

        # 落子
        state.board[y][x] = player_color

        # 检查是否五连
        if self._check_winner(state.board, x, y, player_color):
            state.finished = True
            state.winner = player_color

            # 获取双方用户名（在重置前）
            black_name = self._get_username_by_user_id(room_id, state.black_user_id)
            white_name = self._get_username_by_user_id(room_id, state.white_user_id)
            winner_name = black_name if player_color == 1 else white_name

            game_over_msg = (
                f"🎮 对局结束！黑方：{black_name} vs 白方：{white_name} —— "
                f"{winner_name}（{'黑子' if player_color == 1 else '白子'}）获胜！可点击「加入对局」开始新一局。"
            )
            await self._broadcast_system(room_id, game_over_msg)

            # 同时作为聊天消息广播，便于在消息列表中查看
            chat_msg = chat_pb2.ChatMessage(
                user="System",
                room_id=room_id,
                content=game_over_msg,
                timestamp=int(time.time() * 1000),
                type=chat_pb2.MessageType.USER_TEXT,
            )
            await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=chat_msg).SerializeToString())

            # 重置状态，允许重新加入对局
            state.black_user_id = None
            state.white_user_id = None
            state.joined_user_ids.clear()
            state.reset_board()
            state.started = False
            state.finished = False
            state.winner = 0
        else:
            # 轮到另一方
            state.current_turn = 2 if state.current_turn == 1 else 1
            next_desc = "黑子" if state.current_turn == 1 else "白子"
            await self._broadcast_system(
                room_id,
                f"{username} 在 ({x}, {y}) 落子成功，下一手轮到 {next_desc}。",
            )

        # 向房间内所有用户广播最新棋盘状态（包含各自的 role）
        await self._broadcast_gobang_state(room_id)

    async def _handle_gobang_join_message(
        self,
        room_id: int,
        websocket: WebSocket,
        username: str,
        user_id: Optional[int],
    ) -> None:
        """处理加入五子棋对局的请求"""
        state = self.room_states.setdefault(room_id, GobangRoomState())

        if user_id is None:
            await self._send_error(room_id, websocket, "未登录用户不能加入对局，只能观战。")
            return

        if state.finished:
            await self._send_error(room_id, websocket, "本局已经结束，不能再加入，只能观战。")
            return

        # 已经在本局中（黑/白/已加入等待开局），直接返回当前状态即可
        if user_id == state.black_user_id or user_id == state.white_user_id or user_id in state.joined_user_ids:
            await self._send_error(room_id, websocket, "你已经在本局中，无需重复加入。")
            return

        # 如果已经有两个玩家在对局中（黑白已确定），不再允许第三人加入，只能观战
        if state.black_user_id is not None and state.white_user_id is not None:
            await self._send_error(room_id, websocket, "本局已满两名玩家，你只能作为观战者。")
            return

        # 记录为已申请加入的玩家
        state.joined_user_ids.add(user_id)

        # 如果当前加入人数不足 2，等待另一人
        if len(state.joined_user_ids) < 2:
            await self._send_error(room_id, websocket, "已加入对局，等待另一位玩家加入...")
            # 同时广播一条系统提示
            await self._broadcast_system(room_id, f"{username} 已加入本局，等待另一位玩家...")
            # 单独向该玩家同步当前状态（仍是观战者身份）
            await self._broadcast_gobang_state(room_id)
            return

        # 恰好两人，随机分配黑白并开始对局
        players = list(state.joined_user_ids)[:2]
        random.shuffle(players)
        state.black_user_id, state.white_user_id = players[0], players[1]
        state.started = True
        state.current_turn = 1

        await self._broadcast_system(
            room_id,
            f"五子棋对局开始：黑子（user_id={state.black_user_id}），白子（user_id={state.white_user_id}）。",
        )

        # 广播最新状态给所有人（包括观战者）
        await self._broadcast_gobang_state(room_id)

    async def _handle_gobang_leave_message(
        self,
        room_id: int,
        websocket: WebSocket,
        username: str,
        user_id: Optional[int],
    ) -> None:
        """处理退出五子棋等待队列的请求（仅在对局未开始时允许）"""
        state = self.room_states.setdefault(room_id, GobangRoomState())

        if user_id is None:
            await self._send_error(room_id, websocket, "未登录用户不能退出对局。")
            return

        # 对局已经开始则不允许退出（防止中途解散）
        if state.started:
            await self._send_error(room_id, websocket, "对局已开始，不能退出对局。")
            return

        if user_id not in state.joined_user_ids:
            await self._send_error(room_id, websocket, "你当前未在对局等待队列中，无需退出。")
            return

        # 从等待队列中移除
        state.joined_user_ids.discard(user_id)

        await self._broadcast_system(room_id, f"{username} 退出了本局等待队列。")
        await self._broadcast_gobang_state(room_id)

    def _cancel_disconnect_task_if_reconnect(self, room_id: int, user_id: Optional[int]) -> None:
        """若重连用户正是断线超时等待的玩家，取消超时任务"""
        if user_id is None:
            return
        entry = self._disconnect_tasks.pop(room_id, None)
        if entry:
            task, disconnected_uid = entry
            if disconnected_uid == user_id and not task.done():
                task.cancel()

    def _start_disconnect_timeout(self, room_id: int, disconnected_user_id: int) -> None:
        """启动断线超时任务：5 分钟后若未重连则自动结束对局"""
        # 若已有超时任务，先取消
        entry = self._disconnect_tasks.pop(room_id, None)
        if entry:
            task, _ = entry
            if not task.done():
                task.cancel()

        async def _timeout_task() -> None:
            try:
                await asyncio.sleep(DISCONNECT_TIMEOUT_SECONDS)
                await self._end_game_due_to_disconnect(room_id, disconnected_user_id)
            except asyncio.CancelledError:
                pass
            finally:
                self._disconnect_tasks.pop(room_id, None)

        task = asyncio.create_task(_timeout_task())
        self._disconnect_tasks[room_id] = (task, disconnected_user_id)

    async def _end_game_due_to_disconnect(self, room_id: int, disconnected_user_id: int) -> None:
        """因对战玩家断线超时而结束对局，重置状态并广播"""
        state = self.room_states.get(room_id)
        if not state or not state.started or state.finished:
            return

        disconnected_name = self._get_username_by_user_id(room_id, disconnected_user_id)
        other_user_id = (
            state.white_user_id if disconnected_user_id == state.black_user_id else state.black_user_id
        )
        other_name = self._get_username_by_user_id(room_id, other_user_id)
        role_desc = "黑方" if disconnected_user_id == state.black_user_id else "白方"

        game_over_msg = (
            f"⏱ 对局结束！{disconnected_name}（{role_desc}）断线超过 5 分钟，"
            f"另一方 {other_name} 获胜。可点击「加入对局」开始新一局。"
        )
        await self._broadcast_system(room_id, game_over_msg)

        chat_msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=game_over_msg,
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.USER_TEXT,
        )
        await self.broadcast(room_id, chat_pb2.WsEnvelope(chat=chat_msg).SerializeToString())

        # 重置状态
        state.black_user_id = None
        state.white_user_id = None
        state.joined_user_ids.clear()
        state.reset_board()
        state.started = False
        state.finished = False
        state.winner = 0

        await self._broadcast_gobang_state(room_id)

    def _get_username_by_user_id(self, room_id: int, user_id: Optional[int]) -> str:
        """根据 user_id 获取当前在房间内的用户名，若不在线则返回占位"""
        if user_id is None:
            return "未知"
        for ws in self.room_id_to_connections.get(room_id, set()):
            if self.websocket_to_user_id.get(ws) == user_id:
                return self.websocket_to_username.get(ws, "未知")
        return f"用户{user_id}"

    async def _send_error(self, room_id: int, websocket: WebSocket, message: str) -> None:
        """发送错误提示（系统消息，仅发给当前用户）"""
        msg = chat_pb2.ChatMessage(
            user="System",
            room_id=room_id,
            content=message,
            timestamp=int(time.time() * 1000),
            type=chat_pb2.MessageType.SYSTEM,
        )
        await self._send_to_connection(room_id, websocket, chat_pb2.WsEnvelope(chat=msg).SerializeToString())

    def _build_state_payload(
        self,
        room_id: int,
        state: GobangRoomState,
        user_id: Optional[int],
    ) -> Dict:
        """构造发送给某个用户的五子棋状态 JSON payload"""
        if user_id is not None:
            if user_id == state.black_user_id:
                role = "black"
            elif user_id == state.white_user_id:
                role = "white"
            elif user_id in state.joined_user_ids:
                role = "waiting_player"  # 已加入等待队列，显示为玩家
            else:
                role = "spectator"
        else:
            role = "spectator"

        if state.winner == 1:
            winner_str = "black"
        elif state.winner == 2:
            winner_str = "white"
        else:
            winner_str = ""

        return {
            "board": state.board,
            "current_turn": state.current_turn,
            "finished": state.finished,
            "winner": winner_str,
            "role": role,
            "room_id": room_id,
            "started": state.started,
        }

    async def _broadcast_gobang_state(self, room_id: int) -> None:
        """根据当前状态向房间内所有连接广播五子棋棋盘状态"""
        state = self.room_states.get(room_id)
        if not state:
          return

        connections = list(self.room_id_to_connections.get(room_id, set()))
        if not connections:
            return

        for ws in connections:
            uid = self.websocket_to_user_id.get(ws)
            payload = self._build_state_payload(room_id, state, uid)
            msg = chat_pb2.ChatMessage(
                user="System",
                room_id=room_id,
                content=json.dumps(payload, ensure_ascii=False),
                timestamp=int(time.time() * 1000),
                type=GOBANG_STATE_TYPE,
            )
            try:
                await ws.send_bytes(chat_pb2.WsEnvelope(chat=msg).SerializeToString())
            except Exception:
                # 发送失败时交给基础 ChatRoomManager 清理连接
                self.disconnect(room_id, ws)

    # ---- 五子棋规则校验 ----

    def _check_winner(self, board: List[List[int]], x: int, y: int, color: int) -> bool:
        """判断在 (x, y) 位置落下 color 后是否已经五连"""
        directions: List[Tuple[int, int]] = [
            (1, 0),   # 水平
            (0, 1),   # 垂直
            (1, 1),   # 正斜线
            (1, -1),  # 反斜线
        ]
        for dx, dy in directions:
            count = 1
            # 正向
            count += self._count_dir(board, x, y, dx, dy, color)
            # 反向
            count += self._count_dir(board, x, y, -dx, -dy, color)
            if count >= 5:
                return True
        return False

    def _count_dir(
        self,
        board: List[List[int]],
        x: int,
        y: int,
        dx: int,
        dy: int,
        color: int,
    ) -> int:
        """沿某个方向统计连续相同颜色的棋子数量（不含起点）"""
        cnt = 0
        cx, cy = x + dx, y + dy
        while 0 <= cx < BOARD_SIZE and 0 <= cy < BOARD_SIZE and board[cy][cx] == color:
            cnt += 1
            cx += dx
            cy += dy
        return cnt


# 全局实例
gobang_room_manager = GobangRoomManager()

