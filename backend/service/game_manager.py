from __future__ import annotations

"""
LiveWar 游戏管理器（完整版，接入 live_war 完整逻辑）

说明：
- 整合完整的游戏循环、AI、战斗、资源管理等系统
- 所有消息通过 protos/game.proto 中的 GameMessage / GameStatePayload 进行编码
"""

import asyncio
import time
import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable

from protos import game_pb2

# ========== 游戏配置常量 ==========
UNIT_TYPES = {
    "miner": {"hp": 60, "attack": 6, "speed": 1.0, "attack_range": 1.5, "energy_drop": 10},  # 略微增强
    "engineer": {"hp": 90, "attack": 12, "speed": 4.0, "attack_range": 1.5, "energy_drop": 10},  # 高速移动，快速到达战场
    "heavy_tank": {"hp": 220, "attack": 28, "speed": 0.5, "attack_range": 2.5, "energy_drop": 10},  # 略微增强肉盾能力
    "assault_tank": {"hp": 120, "attack": 32, "speed": 1.2, "attack_range": 2.5, "energy_drop": 10},  # 略微降低攻击，平衡性调整
}

UNIT_SPAWN_COST = {
    "miner": 20,
    "engineer": 50,
    "heavy_tank": 100,
    "assault_tank": 80,
}

GAME_RULES = {
    "tick_interval": 0.1,  # 100ms per tick
    "attack_cooldown": 1.0,
    "mining_speed_penalty": 0.8,
}

MINE_FIELD_CONFIG = {
    "energy_per_harvest": 10,
    "lifetime": 180,  # 3 minutes
    "spawn_interval": 60,  # 1 minute
    "energy_max": 1000,  # 矿场最大能量
    "regen_rate": 30,  # 每秒恢复30能量
}

ENERGY_CONFIG = {
    "hp_restore_percent": 0.5,
    "drop_lifetime": 60,
}


@dataclass
class BaseState:
    """简单的基地状态"""

    x: float
    y: float
    hp: int = 1000
    hp_max: int = 1000


@dataclass
class UnitState:
    """完整的单位状态"""

    id: str  # 改为字符串，使用 uuid
    type: str  # "miner" / "engineer" / "heavy_tank" / "assault_tank"
    team: str  # "red" / "blue"
    owner_id: int
    x: float
    y: float
    hp: int = 100
    hp_max: int = 100
    attack: int = 10
    speed: float = 1.0
    attack_range: float = 1.5
    is_dead: bool = False
    carrying_energy: int = 0
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_id: Optional[str] = None  # 攻击目标ID
    last_attack_time: float = 0.0
    is_mining: bool = False


@dataclass
class MineFieldState:
    """矿场状态"""

    id: str
    x: float
    y: float
    energy: int
    energy_max: int
    created_time: float = 0.0
    lifetime: float = 180.0


@dataclass
class EnergyDrop:
    """掉落的能量"""

    id: str
    x: float
    y: float
    energy: int
    drop_time: float


@dataclass
class HealEffect:
    """治疗特效"""

    id: str
    x: float
    y: float
    created_time: float
    team: str
    lifetime: float = 0.5


@dataclass
class BulletEffect:
    """子弹特效"""

    id: str
    from_x: float
    from_y: float
    to_x: float
    to_y: float
    created_time: float
    team: str
    lifetime: float = 0.3


@dataclass
class RoomGameState:
    """单个聊天室房间的游戏状态（完整版）"""

    # 真正加入游戏的玩家（玩家 = 聊天室用户）
    players: Dict[int, str] = field(default_factory=dict)  # user_id -> username
    # 已选择的阵营
    teams: Dict[int, str] = field(default_factory=dict)  # user_id -> "red"/"blue"
    tick: int = 0
    game_started: bool = False
    game_start_time: float = 0.0
    game_time: float = 0.0
    winner: str = ""  # "red" / "blue" / ""
    game_over_time: float = 0.0

    # 地图 / 基地 / 单位
    width: int = 60
    height: int = 60
    red_base: BaseState | None = None
    blue_base: BaseState | None = None
    units: List[UnitState] = field(default_factory=list)
    mine_fields: List[MineFieldState] = field(default_factory=list)
    energy_drops: List[EnergyDrop] = field(default_factory=list)
    heal_effects: List[HealEffect] = field(default_factory=list)
    bullet_effects: List[BulletEffect] = field(default_factory=list)
    walls: List[tuple[float, float]] = field(default_factory=list)  # (x, y) positions

    # 玩家能量 & 选中的单位类型
    energies: Dict[int, int] = field(default_factory=dict)  # user_id -> energy
    selected_unit_type: Dict[int, str] = field(default_factory=dict)  # user_id -> unit_type

    # 游戏循环相关
    last_mine_spawn_time: float = 0.0
    player_logs: Dict[int, List[str]] = field(default_factory=dict)  # user_id -> logs
    
    # 玩家主矿工跟踪（用于自动重生）
    player_main_miner_id: Dict[int, str] = field(default_factory=dict)  # user_id -> unit_id (主矿工ID)
    player_miner_death_time: Dict[int, float] = field(default_factory=dict)  # user_id -> death_time (主矿工死亡时间)


class LiveWarGameManager:
    """
    LiveWar 游戏管理器（完整版）

    整合完整的游戏循环、AI、战斗、资源管理等系统
    """

    def __init__(self) -> None:
        # room_id -> RoomGameState
        self.room_states: Dict[int, RoomGameState] = {}
        # room_id -> asyncio.Task (游戏循环任务)
        self.game_tasks: Dict[int, Optional[asyncio.Task]] = {}
        # 广播回调函数：room_id -> Callable[[game_pb2.GameMessage], Awaitable[None]]
        self.broadcast_callbacks: Dict[int, Callable[[game_pb2.GameMessage], any]] = {}

    def set_broadcast_callback(self, room_id: int, callback: Callable[[game_pb2.GameMessage], any]) -> None:
        """设置房间的广播回调函数（由 rooms.py 调用，可以是同步或异步）"""
        self.broadcast_callbacks[room_id] = callback

    def _start_game_loop(self, room_id: int) -> None:
        """启动房间的游戏循环（如果还没有启动）"""
        if room_id in self.game_tasks and self.game_tasks[room_id] and not self.game_tasks[room_id].done():
            return  # 已经在运行

        async def game_loop():
            try:
                while room_id in self.room_states:
                    state = self.room_states.get(room_id)
                    if not state or not state.players:
                        break  # 房间已删除或没有玩家

                    try:
                        await self._process_tick(room_id)
                    except Exception as e:
                        # 记录错误但继续运行游戏循环
                        print(f"[GameLoop] Error in _process_tick for room {room_id}: {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                    
                    await asyncio.sleep(GAME_RULES["tick_interval"])
            except asyncio.CancelledError:
                pass
            except Exception as e:
                # 记录严重错误
                print(f"[GameLoop] Fatal error in game loop for room {room_id}: {e}", flush=True)
                import traceback
                traceback.print_exc()

        self.game_tasks[room_id] = asyncio.create_task(game_loop())

    def _stop_game_loop(self, room_id: int) -> None:
        """停止房间的游戏循环"""
        if room_id in self.game_tasks and self.game_tasks[room_id]:
            self.game_tasks[room_id].cancel()
            self.game_tasks[room_id] = None

    # ========== 对外主入口 ==========

    def handle_envelope_from_client(
        self,
        room_id: int,
        user_id: Optional[int],
        username: str,
        msg: game_pb2.GameMessage,
    ) -> list[game_pb2.GameMessage]:
        """
        处理客户端发来的 GameMessage，返回需要广播给整个房间的 GameMessage 列表。

        注意：
        - user_id 可能为 None（未登录匿名观战），这类用户只能观战，不能 join_game。
        """
        state = self._ensure_room(room_id)

        outgoing: list[game_pb2.GameMessage] = []

        if msg.type == game_pb2.GameMessage.JOIN_GAME:
            if user_id is None:
                # 匿名用户不能直接加入游戏，但仍然可以观战
                err = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.ERROR,
                    error=game_pb2.ErrorPayload(message="请先登录再加入游戏"),
                )
                outgoing.append(err)
                return outgoing

            # 记录玩家与阵营
            state.players[user_id] = username
            team = msg.join_game.team or "red"
            state.teams[user_id] = team
            # 初始化能量与默认单位类型
            state.energies.setdefault(user_id, 100)
            state.selected_unit_type.setdefault(user_id, "miner")

            # 为玩家生成一个基础单位，靠近对应基地
            self._spawn_basic_unit_for_player(room_id, user_id, team)

            # 广播玩家加入事件
            join_evt = game_pb2.GameMessage(
                type=game_pb2.GameMessage.PLAYER_JOINED,
                player_event=game_pb2.PlayerEventPayload(
                    player_id=str(user_id),
                    player_name=username,
                    team=team,
                ),
            )
            outgoing.append(join_evt)

            # 检查游戏是否刚结束（10秒内），如果是则禁止开始新游戏
            current_time = time.time()
            if state.winner and state.game_over_time > 0:
                time_since_game_over = current_time - state.game_over_time
                if time_since_game_over < 10:
                    err = game_pb2.GameMessage(
                        type=game_pb2.GameMessage.ERROR,
                        error=game_pb2.ErrorPayload(
                            message=f"游戏刚结束，请等待 {int(10 - time_since_game_over)} 秒后再开始新游戏"
                        ),
                    )
                    outgoing.append(err)
                    return outgoing

            # 检查红蓝双方是否都有至少一名玩家
            red_players = [uid for uid, t in state.teams.items() if t == "red"]
            blue_players = [uid for uid, t in state.teams.items() if t == "blue"]
            has_red_player = len(red_players) > 0
            has_blue_player = len(blue_players) > 0

            # 只有当红蓝双方都有至少一名玩家时，才自动开始游戏
            if not state.game_started and has_red_player and has_blue_player:
                state.game_started = True
                state.game_start_time = time.time()
                state.last_mine_spawn_time = time.time()
                # 确保游戏开始时生成初始矿场（如果还没有）
                if not state.mine_fields:
                    self._spawn_initial_mine_fields(room_id)
                started_msg = game_pb2.GameMessage(type=game_pb2.GameMessage.GAME_STARTED)
                outgoing.append(started_msg)
                # 启动游戏循环
                self._start_game_loop(room_id)

            # 广播一次完整状态
            state.tick += 1
            outgoing.append(
                game_pb2.GameMessage(
                    type=game_pb2.GameMessage.GAME_STATE,
                    game_state=self._build_state_for_room(room_id),
                )
            )

        elif msg.type == game_pb2.GameMessage.LEAVE_GAME:
            if user_id is None:
                return outgoing
            
            # 如果游戏已经开始，不允许退出
            if state.game_started:
                err = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.ERROR,
                    error=game_pb2.ErrorPayload(message="游戏已经开始，无法退出队伍"),
                )
                outgoing.append(err)
                return outgoing
            
            # 游戏未开始，允许退出
            if user_id in state.players:
                state.players.pop(user_id, None)
                state.teams.pop(user_id, None)
                state.energies.pop(user_id, None)
                state.selected_unit_type.pop(user_id, None)
                # 移除玩家的主矿工（如果存在）
                if user_id in state.player_main_miner_id:
                    miner_id = state.player_main_miner_id.pop(user_id)
                    # 从单位列表中移除该矿工
                    state.units = [u for u in state.units if u.id != miner_id]
                if user_id in state.player_miner_death_time:
                    state.player_miner_death_time.pop(user_id)
                
                leave_evt = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.PLAYER_LEFT,
                    player_event=game_pb2.PlayerEventPayload(
                        player_id=str(user_id),
                        player_name=username,
                        team="",
                    ),
                )
                outgoing.append(leave_evt)

                state.tick += 1
                outgoing.append(
                    game_pb2.GameMessage(
                        type=game_pb2.GameMessage.GAME_STATE,
                        game_state=self._build_state_for_room(room_id),
                    )
                )

        elif msg.type == game_pb2.GameMessage.SELECT_UNIT:
            if user_id is None or user_id not in state.players:
                return outgoing
            unit_type = msg.select_unit.unit_type or "miner"
            state.selected_unit_type[user_id] = unit_type
            # 仅广播新的状态（前端可以用 player.selected_unit_type）
            state.tick += 1
            outgoing.append(
                game_pb2.GameMessage(
                    type=game_pb2.GameMessage.GAME_STATE,
                    game_state=self._build_state_for_room(room_id),
                )
            )

        elif msg.type == game_pb2.GameMessage.SPAWN_UNIT:
            if user_id is None or user_id not in state.players:
                return outgoing
            # 简单的能量消耗配置
            unit_type = state.selected_unit_type.get(user_id, "miner")
            cost_map = {
                "miner": 20,
                "engineer": 40,
                "heavy_tank": 80,
                "assault_tank": 60,
            }
            cost = cost_map.get(unit_type, 20)
            energy = state.energies.get(user_id, 0)
            if energy < cost:
                err = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.ERROR,
                    error=game_pb2.ErrorPayload(message="能量不足"),
                )
                outgoing.append(err)
                return outgoing

            state.energies[user_id] = energy - cost
            # 生成单位
            self._spawn_basic_unit_for_player(room_id, user_id, state.teams.get(user_id, "red"), unit_type)
            # 注意：不再在生成时立即采集，让矿工在游戏循环中自动采集

            state.tick += 1
            outgoing.append(
                game_pb2.GameMessage(
                    type=game_pb2.GameMessage.GAME_STATE,
                    game_state=self._build_state_for_room(room_id),
                )
            )

        # 其他 SELECT_TEAM / SELECT_UNIT / SPAWN_UNIT 等逻辑，后续可从 live_war 中迁移

        return outgoing

    # ========== 状态构建与观战裁剪 ==========

    def _ensure_room(self, room_id: int) -> RoomGameState:
        """确保房间有基础地图和基地"""
        if room_id not in self.room_states:
            state = RoomGameState()
            # 简单地图：宽60高60，红方在左下角，蓝方在右上角
            state.width = 60
            state.height = 60
            state.red_base = BaseState(x=8, y=state.height - 8, hp=1000, hp_max=1000)  # 左下角
            state.blue_base = BaseState(x=state.width - 8, y=8, hp=1000, hp_max=1000)  # 右上角
            # 初始矿场会在 _spawn_initial_mine_fields 中生成，这里不生成
            state.last_mine_spawn_time = time.time()
            self.room_states[room_id] = state
        return self.room_states[room_id]

    def _spawn_basic_unit_for_player(self, room_id: int, user_id: int, team: str, unit_type: str = "miner") -> None:
        """为玩家生成一个单位，靠近己方基地"""
        state = self._ensure_room(room_id)
        base = state.red_base if team == "red" else state.blue_base
        if not base:
            return

        # 使用配置获取单位属性
        unit_config = UNIT_TYPES.get(unit_type, UNIT_TYPES["miner"])
        unit_id = str(uuid.uuid4())[:8]

        # 在基地附近随机一点
        offset_y = random.uniform(-2, 2)
        spawn_x = base.x + (2 if team == "red" else -2)
        spawn_y = base.y + offset_y

        unit = UnitState(
            id=unit_id,
            type=unit_type,
            team=team,
            owner_id=user_id,
            x=spawn_x,
            y=spawn_y,
            hp=unit_config["hp"],
            hp_max=unit_config["hp"],
            attack=unit_config["attack"],
            speed=unit_config["speed"],
            attack_range=unit_config["attack_range"],
            target_x=spawn_x,
            target_y=spawn_y,
        )
        state.units.append(unit)
        
        # 如果这是玩家的主矿工（初始单位），记录其ID
        if unit_type == "miner":
            state.player_main_miner_id[user_id] = unit_id
            # 清除死亡时间（如果存在）
            if user_id in state.player_miner_death_time:
                del state.player_miner_death_time[user_id]

    def _harvest_from_nearest_mine(self, room_id: int, user_id: int) -> None:
        """简化采矿：矿工生成时，从最近矿场采集一部分能量给玩家"""
        state = self._ensure_room(room_id)
        if not state.mine_fields:
            return
        # 找最近且还有能量的矿
        best: MineFieldState | None = None
        best_dist = 1e9
        # 取玩家最近单位位置作为参考
        units = [u for u in state.units if u.owner_id == user_id and not u.is_dead]
        if not units:
            return
        ux, uy = units[-1].x, units[-1].y
        for mine in state.mine_fields:
            if mine.energy <= 0:
                continue
            dist = (mine.x - ux) ** 2 + (mine.y - uy) ** 2
            if dist < best_dist:
                best_dist = dist
                best = mine
        if not best:
            return
        # 采集固定量
        harvest = min(30, best.energy)
        best.energy -= harvest
        state.energies[user_id] = state.energies.get(user_id, 0) + harvest

    def _build_state_for_room(self, room_id: int) -> game_pb2.GameStatePayload:
        """
        当前简化版：构造玩家列表 + 基础地图（宽高/基地/单位）+ 阵营人数。
        """
        state = self._ensure_room(room_id)

        # 构造玩家摘要列表
        player_summaries = []
        for uid, name in state.players.items():
            player_summaries.append(
                game_pb2.PlayerSummary(
                    id=str(uid),
                    name=name,
                    team=state.teams.get(uid, ""),
                )
            )

        # 阵营统计：按单位数量
        red_count = sum(1 for u in state.units if u.team == "red" and not u.is_dead)
        blue_count = sum(1 for u in state.units if u.team == "blue" and not u.is_dead)

        team_stats = game_pb2.TeamStatsMap(
            red=game_pb2.TeamStats(units=red_count),
            blue=game_pb2.TeamStats(units=blue_count),
        )

        # 构造 Room（基础地图 + 基地 + 单位 + 矿场）
        room_msg = game_pb2.Room(
            name=f"Room-{room_id}",
            width=state.width,
            height=state.height,
        )

        # 基地
        if state.red_base:
            room_msg.red_base.id = "red_base"
            room_msg.red_base.x = state.red_base.x
            room_msg.red_base.y = state.red_base.y
            room_msg.red_base.hp = int(state.red_base.hp)  # 确保是整数
            room_msg.red_base.hp_max = int(state.red_base.hp_max)  # 确保是整数

        if state.blue_base:
            room_msg.blue_base.id = "blue_base"
            room_msg.blue_base.x = state.blue_base.x
            room_msg.blue_base.y = state.blue_base.y
            room_msg.blue_base.hp = int(state.blue_base.hp)  # 确保是整数
            room_msg.blue_base.hp_max = int(state.blue_base.hp_max)  # 确保是整数

        # 矿场
        for m in state.mine_fields:
            mine_msg = room_msg.mine_fields.add()
            mine_msg.id = m.id
            mine_msg.x = m.x
            mine_msg.y = m.y
            mine_msg.energy = int(m.energy)  # 确保是整数
            mine_msg.energy_max = int(m.energy_max)  # 确保是整数

        # 单位
        for u in state.units:
            unit_msg = room_msg.units.add()
            unit_msg.id = u.id
            unit_msg.type = u.type
            unit_msg.team = u.team
            unit_msg.owner_id = str(u.owner_id)
            unit_msg.x = u.x
            unit_msg.y = u.y
            unit_msg.hp = int(u.hp)  # 确保是整数
            unit_msg.hp_max = int(u.hp_max)  # 确保是整数
            unit_msg.attack = u.attack
            unit_msg.speed = u.speed
            unit_msg.is_dead = u.is_dead
            unit_msg.carrying_energy = u.carrying_energy
            unit_msg.target_x = u.target_x or 0.0
            unit_msg.target_y = u.target_y or 0.0

        # 能量掉落
        for drop in state.energy_drops:
            drop_msg = room_msg.energy_drops.add()
            drop_msg.id = drop.id
            drop_msg.x = drop.x
            drop_msg.y = drop.y
            drop_msg.energy = drop.energy

        # 治疗特效
        for heal in state.heal_effects:
            heal_msg = room_msg.heal_effects.add()
            heal_msg.id = heal.id
            heal_msg.x = heal.x
            heal_msg.y = heal.y
            heal_msg.created_time = heal.created_time
            heal_msg.lifetime = heal.lifetime
            heal_msg.team = heal.team

        # 子弹特效
        for bullet in state.bullet_effects:
            bullet_msg = room_msg.bullet_effects.add()
            bullet_msg.id = bullet.id
            bullet_msg.from_x = bullet.from_x
            bullet_msg.from_y = bullet.from_y
            bullet_msg.to_x = bullet.to_x
            bullet_msg.to_y = bullet.to_y
            bullet_msg.created_time = bullet.created_time
            bullet_msg.lifetime = bullet.lifetime
            bullet_msg.team = bullet.team

        # 构造日志（取所有玩家的最新日志）
        all_logs = []
        for uid in state.players:
            user_logs = state.player_logs.get(uid, [])
            all_logs.extend(user_logs[-3:])  # 每个玩家最近3条
        all_logs = all_logs[-10:]  # 总共最多10条

        payload = game_pb2.GameStatePayload(
            tick=state.tick,
            game_time=state.game_time,
            game_started=state.game_started,
            winner=state.winner,
            room=room_msg,
            logs=all_logs,
            team_stats=team_stats,
            players=player_summaries,
        )
        return payload

    def build_state_for_user(
        self,
        room_id: int,
        user_id: Optional[int],
    ) -> Optional[game_pb2.GameStatePayload]:
        """
        为指定用户构建 GameState（区分玩家 / 观战者）。

        - 如果 user_id 在 players 中：返回包含 player 字段的完整视角（但当前简化版没有 energy 等）。
        - 否则：返回观战视角（player 为空，只能看到 players 列表和 teamStats）。
        """
        if room_id not in self.room_states:
            return None
        base = self._build_state_for_room(room_id)

        if user_id is None or user_id not in self.room_states[room_id].players:
            # 观战者
            base.player.CopyFrom(game_pb2.Player())  # 空玩家
            return base

        # 玩家视角
        name = self.room_states[room_id].players[user_id]
        team = self.room_states[room_id].teams.get(user_id, "")
        energy = self.room_states[room_id].energies.get(user_id, 0)
        selected_type = self.room_states[room_id].selected_unit_type.get(user_id, "miner")
        base.player.CopyFrom(
            game_pb2.Player(
                id=str(user_id),
                name=name,
                team=team,
                selected_unit_type=selected_type,
                energy=energy,
            )
        )
        return base

    def has_active_players(self, room_id: int) -> bool:
        state = self.room_states.get(room_id)
        return bool(state and state.players)

    # ========== 游戏循环 ==========

    async def _process_tick(self, room_id: int) -> None:
        """处理一个游戏 tick"""
        state = self.room_states.get(room_id)
        if not state or not state.game_started:
            return

        # 游戏已结束，检查是否需要重置（10秒后重置）
        if state.winner:
            current_time = time.time()
            if state.game_over_time > 0 and current_time - state.game_over_time >= 10:
                self._reset_game(room_id)
            return

        state.tick += 1
        state.game_time = time.time() - state.game_start_time
        current_time = time.time()

        # 1. 处理矿场刷新
        self._process_mine_field_refresh(room_id, current_time)

        # 2. 处理单位AI行为
        self._process_unit_ai(room_id, current_time)

        # 3. 处理战斗
        self._process_combat(room_id, current_time)

        # 4. 清理过期的能量掉落和特效
        self._cleanup_energy_drops(room_id, current_time)
        self._cleanup_effects(room_id, current_time)

        # 5. 检查并重生玩家的主矿工（死亡5秒后自动重生）
        self._check_and_respawn_player_miners(room_id, current_time)

        # 6. 检查游戏结束条件
        await self._check_game_over(room_id)

        # 7. 广播状态（每 tick 都广播）
        self._broadcast_state(room_id)

    def _reset_game(self, room_id: int) -> None:
        """重置游戏状态，使其可以重新开始游戏"""
        if room_id not in self.room_states:
            return
        state = self.room_states[room_id]
        
        # 清空玩家记录，让玩家可以重新选择阵营
        state.players.clear()
        state.teams.clear()
        state.energies.clear()
        state.selected_unit_type.clear()
        state.player_logs.clear()
        
        # 重置游戏状态
        state.tick = 0
        state.game_started = False
        state.game_start_time = 0.0
        state.game_time = 0.0
        state.winner = ""
        state.game_over_time = 0.0
        state.last_mine_spawn_time = 0.0
        
        # 清空所有游戏实体
        state.units.clear()
        state.mine_fields.clear()
        state.energy_drops.clear()
        state.heal_effects.clear()
        state.bullet_effects.clear()
        
        # 重置基地血量
        if state.red_base:
            state.red_base.hp = state.red_base.hp_max
        if state.blue_base:
            state.blue_base.hp = state.blue_base.hp_max
        
        # 清空玩家主矿工跟踪数据
        state.player_main_miner_id.clear()
        state.player_miner_death_time.clear()
        
        # 注意：不在这里生成矿场，矿场只在游戏真正开始时生成（在 handle_envelope_from_client 中）
        
        # 广播重置后的状态，让前端知道游戏已重置
        self._broadcast_state(room_id)

    def _broadcast_state(self, room_id: int) -> None:
        """广播游戏状态给所有连接"""
        callback = self.broadcast_callbacks.get(room_id)
        if callback:
            try:
                msg = game_pb2.GameMessage(
                    type=game_pb2.GameMessage.GAME_STATE,
                    game_state=self._build_state_for_room(room_id),
                )
                # 调用回调（可能是同步或异步）
                result = callback(msg)
                # 如果是协程，创建任务执行（不等待）
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                # 广播失败不应该影响游戏循环
                print(f"[GameLoop] Error broadcasting state for room {room_id}: {e}", flush=True)
                # 不打印完整 traceback，避免日志过多

    # ========== 矿场和资源管理 ==========

    def _process_mine_field_refresh(self, room_id: int, current_time: float) -> None:
        """处理矿场刷新：移除过期矿场，定期生成新矿场，恢复能量"""
        state = self.room_states.get(room_id)
        if not state or not state.game_started:
            return  # 游戏未开始时不处理矿场

        # 移除过期的矿场
        expired = [m for m in state.mine_fields if current_time - m.created_time >= m.lifetime]
        for m in expired:
            state.mine_fields.remove(m)

        # 矿场每秒恢复30能量
        regen_per_tick = MINE_FIELD_CONFIG["regen_rate"] * GAME_RULES["tick_interval"]
        for mine in state.mine_fields:
            if mine.energy < mine.energy_max:
                mine.energy = int(min(mine.energy_max, mine.energy + regen_per_tick))

        # 每60秒生成一个新矿场
        if current_time - state.last_mine_spawn_time >= MINE_FIELD_CONFIG["spawn_interval"]:
            self._spawn_mine_field(room_id, current_time)
            state.last_mine_spawn_time = current_time

    def _spawn_initial_mine_fields(self, room_id: int) -> None:
        """游戏开始时生成初始矿场（前面几个距离基地更近）"""
        state = self._ensure_room(room_id)
        # 确保游戏已开始
        if not state.game_started:
            return
        if state.mine_fields:
            return  # 已经有矿场了
        
        current_time = time.time()
        energy_max = MINE_FIELD_CONFIG["energy_max"]
        red_base = state.red_base
        blue_base = state.blue_base
        
        # 生成4个初始矿场：前2个距离基地较近，后2个在中场
        # 1. 红方附近矿场（距离基地8-12格）
        for i in range(2):
            attempts = 0
            while attempts < 20:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(8, 12)  # 距离基地8-12格
                mine_x = red_base.x + math.cos(angle) * distance
                mine_y = red_base.y + math.sin(angle) * distance
                mine_x = max(5, min(state.width - 5, mine_x))
                mine_y = max(5, min(state.height - 5, mine_y))
                
                # 确保不在基地上
                if self._distance(mine_x, mine_y, red_base.x, red_base.y) > 5:
                    state.mine_fields.append(
                        MineFieldState(
                            id=f"mine_{uuid.uuid4().hex[:6]}",
                            x=mine_x,
                            y=mine_y,
                            energy=energy_max,
                            energy_max=energy_max,
                            created_time=current_time,
                        )
                    )
                    break
                attempts += 1
        
        # 2. 蓝方附近矿场（距离基地8-12格）
        for i in range(2):
            attempts = 0
            while attempts < 20:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(8, 12)  # 距离基地8-12格
                mine_x = blue_base.x + math.cos(angle) * distance
                mine_y = blue_base.y + math.sin(angle) * distance
                mine_x = max(5, min(state.width - 5, mine_x))
                mine_y = max(5, min(state.height - 5, mine_y))
                
                # 确保不在基地上
                if self._distance(mine_x, mine_y, blue_base.x, blue_base.y) > 5:
                    state.mine_fields.append(
                        MineFieldState(
                            id=f"mine_{uuid.uuid4().hex[:6]}",
                            x=mine_x,
                            y=mine_y,
                            energy=energy_max,
                            energy_max=energy_max,
                            created_time=current_time,
                        )
                    )
                    break
                attempts += 1
        
        state.last_mine_spawn_time = current_time

    def _spawn_mine_field(self, room_id: int, current_time: float) -> None:
        """生成新矿场（避免过于集中在中线）"""
        state = self.room_states.get(room_id)
        if not state or not state.game_started:
            return  # 游戏未开始时不生成矿场

        red_base = state.red_base
        blue_base = state.blue_base
        energy_max = MINE_FIELD_CONFIG["energy_max"]
        
        # 随机选择在红方区域、蓝方区域或中场区域生成
        # 避免过于集中在中线
        zone = random.choice(["red", "blue", "center"])
        
        attempts = 0
        while attempts < 30:
            if zone == "red":
                # 红方区域（地图左侧）
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(8, 20)
                x = red_base.x + math.cos(angle) * distance
                y = red_base.y + math.sin(angle) * distance
            elif zone == "blue":
                # 蓝方区域（地图右侧）
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(8, 20)
                x = blue_base.x + math.cos(angle) * distance
                y = blue_base.y + math.sin(angle) * distance
            else:
                # 中场区域（但避免过于集中在中线）
                center_x = state.width / 2
                center_y = state.height / 2
                # 在中场区域随机，但避免x坐标过于接近中线
                offset_x = random.uniform(-15, 15)
                # 如果太接近中线，增加偏移
                if abs(offset_x) < 3:
                    offset_x = offset_x * 2 if offset_x >= 0 else offset_x * 2
                x = center_x + offset_x
                y = center_y + random.uniform(-8, 8)
            
            # 边界检查
            x = max(5, min(state.width - 5, x))
            y = max(5, min(state.height - 5, y))
            
            # 确保不在基地上
            dist_to_red = self._distance(x, y, red_base.x, red_base.y)
            dist_to_blue = self._distance(x, y, blue_base.x, blue_base.y)
            
            if dist_to_red > 5 and dist_to_blue > 5:
                # 检查是否与现有矿场太近（至少3格距离）
                too_close = False
                for existing_mine in state.mine_fields:
                    if self._distance(x, y, existing_mine.x, existing_mine.y) < 3:
                        too_close = True
                        break
                
                if not too_close:
                    mine = MineFieldState(
                        id=f"mine_{uuid.uuid4().hex[:6]}",
                        x=x,
                        y=y,
                        energy=energy_max,
                        energy_max=energy_max,
                        created_time=current_time,
                    )
                    state.mine_fields.append(mine)
                    return
            
            attempts += 1

    def _cleanup_energy_drops(self, room_id: int, current_time: float) -> None:
        """清理过期的能量掉落"""
        state = self.room_states.get(room_id)
        if not state:
            return
        lifetime = ENERGY_CONFIG["drop_lifetime"]
        state.energy_drops = [d for d in state.energy_drops if current_time - d.drop_time < lifetime]

    def _cleanup_effects(self, room_id: int, current_time: float) -> None:
        """清理过期的特效"""
        state = self.room_states.get(room_id)
        if not state:
            return
        state.heal_effects = [e for e in state.heal_effects if current_time - e.created_time < e.lifetime]
        state.bullet_effects = [e for e in state.bullet_effects if current_time - e.created_time < e.lifetime]

    def _check_and_respawn_player_miners(self, room_id: int, current_time: float) -> None:
        """检查并重生玩家的主矿工（死亡5秒后自动重生）"""
        state = self.room_states.get(room_id)
        if not state:
            return

        respawn_delay = 5.0  # 5秒后重生

        # 遍历所有玩家的死亡时间记录
        players_to_respawn = []
        for user_id, death_time in list(state.player_miner_death_time.items()):
            # 检查是否已经过了5秒
            if current_time - death_time >= respawn_delay:
                # 检查玩家是否还在游戏中
                if user_id in state.players and user_id in state.teams:
                    players_to_respawn.append(user_id)

        # 为需要重生的玩家重新生成主矿工
        for user_id in players_to_respawn:
            team = state.teams.get(user_id, "red")
            # 重新生成主矿工
            self._spawn_basic_unit_for_player(room_id, user_id, team, "miner")
            # 清除死亡时间记录
            del state.player_miner_death_time[user_id]

    # ========== 单位AI行为 ==========

    def _process_unit_ai(self, room_id: int, current_time: float) -> None:
        """处理所有单位的AI行为"""
        state = self.room_states.get(room_id)
        if not state:
            return

        for unit in state.units[:]:
            if unit.is_dead:
                continue

            if unit.type == "miner":
                self._ai_miner(room_id, unit, current_time)
            elif unit.type == "engineer":
                self._ai_engineer(room_id, unit, current_time)
            elif unit.type == "heavy_tank":
                self._ai_heavy_tank(room_id, unit, current_time)
            elif unit.type == "assault_tank":
                self._ai_assault_tank(room_id, unit, current_time)

    def _ai_miner(self, room_id: int, unit: UnitState, current_time: float) -> None:
        """矿工AI：采集矿场、收集能量掉落、送回基地、攻击敌人"""
        state = self.room_states.get(room_id)
        if not state:
            return

        base = state.red_base if unit.team == "red" else state.blue_base
        if not base:
            return

        # 如果携带了足够能量，送回基地
        if unit.carrying_energy >= 30:
            self._move_towards(room_id, unit, base.x, base.y)
            if self._distance(unit.x, unit.y, base.x, base.y) < 4:
                # 能量给玩家
                if unit.owner_id in state.energies:
                    state.energies[unit.owner_id] += unit.carrying_energy
                unit.carrying_energy = 0
            return

        # 优先采集掉落能量
        nearest_drop = self._find_nearest_energy_drop(room_id, unit)
        nearest_mine = self._find_nearest_mine_field(room_id, unit)

        if nearest_drop:
            drop_dist = self._distance(unit.x, unit.y, nearest_drop.x, nearest_drop.y)
            mine_dist = float('inf')
            if nearest_mine:
                mine_dist = self._distance(unit.x, unit.y, nearest_mine.x, nearest_mine.y)

            if drop_dist < mine_dist:
                self._move_towards(room_id, unit, nearest_drop.x, nearest_drop.y)
                if drop_dist < 1.5:
                    unit.carrying_energy += nearest_drop.energy
                    heal = int(unit.hp_max * ENERGY_CONFIG["hp_restore_percent"])
                    unit.hp = int(min(unit.hp_max, unit.hp + heal))
                    state.energy_drops.remove(nearest_drop)
                return

        # 去最近的矿场采集
        if nearest_mine:
            self._move_towards(room_id, unit, nearest_mine.x, nearest_mine.y)
            if self._distance(unit.x, unit.y, nearest_mine.x, nearest_mine.y) < 2:
                harvest = min(MINE_FIELD_CONFIG["energy_per_harvest"], nearest_mine.energy)
                nearest_mine.energy -= harvest
                unit.carrying_energy += harvest
            return

        # 没有能量可采集时，攻击附近的敌人
        enemy = self._find_nearest_enemy(room_id, unit)
        if enemy:
            unit.target_id = enemy.id
            self._move_towards(room_id, unit, enemy.x, enemy.y)
        else:
            # 没有敌人，返回基地附近待命
            if base:
                self._move_towards(room_id, unit, base.x, base.y)

    def _ai_engineer(self, room_id: int, unit: UnitState, current_time: float) -> None:
        """工程师AI：只寻找残血单位，无残血单位回基地"""
        state = self.room_states.get(room_id)
        if not state:
            return

        base = state.red_base if unit.team == "red" else state.blue_base
        if not base:
            return

        heal_per_tick = 10 * GAME_RULES["tick_interval"]  # 每秒10，转换为每tick
        
        # 1. 持续治疗身边3格内的所有残血友方单位
        healed_any = False
        for ally in state.units:
            if ally.is_dead or ally.team != unit.team or ally.id == unit.id:
                continue
            if ally.hp < ally.hp_max:
                dist = self._distance(unit.x, unit.y, ally.x, ally.y)
                if dist <= 3:
                    heal = min(heal_per_tick, ally.hp_max - ally.hp)
                    if heal > 0:
                        ally.hp = int(min(ally.hp_max, ally.hp + heal))
                        # 在受伤单位位置添加治疗特效
                        state.heal_effects.append(
                            HealEffect(
                                id=f"heal_{uuid.uuid4().hex[:6]}",
                                x=ally.x,
                                y=ally.y,
                                created_time=current_time,
                                team=unit.team,
                            )
                        )
                        healed_any = True
        
        # 治疗身边3格内的基地
        if base.hp < base.hp_max:
            dist_to_base = self._distance(unit.x, unit.y, base.x, base.y)
            if dist_to_base <= 3:
                heal = min(heal_per_tick, base.hp_max - base.hp)
                if heal > 0:
                    base.hp = int(min(base.hp_max, base.hp + heal))
                state.heal_effects.append(
                    HealEffect(
                        id=f"heal_{uuid.uuid4().hex[:6]}",
                        x=base.x,
                        y=base.y,
                        created_time=current_time,
                        team=unit.team,
                    )
                )
                healed_any = True
        
        # 如果正在治疗，在工程师位置也添加治疗特效（用于显示光环）
        if healed_any:
            state.heal_effects.append(
                HealEffect(
                    id=f"heal_engineer_{uuid.uuid4().hex[:6]}",
                    x=unit.x,
                    y=unit.y,
                    created_time=current_time,
                    team=unit.team,
                )
            )
            # 如果身边3格内有需要治疗的单位，保持当前位置（持续治疗）
            return

        # 2. 寻找残血单位（按血量百分比排序，优先最残血的）
        injured_allies = []
        for ally in state.units:
            if ally.is_dead or ally.team != unit.team or ally.id == unit.id:
                continue
            if ally.hp < ally.hp_max:
                dist = self._distance(unit.x, unit.y, ally.x, ally.y)
                hp_percent = ally.hp / ally.hp_max if ally.hp_max > 0 else 1.0
                injured_allies.append((ally, dist, hp_percent))
        
        # 按血量百分比排序（最残血的优先），然后按距离排序
        injured_allies.sort(key=lambda x: (x[2], x[1]))  # 先按血量百分比，再按距离
        
        if injured_allies:
            # 优先选择最残血的单位
            needs_heal = injured_allies[0][0]
            dist_to_ally = injured_allies[0][1]
            
            if dist_to_ally > 3:
                # 移动到距离伤员2格的位置（确保在3格治疗范围内）
                dx = needs_heal.x - unit.x
                dy = needs_heal.y - unit.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                    # 目标位置：距离伤员2格
                    target_x = needs_heal.x - dx * 2.0
                    target_y = needs_heal.y - dy * 2.0
                    # 使用工程师专用的移动方法（更好的寻路）
                    self._move_engineer_towards(room_id, unit, target_x, target_y)
        else:
            # 没有残血单位，返回基地
            self._move_engineer_towards(room_id, unit, base.x, base.y)

    def _ai_heavy_tank(self, room_id: int, unit: UnitState, current_time: float) -> None:
        """重装坦克AI：远程攻击，智能路径规划，实现包围效果"""
        state = self.room_states.get(room_id)
        if not state:
            return

        # 优先寻找敌方坦克
        enemy_tank = None
        min_dist = float('inf')
        for target in state.units:
            if target.is_dead or target.team == unit.team:
                continue
            if target.type in ["heavy_tank", "assault_tank"]:
                dist = self._distance(unit.x, unit.y, target.x, target.y)
                if dist < min_dist:
                    min_dist = dist
                    enemy_tank = target

        if enemy_tank:
            unit.target_id = enemy_tank.id
            # 如果在攻击范围内，不移动（战斗系统会处理攻击）
            if min_dist <= unit.attack_range:
                return
            # 使用智能路径规划移动到攻击范围（可以绕过障碍）
            self._move_to_attack_range(room_id, unit, enemy_tank.x, enemy_tank.y, unit.attack_range)
            return

        # 没有坦克，攻击敌方基地
        enemy_base = state.blue_base if unit.team == "red" else state.red_base
        if enemy_base and enemy_base.hp > 0:
            unit.target_id = None
            dist_to_base = self._distance(unit.x, unit.y, enemy_base.x, enemy_base.y)
            # 如果在攻击范围内，不移动
            if dist_to_base <= unit.attack_range:
                return
            # 使用智能路径规划移动到攻击范围
            self._move_to_attack_range(room_id, unit, enemy_base.x, enemy_base.y, unit.attack_range)
        else:
            # 守在前线
            base = state.red_base if unit.team == "red" else state.blue_base
            if base:
                frontline_x = base.x + (15 if unit.team == "red" else -15)
                self._move_towards(room_id, unit, frontline_x, base.y)

    def _ai_assault_tank(self, room_id: int, unit: UnitState, current_time: float) -> None:
        """突击坦克AI：远程攻击，智能路径规划，实现包围效果"""
        state = self.room_states.get(room_id)
        if not state:
            return

        # 1. 优先寻找敌方坦克
        enemy_tank = None
        min_dist = float('inf')
        for target in state.units:
            if target.is_dead or target.team == unit.team:
                continue
            if target.type in ["heavy_tank", "assault_tank"]:
                dist = self._distance(unit.x, unit.y, target.x, target.y)
                if dist < min_dist:
                    min_dist = dist
                    enemy_tank = target

        if enemy_tank:
            unit.target_id = enemy_tank.id
            # 如果在攻击范围内，不移动
            if min_dist <= unit.attack_range:
                return
            # 使用智能路径规划移动到攻击范围（可以绕过障碍）
            self._move_to_attack_range(room_id, unit, enemy_tank.x, enemy_tank.y, unit.attack_range)
            return

        # 2. 其次寻找敌方工程师
        enemy_engineer = self._find_nearest_enemy_of_type(room_id, unit, "engineer")
        if enemy_engineer:
            unit.target_id = enemy_engineer.id
            dist = self._distance(unit.x, unit.y, enemy_engineer.x, enemy_engineer.y)
            # 如果在攻击范围内，不移动
            if dist <= unit.attack_range:
                return
            # 使用智能路径规划移动到攻击范围
            self._move_to_attack_range(room_id, unit, enemy_engineer.x, enemy_engineer.y, unit.attack_range)
            return

        # 3. 最后寻找敌方矿工
        enemy_miner = self._find_nearest_enemy_of_type(room_id, unit, "miner")
        if enemy_miner:
            unit.target_id = enemy_miner.id
            dist = self._distance(unit.x, unit.y, enemy_miner.x, enemy_miner.y)
            # 如果在攻击范围内，不移动
            if dist <= unit.attack_range:
                return
            # 使用智能路径规划移动到攻击范围
            self._move_to_attack_range(room_id, unit, enemy_miner.x, enemy_miner.y, unit.attack_range)
            return

        # 没有敌人，守在前线
        base = state.red_base if unit.team == "red" else state.blue_base
        if base:
            frontline_x = base.x + (15 if unit.team == "red" else -15)
            self._move_towards(room_id, unit, frontline_x, base.y)

    # ========== 战斗系统 ==========

    def _process_combat(self, room_id: int, current_time: float) -> None:
        """处理战斗"""
        state = self.room_states.get(room_id)
        if not state:
            return

        for unit in state.units[:]:
            if unit.is_dead:
                continue

            # 检查攻击冷却
            if current_time - unit.last_attack_time < GAME_RULES["attack_cooldown"]:
                continue

            # 根据单位类型决定攻击目标
            if unit.type == "assault_tank":
                # 突击坦克：优先坦克，其次工程师，然后矿工
                attacked = False
                for target in state.units[:]:
                    if target.is_dead or target.team == unit.team:
                        continue
                    if target.type not in ["heavy_tank", "assault_tank", "engineer", "miner"]:
                        continue
                    # 优先级：坦克 > 工程师 > 矿工
                    priority = {"heavy_tank": 1, "assault_tank": 1, "engineer": 2, "miner": 3}.get(target.type, 99)
                    if priority > 3:
                        continue

                    dist = self._distance(unit.x, unit.y, target.x, target.y)
                    if dist <= unit.attack_range:
                        self._attack_unit(room_id, unit, target, current_time)
                        attacked = True
                        break

            elif unit.type == "heavy_tank":
                # 重装坦克：优先攻击坦克，如果没有坦克或坦克不在范围内，攻击基地
                attacked = False
                # 先尝试攻击敌方坦克（在攻击范围内的）
                for target in state.units[:]:
                    if target.is_dead or target.team == unit.team:
                        continue
                    if target.type not in ["heavy_tank", "assault_tank"]:
                        continue

                    dist = self._distance(unit.x, unit.y, target.x, target.y)
                    if dist <= unit.attack_range:
                        self._attack_unit(room_id, unit, target, current_time)
                        attacked = True
                        break

                # 如果没有攻击坦克，攻击基地（无论是否有坦克，只要基地在范围内就攻击）
                if not attacked:
                    enemy_base = state.blue_base if unit.team == "red" else state.red_base
                    if enemy_base and enemy_base.hp > 0:
                        dist = self._distance(unit.x, unit.y, enemy_base.x, enemy_base.y)
                        if dist <= unit.attack_range:
                            self._attack_base(room_id, unit, enemy_base, current_time)

            else:
                # 其他单位（矿工、工程师）：可以攻击所有敌人和基地
                attacked = False
                for target in state.units[:]:
                    if target.is_dead or target.team == unit.team:
                        continue

                    dist = self._distance(unit.x, unit.y, target.x, target.y)
                    if dist <= unit.attack_range:
                        self._attack_unit(room_id, unit, target, current_time)
                        attacked = True
                        break

                # 如果没有攻击单位，攻击基地
                if not attacked:
                    enemy_base = state.blue_base if unit.team == "red" else state.red_base
                    if enemy_base and enemy_base.hp > 0:
                        dist = self._distance(unit.x, unit.y, enemy_base.x, enemy_base.y)
                        if dist <= unit.attack_range:
                            self._attack_base(room_id, unit, enemy_base, current_time)

    def _attack_unit(self, room_id: int, attacker: UnitState, target: UnitState, current_time: float) -> None:
        """单位攻击单位"""
        state = self.room_states.get(room_id)
        if not state:
            return

        # 添加子弹特效（只有坦克才显示）
        if attacker.type in ["heavy_tank", "assault_tank"]:
            state.bullet_effects.append(
                BulletEffect(
                    id=f"bullet_{uuid.uuid4().hex[:6]}",
                    from_x=attacker.x,
                    from_y=attacker.y,
                    to_x=target.x,
                    to_y=target.y,
                    created_time=current_time,
                    team=attacker.team,
                )
            )

        # 造成伤害
        target.hp = int(max(0, target.hp - attacker.attack))
        attacker.last_attack_time = current_time

        # 检查是否死亡
        if target.hp <= 0:
            self._handle_unit_death(room_id, target, current_time)

    def _attack_base(self, room_id: int, attacker: UnitState, base: BaseState, current_time: float) -> None:
        """单位攻击基地"""
        state = self.room_states.get(room_id)
        if not state:
            return

        # 添加子弹特效（只有坦克才显示）
        if attacker.type in ["heavy_tank", "assault_tank"]:
            state.bullet_effects.append(
                BulletEffect(
                    id=f"bullet_{uuid.uuid4().hex[:6]}",
                    from_x=attacker.x,
                    from_y=attacker.y,
                    to_x=base.x,
                    to_y=base.y,
                    created_time=current_time,
                    team=attacker.team,
                )
            )

        base.hp = int(max(0, base.hp - attacker.attack))
        attacker.last_attack_time = current_time

    def _handle_unit_death(self, room_id: int, unit: UnitState, current_time: float) -> None:
        """处理单位死亡"""
        state = self.room_states.get(room_id)
        if not state:
            return

        if unit.is_dead:
            return

        unit.is_dead = True

        # 掉落能量
        energy_drop = unit.carrying_energy + UNIT_TYPES.get(unit.type, {}).get("energy_drop", 10)
        if energy_drop > 0:
            state.energy_drops.append(
                EnergyDrop(
                    id=f"drop_{uuid.uuid4().hex[:8]}",
                    x=unit.x,
                    y=unit.y,
                    energy=energy_drop,
                    drop_time=current_time,
                )
            )

        unit.carrying_energy = 0

        # 检查是否是玩家的主矿工死亡
        if unit.type == "miner" and unit.owner_id in state.player_main_miner_id:
            if state.player_main_miner_id[unit.owner_id] == unit.id:
                # 记录主矿工死亡时间
                state.player_miner_death_time[unit.owner_id] = current_time
                # 清除主矿工ID记录
                del state.player_main_miner_id[unit.owner_id]

        # 从列表中移除
        if unit in state.units:
            state.units.remove(unit)

    async def _check_game_over(self, room_id: int) -> None:
        """检查游戏结束条件"""
        state = self.room_states.get(room_id)
        if not state or state.winner:
            return

        # 检查基地是否被摧毁
        winner = None
        if state.red_base and state.red_base.hp <= 0:
            winner = "blue"
        elif state.blue_base and state.blue_base.hp <= 0:
            winner = "red"
        
        if winner:
            state.winner = winner
            state.game_over_time = time.time()
            
            # 构建胜利方队员列表
            winner_team_players = []
            for user_id, username in state.players.items():
                if state.teams.get(user_id) == winner:
                    winner_team_players.append(username)
            
            # 发送游戏结束消息
            winner_name = "RED" if winner == "red" else "BLUE"
            game_over_msg = game_pb2.GameMessage(
                type=game_pb2.GameMessage.GAME_OVER,
                game_over=game_pb2.GameOverPayload(
                    winner=winner,
                    winner_name=winner_name,
                ),
            )
            
            # 通过广播回调发送消息
            callback = self.broadcast_callbacks.get(room_id)
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(game_over_msg)
                    else:
                        callback(game_over_msg)
                except Exception as e:
                    # 广播失败不应该影响游戏流程
                    print(f"[GameLoop] Error broadcasting game over for room {room_id}: {e}", flush=True)

    # ========== 辅助函数 ==========

    def _distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """计算两点距离"""
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def _move_to_attack_range(self, room_id: int, unit: UnitState, target_x: float, target_y: float, attack_range: float) -> None:
        """智能移动到攻击范围内，可以绕过障碍，实现包围效果
        
        Args:
            room_id: 房间ID
            unit: 移动的单位
            target_x, target_y: 目标位置
            attack_range: 攻击范围
        """
        if unit.is_dead:
            return

        # 更新单位的目标位置（用于前端显示炮管方向）
        unit.target_x = target_x
        unit.target_y = target_y

        # 计算当前距离
        current_dist = self._distance(unit.x, unit.y, target_x, target_y)
        
        # 如果已经在攻击范围内，不需要移动
        if current_dist <= attack_range:
            return

        state = self.room_states.get(room_id)
        if not state:
            return

        # 计算包围角度：统计有多少个友方单位正在接近同一个目标
        allies_approaching = 0
        for other_unit in state.units:
            if other_unit.is_dead or other_unit.team != unit.team or other_unit.id == unit.id:
                continue
            # 检查其他单位是否也在接近同一个目标（通过目标ID或目标位置判断）
            is_approaching_same_target = False
            if unit.target_id and other_unit.target_id == unit.target_id:
                is_approaching_same_target = True
            elif other_unit.target_x is not None and other_unit.target_y is not None:
                # 检查目标位置是否接近（允许0.5的误差）
                if abs(other_unit.target_x - target_x) < 0.5 and abs(other_unit.target_y - target_y) < 0.5:
                    is_approaching_same_target = True
            
            if is_approaching_same_target:
                other_dist = self._distance(other_unit.x, other_unit.y, target_x, target_y)
                if other_dist > attack_range:  # 如果其他单位也在接近，计入包围计数
                    allies_approaching += 1

        # 根据包围单位数量，计算理想的接近角度
        # 0个单位：从正面接近（0度）
        # 1个单位：从左侧接近（-90度）
        # 2个单位：从右侧接近（90度）
        # 3个单位：从后方接近（180度）
        # 4个及以上：均匀分布角度
        angle_offset = 0.0
        if allies_approaching > 0:
            # 计算单位在包围圈中的位置索引
            position_index = allies_approaching % 4
            if position_index == 0:
                angle_offset = -90  # 左侧
            elif position_index == 1:
                angle_offset = 90   # 右侧
            elif position_index == 2:
                angle_offset = 180  # 后方
            else:
                angle_offset = -45  # 左前
        else:
            angle_offset = 0  # 正面

        # 计算目标方向（从单位到目标）
        dx = target_x - unit.x
        dy = target_y - unit.y
        main_angle = math.atan2(dy, dx)

        # 应用包围角度偏移
        approach_angle = main_angle + math.radians(angle_offset)

        # 计算理想位置：在攻击范围边缘，从指定角度接近
        ideal_dist = attack_range * 0.9  # 稍微靠近一点，确保在攻击范围内
        ideal_x = target_x - math.cos(approach_angle) * ideal_dist
        ideal_y = target_y - math.sin(approach_angle) * ideal_dist

        # 边界检查
        ideal_x = max(2, min(state.width - 3, ideal_x))
        ideal_y = max(2, min(state.height - 3, ideal_y))

        # 使用改进的路径规划移动到理想位置
        self._move_towards_smart(room_id, unit, ideal_x, ideal_y, target_x, target_y, attack_range)

    def _move_towards_smart(self, room_id: int, unit: UnitState, ideal_x: float, ideal_y: float, 
                           target_x: float, target_y: float, attack_range: float) -> None:
        """智能路径规划：尝试移动到理想位置，如果被阻挡则寻找替代路径到达攻击范围"""
        if unit.is_dead:
            return

        speed = unit.speed * GAME_RULES["tick_interval"]
        if unit.is_mining:
            speed *= GAME_RULES["mining_speed_penalty"]

        state = self.room_states.get(room_id)
        if not state:
            return

        # 计算到理想位置的方向
        dx = ideal_x - unit.x
        dy = ideal_y - unit.y
        dist_to_ideal = math.sqrt(dx * dx + dy * dy)

        if dist_to_ideal < 0.5:
            # 已经到达理想位置，检查是否在攻击范围内
            current_dist = self._distance(unit.x, unit.y, target_x, target_y)
            if current_dist <= attack_range:
                return
            # 如果不在攻击范围内，尝试直接移动到攻击范围边缘
            ideal_x = target_x
            ideal_y = target_y
            dx = ideal_x - unit.x
            dy = ideal_y - unit.y
            dist_to_ideal = math.sqrt(dx * dx + dy * dy)

        if dist_to_ideal > 0:
            dx /= dist_to_ideal
            dy /= dist_to_ideal

        # 路径预测：检查前方是否有阻塞
        lookahead_steps = 3
        path_blocked = False
        for step in range(1, lookahead_steps + 1):
            check_x = unit.x + dx * speed * step
            check_y = unit.y + dy * speed * step
            check_x = max(2, min(state.width - 3, check_x))
            check_y = max(2, min(state.height - 3, check_y))
            
            if self._is_position_blocked(room_id, check_x, check_y, unit.id, unit.type):
                path_blocked = True
                break

        # 如果路径被阻塞，尝试从多个角度绕过
        if path_blocked:
            main_angle = math.atan2(dy, dx)
            best_pos = None
            best_score = float('inf')
            
            # 尝试多个角度（每30度一个）
            for angle_offset in range(-90, 91, 30):
                angle = main_angle + math.radians(angle_offset)
                dir_x = math.cos(angle)
                dir_y = math.sin(angle)
                
                # 尝试不同步长
                for step_mult in [1.0, 0.8, 0.6]:
                    try_x = unit.x + dir_x * speed * step_mult
                    try_y = unit.y + dir_y * speed * step_mult
                    
                    try_x = max(2, min(state.width - 3, try_x))
                    try_y = max(2, min(state.height - 3, try_y))
                    
                    # 检查这个位置是否可移动
                    if not self._is_position_blocked(room_id, try_x, try_y, unit.id, unit.type):
                        # 检查从这个位置到目标的距离
                        new_dist_to_target = self._distance(try_x, try_y, target_x, target_y)
                        new_dist_to_ideal = self._distance(try_x, try_y, ideal_x, ideal_y)
                        
                        # 评分：优先选择能到达攻击范围且接近理想位置的方向
                        if new_dist_to_target <= attack_range:
                            # 如果在攻击范围内，优先选择
                            score = new_dist_to_ideal + abs(angle_offset) * 0.1
                        else:
                            # 如果不在攻击范围内，优先选择能更接近目标的方向
                            old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                            if new_dist_to_target < old_dist:
                                score = new_dist_to_target + abs(angle_offset) * 0.1
                            else:
                                continue  # 跳过这个方向
                        
                        if score < best_score:
                            best_score = score
                            best_pos = (try_x, try_y)
            
            if best_pos:
                unit.x = best_pos[0]
                unit.y = best_pos[1]
                return

        # 如果路径通畅，尝试直接移动
        new_x = unit.x + dx * speed
        new_y = unit.y + dy * speed

        new_x = max(2, min(state.width - 3, new_x))
        new_y = max(2, min(state.height - 3, new_y))

        # 检查目标位置是否被占用
        if not self._is_position_blocked(room_id, new_x, new_y, unit.id, unit.type):
            unit.x = new_x
            unit.y = new_y
            return

        # 如果直接移动被阻挡，使用8方向绕路
        main_angle = math.atan2(dy, dx)
        best_pos = None
        best_score = float('inf')
        
        main_directions = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]
        
        direction_scores = []
        for dir_x, dir_y in main_directions:
            dir_angle = math.atan2(dir_y, dir_x)
            angle_diff = abs(dir_angle - main_angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
            direction_scores.append((angle_diff, dir_x, dir_y))
        
        direction_scores.sort(key=lambda x: x[0])
        
        for angle_diff, dir_x, dir_y in direction_scores:
            for step_mult in [1.0, 0.8, 0.6, 0.4]:
                try_x = unit.x + dir_x * speed * step_mult
                try_y = unit.y + dir_y * speed * step_mult
                
                try_x = max(2, min(state.width - 3, try_x))
                try_y = max(2, min(state.height - 3, try_y))
                
                if not self._is_position_blocked(room_id, try_x, try_y, unit.id, unit.type):
                    new_dist_to_target = self._distance(try_x, try_y, target_x, target_y)
                    new_dist_to_ideal = self._distance(try_x, try_y, ideal_x, ideal_y)
                    old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                    
                    # 优先选择能到达攻击范围的位置
                    if new_dist_to_target <= attack_range:
                        score = new_dist_to_ideal + angle_diff * 0.2
                        if score < best_score:
                            best_score = score
                            best_pos = (try_x, try_y)
                    elif new_dist_to_target < old_dist:
                        score = new_dist_to_target + angle_diff * 0.2
                        if score < best_score:
                            best_score = score
                            best_pos = (try_x, try_y)
        
        if best_pos:
            unit.x = best_pos[0]
            unit.y = best_pos[1]

    def _move_towards(self, room_id: int, unit: UnitState, target_x: float, target_y: float) -> None:
        """移动单位向目标，带智能路径规划（检测前方阻塞并提前绕路）"""
        if unit.is_dead:
            return

        # 更新单位的目标位置（用于前端显示炮管方向）
        unit.target_x = target_x
        unit.target_y = target_y

        dx = target_x - unit.x
        dy = target_y - unit.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.5:
            return

        # 计算移动速度
        speed = unit.speed * GAME_RULES["tick_interval"]
        if unit.is_mining:
            speed *= GAME_RULES["mining_speed_penalty"]

        state = self.room_states.get(room_id)
        if not state:
            return

        # 归一化方向
        if dist > 0:
            dx /= dist
            dy /= dist

        # 路径预测：检查前方几步是否有阻塞
        lookahead_steps = 3  # 向前看3步
        path_blocked = False
        for step in range(1, lookahead_steps + 1):
            check_x = unit.x + dx * speed * step
            check_y = unit.y + dy * speed * step
            check_x = max(2, min(state.width - 3, check_x))
            check_y = max(2, min(state.height - 3, check_y))
            
            if self._is_position_blocked(room_id, check_x, check_y, unit.id, unit.type):
                path_blocked = True
                break

        # 如果前方路径被阻塞，提前选择旁边的路径
        if path_blocked:
            # 计算主方向角度
            main_angle = math.atan2(dy, dx)
            
            # 生成候选方向：主方向两侧各45度范围内的方向
            best_pos = None
            best_score = float('inf')
            
            # 尝试主方向两侧的方向（每15度一个）
            for angle_offset in range(-45, 46, 15):  # -45度到+45度，每15度
                angle = main_angle + math.radians(angle_offset)
                dir_x = math.cos(angle)
                dir_y = math.sin(angle)
                
                # 尝试不同步长
                for step_mult in [1.0, 0.8, 0.6]:
                    try_x = unit.x + dir_x * speed * step_mult
                    try_y = unit.y + dir_y * speed * step_mult
                    
                    # 边界检查
                    try_x = max(2, min(state.width - 3, try_x))
                    try_y = max(2, min(state.height - 3, try_y))
                    
                    # 检查这个位置是否可移动
                    if not self._is_position_blocked(room_id, try_x, try_y, unit.id, unit.type):
                        # 检查这个方向的前方是否通畅（向前看2步）
                        path_clear = True
                        for step in range(1, 3):
                            future_x = try_x + dir_x * speed * step
                            future_y = try_y + dir_y * speed * step
                            future_x = max(2, min(state.width - 3, future_x))
                            future_y = max(2, min(state.height - 3, future_y))
                            
                            if self._is_position_blocked(room_id, future_x, future_y, unit.id, unit.type):
                                path_clear = False
                                break
                        
                        if path_clear:
                            new_dist = self._distance(try_x, try_y, target_x, target_y)
                            old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                            
                            # 评分：优先选择能更接近目标且路径通畅的方向
                            angle_penalty = abs(angle_offset) * 0.1
                            score = new_dist + angle_penalty
                            
                            if new_dist < old_dist and score < best_score:
                                best_score = score
                                best_pos = (try_x, try_y)
            
            # 如果找到了更好的路径，使用它
            if best_pos:
                unit.x = best_pos[0]
                unit.y = best_pos[1]
                return

        # 如果前方路径通畅，尝试直接移动
        new_x = unit.x + dx * speed
        new_y = unit.y + dy * speed

        # 边界检查
        new_x = max(2, min(state.width - 3, new_x))
        new_y = max(2, min(state.height - 3, new_y))

        # 检查目标位置是否被占用
        if not self._is_position_blocked(room_id, new_x, new_y, unit.id, unit.type):
            unit.x = new_x
            unit.y = new_y
            return

        # 如果直接移动被阻挡，使用改进的绕路算法
        # 1. 首先尝试8个主要方向（上下左右和斜向）
        best_pos = None
        best_score = float('inf')
        main_angle = math.atan2(dy, dx)
        
        # 8个主要方向：上、右上、右、右下、下、左下、左、左上
        main_directions = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]
        
        # 计算每个方向与目标方向的夹角，按优先级排序
        direction_scores = []
        for dir_x, dir_y in main_directions:
            dir_angle = math.atan2(dir_y, dir_x)
            angle_diff = abs(dir_angle - main_angle)
            # 处理角度环绕（-π到π）
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
            direction_scores.append((angle_diff, dir_x, dir_y))
        
        # 按角度差排序，优先尝试接近目标方向的方向
        direction_scores.sort(key=lambda x: x[0])
        
        # 尝试每个方向，使用不同步长
        for angle_diff, dir_x, dir_y in direction_scores:
            for step_mult in [1.0, 0.8, 0.6, 0.4, 0.2]:
                try_x = unit.x + dir_x * speed * step_mult
                try_y = unit.y + dir_y * speed * step_mult
                
                # 边界检查
                try_x = max(2, min(state.width - 3, try_x))
                try_y = max(2, min(state.height - 3, try_y))
                
                # 检查是否可移动
                if not self._is_position_blocked(room_id, try_x, try_y, unit.id, unit.type):
                    new_dist = self._distance(try_x, try_y, target_x, target_y)
                    old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                    
                    # 评分：优先选择能更接近目标的位置
                    if new_dist < old_dist or (new_dist <= old_dist + speed * 0.5):
                        score = new_dist + angle_diff * 0.2
                        if score < best_score:
                            best_score = score
                            best_pos = (try_x, try_y)
        
        # 如果找到了更好的位置，移动过去
        if best_pos:
            unit.x = best_pos[0]
            unit.y = best_pos[1]
        else:
            # 如果完全卡住，尝试更激进的绕路：检查周围更大范围
            for radius in [1.5, 2.0, 2.5]:
                for angle_offset in range(0, 360, 45):  # 每45度尝试一次
                    angle_rad = math.radians(angle_offset)
                    try_x = unit.x + math.cos(angle_rad) * speed * radius
                    try_y = unit.y + math.sin(angle_rad) * speed * radius
                    
                    # 边界检查
                    try_x = max(2, min(state.width - 3, try_x))
                    try_y = max(2, min(state.height - 3, try_y))
                    
                    if not self._is_position_blocked(room_id, try_x, try_y, unit.id, unit.type):
                        new_dist = self._distance(try_x, try_y, target_x, target_y)
                        old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                        
                        # 只要能移动，即使稍微远离目标也可以（避免完全卡死）
                        if new_dist <= old_dist + speed * 1.0:
                            unit.x = try_x
                            unit.y = try_y
                            return

    def _is_position_blocked(self, room_id: int, x: float, y: float, exclude_unit_id: str, unit_type: str = None) -> bool:
        """检查位置是否被占用
        
        Args:
            room_id: 房间ID
            x, y: 目标位置
            exclude_unit_id: 排除的单位ID（自己）
            unit_type: 移动的单位类型，如果是engineer则有特殊规则
        """
        state = self.room_states.get(room_id)
        if not state:
            return True

        # 将坐标转换为格子坐标（向下取整）
        grid_x = int(math.floor(x))
        grid_y = int(math.floor(y))

        # 工程师特殊规则：不占用其他单位的2格限制，但每格最多2个工程师
        if unit_type == "engineer":
            engineers_in_cell = 0
            for other_unit in state.units:
                if other_unit.is_dead or other_unit.id == exclude_unit_id:
                    continue
                
                other_grid_x = int(math.floor(other_unit.x))
                other_grid_y = int(math.floor(other_unit.y))
                
                # 如果其他工程师在同一格子
                if other_grid_x == grid_x and other_grid_y == grid_y:
                    if other_unit.type == "engineer":
                        engineers_in_cell += 1
                        # 如果已经有2个工程师，则被阻挡
                        if engineers_in_cell >= 2:
                            return True
            # 工程师可以和其他单位共享格子，不检查其他单位数量
            return False
        
        # 其他单位：每个格子最多2个单位
        units_in_cell = 0
        for other_unit in state.units:
            if other_unit.is_dead or other_unit.id == exclude_unit_id:
                continue
            
            other_grid_x = int(math.floor(other_unit.x))
            other_grid_y = int(math.floor(other_unit.y))
            
            # 如果其他单位在同一格子
            if other_grid_x == grid_x and other_grid_y == grid_y:
                # 工程师不占用其他单位的2格限制
                if other_unit.type != "engineer":
                    units_in_cell += 1
                    # 如果已经有2个单位（不包括工程师），则被阻挡
                    if units_in_cell >= 2:
                        return True

        # 检查是否在墙壁上
        for wall in state.walls:
            wall_x, wall_y = wall
            if int(wall_x) == grid_x and int(wall_y) == grid_y:
                return True

        # 检查是否在基地上（不能穿过基地）
        if state.red_base:
            base_grid_x = int(math.floor(state.red_base.x))
            base_grid_y = int(math.floor(state.red_base.y))
            if base_grid_x == grid_x and base_grid_y == grid_y:
                return True

        if state.blue_base:
            base_grid_x = int(math.floor(state.blue_base.x))
            base_grid_y = int(math.floor(state.blue_base.y))
            if base_grid_x == grid_x and base_grid_y == grid_y:
                return True

        return False

    def _move_engineer_towards(self, room_id: int, unit: UnitState, target_x: float, target_y: float) -> None:
        """工程师专用的移动方法，带智能路径规划（检测前方阻塞并提前绕路）"""
        if unit.is_dead:
            return

        # 更新单位的目标位置（用于前端显示）
        unit.target_x = target_x
        unit.target_y = target_y

        dx = target_x - unit.x
        dy = target_y - unit.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.5:
            return

        # 计算移动速度
        speed = unit.speed * GAME_RULES["tick_interval"]

        state = self.room_states.get(room_id)
        if not state:
            return

        # 归一化方向
        if dist > 0:
            dx /= dist
            dy /= dist

        # 路径预测：检查前方几步是否有阻塞
        lookahead_steps = 3  # 向前看3步
        path_blocked = False
        for step in range(1, lookahead_steps + 1):
            check_x = unit.x + dx * speed * step
            check_y = unit.y + dy * speed * step
            check_x = max(2, min(state.width - 3, check_x))
            check_y = max(2, min(state.height - 3, check_y))
            
            if self._is_position_blocked(room_id, check_x, check_y, unit.id, "engineer"):
                path_blocked = True
                break

        # 如果前方路径被阻塞，提前选择旁边的路径
        if path_blocked:
            # 计算主方向角度
            main_angle = math.atan2(dy, dx)
            
            # 生成候选方向：主方向两侧各60度范围内的方向
            best_pos = None
            best_score = float('inf')
            
            # 尝试主方向两侧的方向（每15度一个）
            for angle_offset in range(-60, 61, 15):  # -60度到+60度，每15度
                angle = main_angle + math.radians(angle_offset)
                dir_x = math.cos(angle)
                dir_y = math.sin(angle)
                
                # 尝试不同步长
                for step_mult in [1.0, 0.8, 0.6]:
                    try_x = unit.x + dir_x * speed * step_mult
                    try_y = unit.y + dir_y * speed * step_mult
                    
                    # 边界检查
                    try_x = max(2, min(state.width - 3, try_x))
                    try_y = max(2, min(state.height - 3, try_y))
                    
                    # 检查这个位置是否可移动（工程师特殊规则）
                    if not self._is_position_blocked(room_id, try_x, try_y, unit.id, "engineer"):
                        # 检查这个方向的前方是否通畅（向前看2步）
                        path_clear = True
                        for step in range(1, 3):
                            future_x = try_x + dir_x * speed * step
                            future_y = try_y + dir_y * speed * step
                            future_x = max(2, min(state.width - 3, future_x))
                            future_y = max(2, min(state.height - 3, future_y))
                            
                            if self._is_position_blocked(room_id, future_x, future_y, unit.id, "engineer"):
                                path_clear = False
                                break
                        
                        if path_clear:
                            new_dist = self._distance(try_x, try_y, target_x, target_y)
                            old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                            
                            # 评分：优先选择能更接近目标且路径通畅的方向
                            angle_penalty = abs(angle_offset) * 0.05  # 较小的角度惩罚
                            score = new_dist + angle_penalty
                            
                            if new_dist < old_dist and score < best_score:
                                best_score = score
                                best_pos = (try_x, try_y)
            
            # 如果找到了更好的路径，使用它
            if best_pos:
                unit.x = best_pos[0]
                unit.y = best_pos[1]
                return

        # 如果前方路径通畅，尝试直接移动
        new_x = unit.x + dx * speed
        new_y = unit.y + dy * speed

        # 边界检查
        new_x = max(2, min(state.width - 3, new_x))
        new_y = max(2, min(state.height - 3, new_y))

        # 检查目标位置是否被占用（工程师特殊规则）
        if not self._is_position_blocked(room_id, new_x, new_y, unit.id, "engineer"):
            unit.x = new_x
            unit.y = new_y
            return

        # 如果直接移动被阻挡，使用改进的绕路算法
        # 生成24个候选方向（更细粒度）
        best_pos = None
        best_score = float('inf')
        main_angle = math.atan2(dy, dx)
        
        for i in range(24):
            angle = main_angle + (i - 12) * math.pi / 12  # 每15度一个方向
            dir_x = math.cos(angle)
            dir_y = math.sin(angle)
            
            # 尝试不同步长
            for step_mult in [1.0, 0.8, 0.6, 0.4, 0.2]:
                try_x = unit.x + dir_x * speed * step_mult
                try_y = unit.y + dir_y * speed * step_mult
                
                # 边界检查
                try_x = max(2, min(state.width - 3, try_x))
                try_y = max(2, min(state.height - 3, try_y))
                
                # 检查是否可移动（工程师特殊规则）
                if not self._is_position_blocked(room_id, try_x, try_y, unit.id, "engineer"):
                    new_dist = self._distance(try_x, try_y, target_x, target_y)
                    old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                    
                    # 评分：优先选择能更接近目标的位置
                    angle_penalty = abs(angle - main_angle) * 0.05
                    score = new_dist + angle_penalty
                    
                    if new_dist < old_dist or (new_dist <= old_dist + speed * 0.8):
                        if score < best_score:
                            best_score = score
                            best_pos = (try_x, try_y)
        
        # 如果找到了更好的位置，移动过去
        if best_pos:
            unit.x = best_pos[0]
            unit.y = best_pos[1]
        else:
            # 如果完全卡住，尝试更激进的绕路：检查周围更大范围
            for radius in [1.0, 1.5, 2.0, 2.5]:
                for angle_offset in range(0, 360, 30):  # 每30度尝试一次
                    angle_rad = math.radians(angle_offset)
                    try_x = unit.x + math.cos(angle_rad) * speed * radius
                    try_y = unit.y + math.sin(angle_rad) * speed * radius
                    
                    # 边界检查
                    try_x = max(2, min(state.width - 3, try_x))
                    try_y = max(2, min(state.height - 3, try_y))
                    
                    if not self._is_position_blocked(room_id, try_x, try_y, unit.id, "engineer"):
                        new_dist = self._distance(try_x, try_y, target_x, target_y)
                        old_dist = self._distance(unit.x, unit.y, target_x, target_y)
                        
                        # 只要能移动，即使稍微远离目标也可以（避免完全卡死）
                        if new_dist <= old_dist + speed * 1.5:
                            unit.x = try_x
                            unit.y = try_y
                            return

    def _find_nearest_enemy(self, room_id: int, unit: UnitState) -> Optional[UnitState]:
        """寻找最近的敌人"""
        state = self.room_states.get(room_id)
        if not state:
            return None

        nearest = None
        min_dist = float('inf')

        for target in state.units:
            if target.is_dead or target.team == unit.team:
                continue
            dist = self._distance(unit.x, unit.y, target.x, target.y)
            if dist < min_dist:
                min_dist = dist
                nearest = target

        return nearest

    def _find_nearest_enemy_of_type(self, room_id: int, unit: UnitState, target_type: str) -> Optional[UnitState]:
        """寻找指定类型的最近敌人"""
        state = self.room_states.get(room_id)
        if not state:
            return None

        nearest = None
        min_dist = float('inf')

        for target in state.units:
            if target.is_dead or target.team == unit.team or target.type != target_type:
                continue
            dist = self._distance(unit.x, unit.y, target.x, target.y)
            if dist < min_dist:
                min_dist = dist
                nearest = target

        return nearest

    def _find_nearest_mine_field(self, room_id: int, unit: UnitState) -> Optional[MineFieldState]:
        """寻找最近的有能量的矿场"""
        state = self.room_states.get(room_id)
        if not state:
            return None

        nearest = None
        min_dist = float('inf')

        for mine in state.mine_fields:
            if mine.energy <= 0:
                continue
            dist = self._distance(unit.x, unit.y, mine.x, mine.y)
            if dist < min_dist:
                min_dist = dist
                nearest = mine

        return nearest

    def _find_nearest_ally_tank(self, room_id: int, unit: UnitState) -> Optional[UnitState]:
        """寻找最近的友方坦克（优先重装坦克）"""
        state = self.room_states.get(room_id)
        if not state:
            return None

        # 优先寻找重装坦克
        nearest_heavy = None
        min_dist_heavy = float('inf')
        
        nearest_assault = None
        min_dist_assault = float('inf')

        for ally in state.units:
            if ally.is_dead or ally.team != unit.team or ally.id == unit.id:
                continue
            
            if ally.type == "heavy_tank":
                dist = self._distance(unit.x, unit.y, ally.x, ally.y)
                if dist < min_dist_heavy:
                    min_dist_heavy = dist
                    nearest_heavy = ally
            elif ally.type == "assault_tank":
                dist = self._distance(unit.x, unit.y, ally.x, ally.y)
                if dist < min_dist_assault:
                    min_dist_assault = dist
                    nearest_assault = ally

        # 优先返回重装坦克
        if nearest_heavy:
            return nearest_heavy
        return nearest_assault

    def _find_nearest_energy_drop(self, room_id: int, unit: UnitState) -> Optional[EnergyDrop]:
        """寻找最近的能量掉落"""
        state = self.room_states.get(room_id)
        if not state:
            return None

        nearest = None
        min_dist = float('inf')

        for drop in state.energy_drops:
            dist = self._distance(unit.x, unit.y, drop.x, drop.y)
            if dist < min_dist:
                min_dist = dist
                nearest = drop

        return nearest


game_manager = LiveWarGameManager()


