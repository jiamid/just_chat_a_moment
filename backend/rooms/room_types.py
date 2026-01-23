from enum import Enum


class RoomType(str, Enum):
    """房间类型枚举"""
    CHAT = "chat"  # 纯聊天房间
    DRAWING = "drawing"  # 你画我猜房间
    LIVE_WAR = "live_war"  # LiveWar游戏房间
