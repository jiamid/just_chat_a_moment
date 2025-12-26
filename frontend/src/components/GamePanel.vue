<template>
  <div class="game-panel-new">
    <!-- 顶部：红蓝方血量（像素风格） -->
    <div class="game-top-bar">
      <!-- 两行合并：RED VS BLUE占据两行高度，文字一行显示 -->
      <div class="top-bar-double-row">
        <div class="top-bar-left-column">
          <div class="team-hp red-team">
            <div class="hp-bar-container">
              <div class="hp-bar-bg pixel-border">
                <div
                  class="hp-bar-fill red pixel-fill"
                  :style="{ width: (redBaseHpPercent * 100) + '%' }"
                >
                  <span class="hp-value-inside pixel-text">{{ redBaseHp }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="team-units red-team">
            <div class="units-by-type">
              <div class="unit-type-item" v-for="(cfg, key) in unitTypesConfig" :key="key">
                <UnitIcon
                  :unitType="key"
                  team="red"
                  :size="16"
                  class="unit-type-icon"
                />
                <span class="unit-type-count pixel-text">{{ getRedTeamUnitCountByType(key) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="vs-divider-double pixel-text">
          <span class="red-text">RED</span> VS <span class="blue-text">BLUE</span>
        </div>
        <div class="top-bar-right-column">
          <div class="team-hp blue-team">
            <div class="hp-bar-container">
              <div class="hp-bar-bg pixel-border">
                <div
                  class="hp-bar-fill blue pixel-fill"
                  :style="{ width: (blueBaseHpPercent * 100) + '%' }"
                >
                  <span class="hp-value-inside pixel-text">{{ blueBaseHp }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="team-units blue-team">
            <div class="units-by-type">
              <div class="unit-type-item" v-for="(cfg, key) in unitTypesConfig" :key="key">
                <UnitIcon
                  :unitType="key"
                  team="blue"
                  :size="16"
                  class="unit-type-icon"
                />
                <span class="unit-type-count pixel-text">{{ getBlueTeamUnitCountByType(key) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 第三行：玩家列表和游戏规则按钮 -->
      <div class="top-bar-row">
        <div class="button-group">
          <button
            class="icon-toggle-btn player-list-toggle"
            :class="{ 'active': showPlayerList }"
            @click="showPlayerList = !showPlayerList; showGameRules = false"
            title="玩家列表"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </button>
          <button
            class="icon-toggle-btn game-rules-toggle"
            :class="{ 'active': showGameRules }"
            @click="showGameRules = !showGameRules; showPlayerList = false"
            title="游戏规则"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 中间：游戏画布 -->
    <div class="game-canvas-container">
      <LiveWarCanvas v-if="gameState && !showPlayerList && !showGameRules" :gameState="gameState" />

      <!-- 玩家列表展开区域（覆盖在画布上方） -->
      <div v-if="showPlayerList" class="player-list-container pixel-style">
        <div class="player-list-columns">
          <div class="player-list-column red-team">
            <div class="player-list-header pixel-text">Red Team</div>
            <div
              v-for="player in redTeamPlayers"
              :key="player.userId || player.id"
              class="player-list-item pixel-text"
            >
              {{ player.name || player.username }}
            </div>
            <div v-if="redTeamPlayers.length === 0" class="player-list-empty pixel-text">
              No players
            </div>
          </div>
          <div class="player-list-column blue-team">
            <div class="player-list-header pixel-text">Blue Team</div>
            <div
              v-for="player in blueTeamPlayers"
              :key="player.userId || player.id"
              class="player-list-item pixel-text"
            >
              {{ player.name || player.username }}
            </div>
            <div v-if="blueTeamPlayers.length === 0" class="player-list-empty pixel-text">
              No players
            </div>
          </div>
        </div>
      </div>

      <!-- 游戏规则展开区域（覆盖在画布上方） -->
      <div v-if="showGameRules" class="game-rules-container pixel-style">
        <div class="game-rules-content">
          <div class="unit-rules-list">
            <div class="unit-rule-item">
              <div class="unit-rule-header pixel-text">
                <span class="unit-icon">{{ unitTypesConfig.miner.icon }}</span>
                <span class="unit-name">{{ unitTypesConfig.miner.name }}</span>
                <span class="unit-cost">成本: {{ unitTypesConfig.miner.cost }}</span>
              </div>
              <div class="unit-rule-details pixel-text">
                <div>生命值: 60 | 攻击力: 6 | 速度: 1.0 | 攻击范围: 1.5</div>
                <div class="unit-description">基础单位，擅长采集资源，适合前期发展</div>
              </div>
            </div>
            <div class="unit-rule-item">
              <div class="unit-rule-header pixel-text">
                <span class="unit-icon">{{ unitTypesConfig.engineer.icon }}</span>
                <span class="unit-name">{{ unitTypesConfig.engineer.name }}</span>
                <span class="unit-cost">成本: {{ unitTypesConfig.engineer.cost }}</span>
              </div>
              <div class="unit-rule-details pixel-text">
                <div>生命值: 90 | 攻击力: 12 | 速度: 4.0 | 攻击范围: 1.5</div>
                <div class="unit-description">高速移动单位，快速到达战场，机动性强</div>
              </div>
            </div>
            <div class="unit-rule-item">
              <div class="unit-rule-header pixel-text">
                <span class="unit-icon">{{ unitTypesConfig.heavy_tank.icon }}</span>
                <span class="unit-name">{{ unitTypesConfig.heavy_tank.name }}</span>
                <span class="unit-cost">成本: {{ unitTypesConfig.heavy_tank.cost }}</span>
              </div>
              <div class="unit-rule-details pixel-text">
                <div>生命值: 220 | 攻击力: 28 | 速度: 0.5 | 攻击范围: 2.5</div>
                <div class="unit-description">重型防御单位，高生命值，适合作为前线肉盾</div>
              </div>
            </div>
            <div class="unit-rule-item">
              <div class="unit-rule-header pixel-text">
                <span class="unit-icon">{{ unitTypesConfig.assault_tank.icon }}</span>
                <span class="unit-name">{{ unitTypesConfig.assault_tank.name }}</span>
                <span class="unit-cost">成本: {{ unitTypesConfig.assault_tank.cost }}</span>
              </div>
              <div class="unit-rule-details pixel-text">
                <div>生命值: 120 | 攻击力: 32 | 速度: 1.2 | 攻击范围: 2.5</div>
                <div class="unit-description">高攻击力单位，优先攻击坦克和工程师，适合快速消灭敌人</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 游戏结束展示（覆盖在画布上方） -->
      <div v-if="gameOverInfo" class="game-over-overlay pixel-style">
        <div class="game-over-content">
          <div class="game-over-title pixel-text" :class="gameOverInfo.winner">{{ gameOverInfo.winnerName }} WIN</div>
          <div class="game-over-players">
            <div
              v-for="(player, index) in gameOverInfo.winnerPlayers"
              :key="index"
              class="game-over-player pixel-text"
            >
              - {{ player }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 游戏控制按钮 -->
    <div class="game-controls">
      <!-- 已加入队伍且游戏已开始：显示能量栏和单位生成 -->
      <template v-if="inGame && !isGameSpectator && currentPlayer && isGameStarted">
        <div class="player-stats-row">
          <div class="energy-display">
            <span class="energy-value">{{ currentPlayer.energy || 0 }}</span>
          </div>
          <div class="unit-counts">
            <div class="unit-count-item" v-for="(cfg, key) in unitTypesConfig" :key="key">
              <UnitIcon
                :unitType="key"
                :team="currentPlayer.team"
                :size="20"
                class="unit-count-icon"
              />
              <span class="unit-count-value">{{ getUnitCount(key) }}</span>
            </div>
          </div>
        </div>
        <!-- 四个兵种按钮 -->
        <div class="unit-spawn-buttons">
          <button
            v-for="(cfg, key) in unitTypesConfig"
            :key="key"
            class="unit-spawn-btn"
            :class="{
              disabled: (currentPlayer.energy || 0) < cfg.cost,
              'red-team': currentPlayer && currentPlayer.team === 'red',
              'blue-team': currentPlayer && currentPlayer.team === 'blue'
            }"
            @click="$emit('select-and-spawn-unit', key)"
            :disabled="(currentPlayer.energy || 0) < cfg.cost"
          >
            <UnitIcon
              :unitType="key"
              :team="currentPlayer.team"
              :size="32"
              class="unit-spawn-icon"
            />
            <div class="unit-spawn-info">
              <div class="unit-spawn-name">{{ cfg.name }}</div>
              <div class="unit-spawn-cost">{{ cfg.cost }}⚡</div>
            </div>
          </button>
        </div>
      </template>
      <!-- 已加入队伍但游戏未开始：显示退出按钮 -->
      <div v-else-if="inGame && !isGameSpectator && currentPlayer" class="exit-button-container">
        <button
          class="game-exit-btn pixel-text"
          :class="{
            'red-team': currentPlayer && currentPlayer.team === 'red',
            'blue-team': currentPlayer && currentPlayer.team === 'blue'
          }"
          :disabled="!isConnected"
          @click="$emit('leave-game')"
        >
          退出队伍
        </button>
      </div>
      <!-- 未加入队伍：显示加入按钮 -->
      <div v-else-if="!inGame" class="join-buttons-container">
        <button
          class="join-team-btn pixel-text join-red-btn"
          :disabled="!isConnected"
          @click="$emit('join-game', 'red')"
        >
          加入红方
        </button>
        <button
          class="join-team-btn pixel-text join-blue-btn"
          :disabled="!isConnected"
          @click="$emit('join-game', 'blue')"
        >
          加入蓝方
        </button>
      </div>
      <!-- 观战者：显示退出游戏按钮 -->
      <div v-else-if="inGame" class="exit-button-container">
        <button
          class="game-exit-btn spectator-exit pixel-text"
          :disabled="!isConnected"
          @click="$emit('leave-game')"
        >
          退出游戏
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import LiveWarCanvas from './LiveWarCanvas.vue'
import UnitIcon from './UnitIcon.vue'

export default {
  name: 'GamePanel',
  components: {
    LiveWarCanvas,
    UnitIcon
  },
  props: {
    gameState: {
      type: Object,
      default: null
    },
    gameOverInfo: {
      type: Object,
      default: null
    },
    isConnected: {
      type: Boolean,
      default: false
    },
    unitTypesConfig: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
      showPlayerList: false,
      showGameRules: false
    }
  },
  computed: {
    isGameSpectator () {
      if (!this.gameState || !this.gameState.player) return true
      return !this.gameState.player.team
    },
    currentPlayer () {
      return this.gameState && this.gameState.player ? this.gameState.player : null
    },
    isGameStarted () {
      return this.gameState && this.gameState.game_started === true
    },
    inGame () {
      return !!(this.gameState && this.gameState.player && this.gameState.player.team)
    },
    redBaseHp () {
      return this.gameState && this.gameState.room && this.gameState.room.redBase ? this.gameState.room.redBase.hp : 0
    },
    redBaseHpMax () {
      return this.gameState && this.gameState.room && this.gameState.room.redBase ? this.gameState.room.redBase.hpMax : 1000
    },
    redBaseHpPercent () {
      return this.redBaseHpMax > 0 ? this.redBaseHp / this.redBaseHpMax : 0
    },
    blueBaseHp () {
      return this.gameState && this.gameState.room && this.gameState.room.blueBase ? this.gameState.room.blueBase.hp : 0
    },
    blueBaseHpMax () {
      return this.gameState && this.gameState.room && this.gameState.room.blueBase ? this.gameState.room.blueBase.hpMax : 1000
    },
    blueBaseHpPercent () {
      return this.blueBaseHpMax > 0 ? this.blueBaseHp / this.blueBaseHpMax : 0
    },
    redTeamPlayers () {
      if (!this.gameState) return []
      const players = this.gameState.players || []
      const teams = (this.gameState.room && this.gameState.room.teams) || {}

      return players.filter(p => {
        const playerId = p.userId || p.id
        const playerTeam = p.team || teams[playerId]
        return playerTeam === 'red'
      })
    },
    blueTeamPlayers () {
      if (!this.gameState) return []
      const players = this.gameState.players || []
      const teams = (this.gameState.room && this.gameState.room.teams) || {}

      return players.filter(p => {
        const playerId = p.userId || p.id
        const playerTeam = p.team || teams[playerId]
        return playerTeam === 'blue'
      })
    }
  },
  methods: {
    getRedTeamUnitCountByType (unitType) {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u =>
        !u.isDead && u.team === 'red' && u.type === unitType
      ).length
    },
    getBlueTeamUnitCountByType (unitType) {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u =>
        !u.isDead && u.team === 'blue' && u.type === unitType
      ).length
    },
    getUnitCount (unitType) {
      if (!this.gameState || !this.gameState.room || !this.currentPlayer || !this.currentPlayer.team) return 0
      const currentUserId = String(this.currentPlayer.id || '')
      if (!currentUserId) {
        return 0
      }

      const allUnits = this.gameState.room.units || []
      const myUnits = allUnits.filter(u => {
        if (u.isDead || u.team !== this.currentPlayer.team || u.type !== unitType) {
          return false
        }
        const unitOwnerId = String(u.ownerId || u.owner_id || '')
        return unitOwnerId === currentUserId
      })

      return myUnits.length
    }
  }
}
</script>

<style scoped>
/* LiveWar 游戏面板 - 新布局 */
.game-panel-new {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 0; /* 游戏面板在气泡容器内，不需要额外圆角 */
  overflow: hidden;
}

/* 顶部：红蓝方血量（像素风格） */
.game-top-bar {
  display: flex;
  flex-direction: column;
  gap: clamp(0.5rem, 1.5vw, 0.75rem); /* 响应式间距 */
  padding: clamp(0.75rem, 2vw, 1rem) clamp(1rem, 3vw, 1.5rem); /* 响应式内边距 */
  background: transparent;
  border-bottom: 2px solid #000000;
  position: relative; /* 为悬浮的玩家列表提供定位上下文 */
  flex-shrink: 0; /* 防止被压缩 */
  min-height: fit-content; /* 确保高度根据内容自适应，但不受绝对定位子元素影响 */
  width: 100%; /* 确保占满容器宽度 */
  box-sizing: border-box; /* 包含padding和border */
}

.top-bar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  position: relative; /* 为 player-list-container 提供定位上下文 */
}

.top-bar-double-row {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 1rem;
  min-height: 80px; /* 确保有两行的高度 */
  width: 100%; /* 确保占满容器宽度 */
  box-sizing: border-box; /* 包含padding和border */
}

.top-bar-left-column,
.top-bar-right-column {
  flex: 1 1 0; /* 允许收缩，但保持相等宽度 */
  min-width: 0; /* 允许在flex容器中收缩 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.5rem;
  box-sizing: border-box; /* 包含padding和border */
}

.vs-divider-double {
  font-size: clamp(0.8rem, 2vw, 1.2rem); /* 响应式字体大小，最小0.8rem，最大1.2rem */
  font-weight: 600;
  color: #000000; /* 默认文字颜色为黑色 */
  margin: 0 clamp(0.5rem, 1.5vw, 1rem); /* 响应式间距 */
  text-shadow: none;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.vs-divider-double .red-text {
  color: #ef4444;
}

.vs-divider-double .blue-text {
  color: #3b82f6;
  align-items: center;
  justify-content: center;
  writing-mode: horizontal-tb;
  letter-spacing: clamp(1px, 0.3vw, 3px); /* 响应式字母间距 */
  text-transform: uppercase; /* 确保大写 */
  position: relative;
  flex-shrink: 0; /* 防止收缩 */
  min-width: fit-content; /* 确保宽度自适应内容 */
}

.team-hp {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.red-team {
  align-items: flex-start;
}

.blue-team {
  align-items: flex-end;
}

.team-label {
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
}

.pixel-text {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.8);
}

.red-team .team-label {
  color: #ef4444;
}

.blue-team .team-label {
  color: #3b82f6;
}

.hp-bar-container {
  display: flex;
  align-items: center;
  width: 100%;
}

.hp-bar-bg {
  flex: 1;
  height: 32px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.75) 100%);
  overflow: hidden;
  border: none;
  position: relative;
  box-sizing: border-box;
  padding: 2px;
  /* 3D凸起效果 - 外边框 */
  box-shadow:
    0 4px 0px rgba(0, 0, 0, 0.4),
    0 2px 0px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(255, 255, 255, 0.1),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
  border-radius: 4px;
}

.pixel-border {
  border-radius: 4px;
}

.hp-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  min-width: 60px; /* 确保有足够空间显示文字 */
  box-sizing: border-box;
  max-width: 100%;
  border-radius: 2px;
}

.pixel-fill {
  border-radius: 2px;
}

.hp-bar-fill.red {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #c0392b 100%);
  box-shadow:
    inset 0 3px 6px rgba(255, 255, 255, 0.4),
    inset 0 -3px 6px rgba(0, 0, 0, 0.4),
    0 2px 4px rgba(239, 68, 68, 0.5);
  justify-content: flex-start;
  padding-left: 8px;
}

.hp-bar-fill.blue {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1e40af 100%);
  box-shadow:
    inset 0 3px 6px rgba(255, 255, 255, 0.4),
    inset 0 -3px 6px rgba(0, 0, 0, 0.4),
    0 2px 4px rgba(59, 130, 246, 0.5);
  justify-content: flex-end;
  padding-right: 8px;
}

.hp-value-inside {
  font-size: 1rem;
  font-weight: 900;
  color: #fff;
  text-shadow:
    2px 2px 0px rgba(0, 0, 0, 0.9),
    4px 4px 0px rgba(0, 0, 0, 0.7),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  white-space: nowrap;
  z-index: 10;
  position: relative;
  letter-spacing: 0.05em;
}

.vs-divider {
  font-size: 1rem;
  font-weight: 700;
  color: #fbbf24;
  margin: 0 1rem;
  text-shadow:
    2px 2px 0 rgba(0, 0, 0, 0.8),
    0 0 10px rgba(251, 191, 36, 0.5);
  white-space: nowrap;
}

/* 兵种数量显示 */
.team-units {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.units-by-type {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: clamp(0.3rem, 1vw, 0.5rem); /* 响应式间距 */
  flex-wrap: wrap; /* 允许换行，一行2个 */
  width: 100%; /* 确保占满容器宽度 */
  box-sizing: border-box; /* 包含padding和border */
}

.unit-type-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
  flex: 1 1 auto; /* 允许伸缩，空间足够时在一行 */
  min-width: calc(50% - clamp(0.3rem, 1vw, 0.5rem) / 2); /* 最小宽度为50%减去gap的一半，强制换行时每行2个 */
  max-width: 100%; /* 最大宽度不超过容器 */
  box-sizing: border-box;
}

.unit-type-icon {
  opacity: 0.9;
}

.unit-type-count {
  font-size: 0.9rem;
  font-weight: 700;
  min-width: 1.2rem;
  text-align: center;
}

.red-team .unit-type-count {
  color: #ef4444;
}

.blue-team .unit-type-count {
  color: #3b82f6;
}

/* 按钮组 */
.button-group {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: flex-start;
}

/* 圆形图标按钮 */
.icon-toggle-btn {
  position: relative;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: none;
  color: #2C3E50;
  cursor: pointer;
  transition: all 0.1s ease-out;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  /* 3D凸起效果 */
  box-shadow:
    0 4px 0px rgba(0, 0, 0, 0.2),
    0 2px 0px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.1);
}

.icon-toggle-btn:hover,
.icon-toggle-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.2),
    inset 0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.icon-toggle-btn.active {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: #fff;
  box-shadow:
    0 4px 0px rgba(25, 113, 194, 0.4),
    0 2px 0px rgba(25, 113, 194, 0.5),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.2);
}

.icon-toggle-btn.active:hover,
.icon-toggle-btn.active:active {
  transform: translateY(2px);
  box-shadow:
    0 2px 0px rgba(25, 113, 194, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.icon-toggle-btn svg {
  width: 20px;
  height: 20px;
  stroke: currentColor;
}

/* 玩家列表展开区域（覆盖在画布上方） */
.player-list-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border: none;
  padding: 2rem;
  box-sizing: border-box;
  z-index: 100; /* 覆盖在画布上方 */
  box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 美化滚动条 - Webkit (Chrome, Safari, Edge) */
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent; /* Firefox */
}

/* Webkit 滚动条样式 */
.player-list-container::-webkit-scrollbar {
  width: 8px;
}

.player-list-container::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.player-list-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  transition: background 0.2s ease;
}

.player-list-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.player-list-columns {
  display: flex;
  gap: 2rem;
  align-items: stretch;
  max-width: 800px;
  width: 100%;
}

.player-list-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0; /* 确保flex子元素可以正确收缩 */
}

.player-list-header {
  font-size: 0.9rem;
  font-weight: 700;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #000000;
  margin-bottom: 0.5rem;
  text-align: center;
  width: 100%;
}

.red-team .player-list-header {
  color: #ef4444;
}

.blue-team .player-list-header {
  color: #3b82f6;
}

.player-list-item {
  font-size: 0.9rem;
  color: #2C3E50;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  width: 100%;
  box-sizing: border-box;
  word-wrap: break-word;
  overflow-wrap: break-word;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.player-list-empty {
  font-size: 0.85rem;
  color: rgba(44, 62, 80, 0.5);
  font-style: italic;
  padding: 0.5rem;
  text-align: center;
}

/* 游戏规则展开区域（覆盖在画布上方） */
.game-rules-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(10px);
  border: none;
  padding: 2rem;
  box-sizing: border-box;
  z-index: 100; /* 覆盖在画布上方 */
  box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 美化滚动条 - Webkit (Chrome, Safari, Edge) */
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent; /* Firefox */
}

/* Webkit 滚动条样式 */
.game-rules-container::-webkit-scrollbar {
  width: 8px;
}

.game-rules-container::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.game-rules-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  transition: background 0.2s ease;
}

.game-rules-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.game-rules-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 800px;
  width: 100%;
}

.game-rules-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  text-align: center;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #000000;
}

.unit-rules-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.unit-rule-item {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  padding: 1rem;
  border-radius: 8px;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.2),
    inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

.unit-rule-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8);
}

.unit-icon {
  font-size: 1.2rem;
}

.unit-name {
  flex: 1;
  font-size: 1rem;
}

.unit-cost {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.unit-rule-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
}

.unit-description {
  margin-top: 0.25rem;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
}

/* 游戏结束展示 */
.game-over-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.game-over-content {
  text-align: center;
  padding: 2rem;
  background: rgba(0, 0, 0, 0.8);
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 0;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 300px;
}

.game-over-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-shadow: 4px 4px 0 rgba(0, 0, 0, 0.8);
  text-align: center;
  width: 100%;
}

.game-over-title.red {
  color: #ef4444;
}

.game-over-title.blue {
  color: #3b82f6;
}

.game-over-players {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  margin-top: 1.5rem;
  width: 100%;
}

.game-over-player {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  width: 100%;
  box-sizing: border-box;
}

/* 中间：游戏画布 */
.game-canvas-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  overflow: hidden;
  padding: 1rem;
  /* 确保画布容器保持宽高比 */
  position: relative;
}

.game-canvas-container canvas {
  /* 确保画布在容器中保持比例，不拉伸 */
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}

/* 底部：玩家控制面板 */
.game-bottom-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  min-height: fit-content;
}

/* 游戏未开始时的退出按钮容器 */
.game-exit-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 2rem 0;
}

/* 退出按钮 - 3D效果 */
.game-exit-btn {
  position: relative;
  width: 100%;
  max-width: 400px;
  min-height: 60px;
  padding: 0.875rem 2.5rem;
  border: none;
  color: #FFFFFF;
  font-size: 1rem;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.1s ease-out;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  text-shadow:
    2px 2px 0px rgba(0, 0, 0, 0.8),
    4px 4px 0px rgba(0, 0, 0, 0.6),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  letter-spacing: 0.05em;
  overflow: visible;
}

/* 红方退出按钮 */
.game-exit-btn.red-team {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #ef4444 100%);
  /* 3D凸起效果 */
  box-shadow:
    0 6px 0px rgba(139, 69, 19, 0.8),
    0 4px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.game-exit-btn.red-team:hover:not(:disabled),
.game-exit-btn.red-team:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(139, 69, 19, 0.8),
    0 1px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

/* 蓝方退出按钮 */
.game-exit-btn.blue-team {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #3b82f6 100%);
  /* 3D凸起效果 */
  box-shadow:
    0 6px 0px rgba(25, 113, 194, 0.8),
    0 4px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.game-exit-btn.blue-team:hover:not(:disabled),
.game-exit-btn.blue-team:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(25, 113, 194, 0.8),
    0 1px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.game-exit-btn.spectator-exit {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 50%, #6b7280 100%);
  box-shadow:
    0 6px 0px rgba(31, 41, 55, 0.8),
    0 4px 0px rgba(31, 41, 55, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.2),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.game-exit-btn.spectator-exit:hover:not(:disabled),
.game-exit-btn.spectator-exit:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(31, 41, 55, 0.8),
    0 1px 0px rgba(31, 41, 55, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.1);
}

.game-exit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.player-stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.energy-display {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  padding-left: 2rem; /* 为背景图标留出空间 */
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.3) 0%, rgba(251, 191, 36, 0.2) 100%);
  border: none;
  border-radius: 8px;
  box-shadow:
    0 3px 0px rgba(184, 134, 11, 0.3),
    0 1px 0px rgba(184, 134, 11, 0.4),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.1);
}

.energy-display::before {
  content: '⚡';
  position: absolute;
  left: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.3rem;
  opacity: 0.6;
  pointer-events: none;
  z-index: 0;
  filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.3));
}

.energy-value {
  position: relative;
  z-index: 1;
  font-size: 1.2rem;
  font-weight: 900;
  color: #fbbf24;
  text-shadow:
    2px 2px 0px rgba(184, 134, 11, 0.8),
    4px 4px 0px rgba(184, 134, 11, 0.6),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  letter-spacing: 0.05em;
}

.unit-counts {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.unit-count-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: none;
  border-radius: 8px;
  box-shadow:
    0 3px 0px rgba(0, 0, 0, 0.15),
    0 1px 0px rgba(0, 0, 0, 0.2),
    inset 0 2px 4px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.1);
}

.unit-count-icon {
  opacity: 0.9;
  filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.2));
}

.unit-count-value {
  font-size: 1rem;
  font-weight: 900;
  color: #2C3E50;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

/* 四个兵种按钮 */
.unit-spawn-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.unit-spawn-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.1s ease-out;
  /* 3D凸起效果 */
  box-shadow:
    0 4px 0px rgba(0, 0, 0, 0.2),
    0 2px 0px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.1);
}

.unit-spawn-btn:hover:not(.disabled),
.unit-spawn-btn:active:not(.disabled) {
  transform: translateY(2px);
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.2),
    inset 0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.unit-spawn-btn.red-team:hover:not(.disabled),
.unit-spawn-btn.red-team:active:not(.disabled) {
  box-shadow:
    0 2px 0px rgba(231, 76, 60, 0.5),
    inset 0 2px 4px rgba(231, 76, 60, 0.2),
    inset 0 -2px 4px rgba(231, 76, 60, 0.1);
}

.unit-spawn-btn.blue-team:hover:not(.disabled),
.unit-spawn-btn.blue-team:active:not(.disabled) {
  box-shadow:
    0 2px 0px rgba(59, 130, 246, 0.5),
    inset 0 2px 4px rgba(59, 130, 246, 0.2),
    inset 0 -2px 4px rgba(59, 130, 246, 0.1);
}

.unit-spawn-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.15),
    inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.unit-spawn-icon {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.unit-spawn-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.unit-spawn-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #2C3E50;
  text-shadow: 0.5px 0.5px 1px rgba(0, 0, 0, 0.1);
}

.unit-spawn-cost {
  font-size: 0.75rem;
  color: #fbbf24;
  font-weight: 700;
  text-shadow:
    1px 1px 0px rgba(0, 0, 0, 0.5),
    2px 2px 0px rgba(0, 0, 0, 0.3);
}

/* 观战者控制按钮 */
.game-controls {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: #ffffff;
  border-top: 1px solid #000000;
  min-height: fit-content;
}

.join-buttons-container {
  display: flex;
  width: 100%;
  gap: 0.5rem;
  align-items: center;
}

.exit-button-container {
  display: flex;
  width: 100%;
  justify-content: center;
  align-items: center;
}

.join-team-btn {
  position: relative;
  flex: 1;
  padding: 0.875rem 2rem;
  font-size: 1rem;
  font-weight: 900;
  border: none;
  cursor: pointer;
  transition: all 0.1s ease-out;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 8px;
  box-sizing: border-box;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  text-shadow:
    2px 2px 0px rgba(0, 0, 0, 0.8),
    4px 4px 0px rgba(0, 0, 0, 0.6),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  overflow: visible;
}

.join-red-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #ef4444 100%);
  /* 3D凸起效果 */
  box-shadow:
    0 6px 0px rgba(139, 69, 19, 0.8),
    0 4px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.join-red-btn:not(:disabled):hover,
.join-red-btn:not(:disabled):active {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(139, 69, 19, 0.8),
    0 1px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.join-blue-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #3b82f6 100%);
  /* 3D凸起效果 */
  box-shadow:
    0 6px 0px rgba(25, 113, 194, 0.8),
    0 4px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.join-blue-btn:not(:disabled):hover,
.join-blue-btn:not(:disabled):active {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(25, 113, 194, 0.8),
    0 1px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.join-team-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  /* 移动端 VS 部分自适应 */
  .vs-divider-double {
    font-size: 0.9rem; /* 移动端字体稍小 */
    margin: 0 0.5rem; /* 移动端间距减小 */
    letter-spacing: 2px; /* 移动端字母间距减小 */
    flex-shrink: 0; /* 防止收缩 */
    min-width: fit-content; /* 确保宽度自适应内容 */
  }

  .top-bar-double-row {
    gap: 0.5rem; /* 移动端间距减小 */
  }

  .top-bar-left-column,
  .top-bar-right-column {
    min-width: 0; /* 允许在移动端收缩 */
    flex: 1 1 0; /* 允许收缩，但保持相等宽度 */
  }

  /* 移动端兵种显示换行 */
  .units-by-type {
    flex-wrap: wrap; /* 允许换行 */
    justify-content: center; /* 居中对齐 */
    gap: 0.3rem; /* 移动端间距减小 */
  }

  .unit-type-item {
    flex: 0 0 auto; /* 不自动伸缩，保持内容宽度 */
    min-width: fit-content; /* 确保宽度自适应内容 */
  }

  /* 确保移动端用户区域正确显示 */

  /* 移动端键盘弹起时调整输入框样式 */

  /* 确保移动端消息容器正确滚动 */

  /* 移动端：当有画图面板时，消息容器需要固定高度 */

  /* 移动端：调整能量条宽度，确保单位数量能摆下 */
  .player-stats-row {
    gap: 0.5rem; /* 减小间距 */
  }

  .energy-display {
    flex-shrink: 1; /* 允许收缩 */
    padding: 0.5rem 0.75rem;
    padding-left: 1.2rem; /* 为背景图标留出空间 */
    min-width: 0; /* 允许收缩到最小 */
  }

  .energy-display::before {
    content: '⚡';
    position: absolute;
    left: 0.4rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1rem; /* 移动端图标稍小 */
    opacity: 0.3;
    pointer-events: none;
    z-index: 0;
  }

  .energy-value {
    font-size: 0.95rem; /* 移动端字体稍小 */
  }

  .unit-counts {
    gap: 0.5rem; /* 减小单位数量之间的间距 */
    flex-shrink: 0; /* 不允许收缩 */
  }
}
</style>
