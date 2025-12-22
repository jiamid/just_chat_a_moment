<template>
  <div class="chat-container">
    <!-- 星空背景 -->
    <StarBackground />
    <!-- 移动端遮罩层 -->
    <div
      v-if="isMobile && showMobileNavbar"
      class="mobile-overlay"
      @click="hideMobileNavbar"
    ></div>

    <!-- 左侧导航栏 -->
    <div class="left-sidebar" :class="{
      'mobile-show': showMobileNavbar && isMobile,
      'collapsed': sidebarCollapsed && !isMobile
    }">
      <!-- 折叠/展开按钮（仅在桌面端显示） -->
      <button
        v-if="!isMobile"
        class="sidebar-toggle-btn"
        @click="toggleSidebar"
        :title="sidebarCollapsed ? '展开菜单' : '折叠菜单'"
      >
        <svg v-if="sidebarCollapsed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>

      <!-- 折叠状态下的标签（已移除文字，只显示按钮） -->

      <!-- 完整内容（折叠时隐藏） -->
      <div v-show="!sidebarCollapsed || isMobile" class="sidebar-content">
        <!-- Logo -->
        <div class="logo-section" @click="goToHome">
          <h1 class="logo-text">JustChatAMoment</h1>
        </div>

        <!-- 房间列表 -->
        <div class="rooms-section">
          <h3>最近房间</h3>
          <div class="room-list">
            <div
              v-for="room in recentRooms"
              :key="room.id"
              :class="['room-item', { active: room.id === roomId }]"
              @click="switchRoom(room.id)"
            >
              <span class="room-name">房间 {{ room.id }}</span>
            </div>
          </div>

          <!-- 房间跳转 -->
          <div class="room-jump">
            <h4>跳转房间</h4>
            <div class="jump-input-group">
              <input
                v-model="jumpRoomId"
                type="text"
                placeholder="房间号"
                class="jump-input"
                @keyup.enter="jumpToRoom"
                @input="filterNumbers"
              />
              <button @click="jumpToRoom" class="jump-btn">GO</button>
            </div>
          </div>
        </div>

        <!-- 用户信息和退出 -->
        <div class="user-section">
          <div class="user-info">
            <span class="username">{{ username }}</span>
            <!-- 连接状态 -->
            <div class="connection-status-navbar">
              <span v-if="isConnected" class="status-indicator connected"></span>
              <span v-if="isConnected" class="status-text">已连接</span>
              <span v-else-if="roomId && !hasEverConnected" class="status-text connecting">连接中...</span>
              <button v-else-if="roomId && hasEverConnected" @click="reconnect" class="reconnect-btn">重连</button>
            </div>
          </div>
          <button @click="logout" class="logout-btn">退出登录</button>
        </div>
      </div>
    </div>

    <!-- 中间游戏区域（仅在游戏面板打开时显示，桌面端，且不在画画模式） -->
    <div v-if="showGamePanel && roomId && !isMobile && !showDrawingPanel" class="game-area">
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
                class="player-list-toggle pixel-text"
                @click="showPlayerList = !showPlayerList; showGameRules = false"
              >
                {{ showPlayerList ? '▼' : '▶' }} 玩家
              </button>
              <button
                class="game-rules-toggle pixel-text"
                @click="showGameRules = !showGameRules; showPlayerList = false"
              >
                {{ showGameRules ? '▼' : '▶' }} 游戏规则
              </button>
            </div>
            <!-- 玩家列表展开区域 -->
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
            <!-- 游戏规则展开区域 -->
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
          </div>
        </div>

        <!-- 中间：游戏画布 -->
        <div class="game-canvas-container">
          <LiveWarCanvas v-if="gameState" :gameState="gameState" />

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
                @click="selectAndSpawnUnit(key)"
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
              @click="leaveGame"
            >
              退出队伍
            </button>
          </div>
          <!-- 未加入队伍：显示加入按钮 -->
          <div v-else-if="!inGame" class="join-buttons-container">
            <button
              class="join-team-btn pixel-text join-red-btn"
              :disabled="!isConnected"
              @click="joinGame('red')"
            >
              加入红方
            </button>
            <button
              class="join-team-btn pixel-text join-blue-btn"
              :disabled="!isConnected"
              @click="joinGame('blue')"
            >
              加入蓝方
            </button>
          </div>
          <!-- 观战者：显示退出游戏按钮 -->
          <button
            v-else-if="inGame"
            class="drawing-btn stop-btn pixel-text"
            :disabled="!isConnected"
            @click="leaveGame"
          >
            退出游戏
          </button>
        </div>
      </div>
    </div>

    <!-- 中间画布区域（仅在画图面板打开时显示，桌面端，且不在游戏模式） -->
    <div v-if="showDrawingPanel && roomId && !isMobile && !showGamePanel" class="drawing-area">
      <div class="drawing-panel">
        <div class="drawing-header">
          <div class="drawing-status">
            <span v-if="currentDrawer" class="drawer-info">
              {{ currentDrawer === username ? '你正在画画' : `${currentDrawer} 正在画画` }}
              <span v-if="currentDrawer === username" class="drawer-timer">
                (剩余 {{ formatDrawerTime(drawerTimeRemaining) }})
              </span>
            </span>
            <span v-else class="drawer-info">暂无画画人</span>
          </div>
          <div class="drawing-controls">
            <button
              v-if="currentDrawer !== username"
              @click="requestDrawing"
              :disabled="!isConnected"
              class="drawing-btn request-btn"
            >
              申请画画
            </button>
            <button
              v-if="currentDrawer === username"
              @click="clearDrawing"
              :disabled="!isConnected"
              class="drawing-btn clear-btn"
            >
              清空画布
            </button>
            <button
              v-if="currentDrawer === username"
              @click="exitDrawing"
              :disabled="!isConnected"
              class="drawing-btn stop-btn"
            >
              退出画画
            </button>
          </div>
        </div>
        <div class="drawing-tools" v-if="currentDrawer === username">
          <div class="color-picker">
            <span>颜色：</span>
            <button
              v-for="color in ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']"
              :key="color"
              @click="changeDrawingColor(color)"
              class="color-btn"
              :class="{ 'active': drawingColor === color && !isEraser }"
              :style="{ backgroundColor: color }"
              :title="color"
            ></button>
            <button
              @click="toggleEraser"
              class="color-btn eraser-btn"
              :class="{ 'active': isEraser }"
              title="橡皮擦"
            >
              🧹
            </button>
          </div>
          <div class="line-width-picker">
            <span>粗细：</span>
            <button
              v-for="width in [1, 3, 5, 8, 12]"
              :key="width"
              @click="changeDrawingLineWidth(width)"
              class="width-btn"
              :class="{ 'active': drawingLineWidth === width }"
            >
              {{ width }}px
            </button>
          </div>
        </div>
        <div class="drawing-container" ref="drawingContainer">
          <div class="canvas-wrapper" v-if="!isMobile">
            <canvas
              ref="drawingCanvas"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
              @touchstart.prevent="startDrawing"
              @touchmove.prevent="draw"
              @touchend.prevent="stopDrawing"
              class="drawing-canvas"
            ></canvas>
          </div>
          <canvas
            v-else
            ref="drawingCanvas"
            @mousedown="startDrawing"
            @mousemove="draw"
            @mouseup="stopDrawing"
            @mouseleave="stopDrawing"
            @touchstart.prevent="startDrawing"
            @touchmove.prevent="draw"
            @touchend.prevent="stopDrawing"
            class="drawing-canvas"
          ></canvas>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="right-chat" :class="{
      'with-drawing': showDrawingPanel && roomId && !showGamePanel,
      'with-game': showGamePanel && roomId
    }">
      <!-- 顶部：房间信息 -->
      <div class="chat-header">
        <div class="header-left">
          <!-- 移动端菜单按钮 -->
          <button v-if="isMobile" @click="toggleMobileNavbar" class="menu-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <h2 v-if="roomId">房间 {{ roomId }}<span v-if="currentRoomCount > 0"> [{{ currentRoomCount }}]</span></h2>
          <h2 v-else>选择房间开始聊天</h2>
        </div>
        <div class="connection-status" v-if="roomId">
          <!-- 画图按钮 -->
          <button
            @click="toggleDrawingPanel"
            :disabled="!isConnected"
            class="drawing-icon-btn"
            :class="{ 'active': showDrawingPanel }"
            title="你画我猜"
          >
            <svg width="24" height="24" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg">
              <path d="M512 1024C229.888 1024 0 794.112 0 512S229.888 0 512 0s512 229.888 512 512c0 30.72-2.56 60.928-8.192 90.624-11.776 66.56-95.232 67.584-175.616 68.608-49.664 0.512-111.616 1.536-127.488 20.992-24.576 29.696-22.528 85.504-20.48 139.776 3.072 77.312 6.144 164.352-77.312 181.76-33.28 6.656-68.096 10.24-102.912 10.24z m0-970.24c-252.416 0-458.24 205.312-458.24 458.24s205.312 458.24 458.24 458.24c31.232 0 61.952-3.072 92.16-9.216 34.816-7.168 37.376-46.08 34.304-126.976-2.048-61.44-4.608-130.56 32.768-176.128 32.256-38.912 98.304-39.424 168.448-40.448 50.176-0.512 118.784-1.536 122.88-24.576 4.608-26.624 7.168-53.76 7.168-80.896 0.512-252.416-205.312-458.24-457.728-458.24z" fill="currentColor"></path>
              <path d="M462.336 319.488c-61.44 0-111.616-50.176-111.616-111.616s50.176-111.616 111.616-111.616 111.616 50.176 111.616 111.616-49.664 111.616-111.616 111.616z m0-169.472c-31.744 0-57.856 26.112-57.856 57.856s26.112 57.856 57.856 57.856c31.744 0 57.856-26.112 57.856-57.856s-25.6-57.856-57.856-57.856zM246.784 475.136c-54.784 0-99.84-44.544-99.84-99.84 0-54.784 44.544-99.84 99.84-99.84 54.784 0 99.84 44.544 99.84 99.84-0.512 54.784-45.056 99.84-99.84 99.84z m0-145.92c-25.088 0-45.568 20.48-45.568 45.568s20.48 45.568 45.568 45.568 45.568-20.48 45.568-45.568-20.48-45.568-45.568-45.568zM738.816 484.352c-68.608 0-123.904-55.808-123.904-123.904s55.808-123.904 123.904-123.904c68.096 0 123.904 55.808 123.904 123.904s-55.808 123.904-123.904 123.904z m0-194.048c-38.4 0-70.144 31.232-70.144 70.144 0 38.4 31.232 70.144 70.144 70.144S808.96 399.36 808.96 360.448c0-38.4-31.744-70.144-70.144-70.144zM270.848 693.248c-41.472 0-75.264-33.792-75.264-75.264S229.376 542.72 270.848 542.72s75.264 33.792 75.264 75.264-33.792 75.264-75.264 75.264z m0-97.28c-11.776 0-21.504 9.728-21.504 21.504s9.728 21.504 21.504 21.504c11.776 0 21.504-9.728 21.504-21.504s-9.728-21.504-21.504-21.504zM464.896 826.368c-34.816 0-63.488-28.672-63.488-63.488 0-34.816 28.16-63.488 63.488-63.488s63.488 28.16 63.488 63.488-28.672 63.488-63.488 63.488z m0-72.704c-5.12 0-9.216 4.096-9.216 9.216s4.096 9.216 9.216 9.216 9.216-4.096 9.216-9.216c0-4.608-4.096-9.216-9.216-9.216z" fill="currentColor"></path>
            </svg>
          </button>
          <!-- LiveWar 按钮 -->
          <button
            @click="toggleGamePanel"
            :disabled="!isConnected"
            class="drawing-icon-btn"
            :class="{ 'active': showGamePanel }"
            title="LiveWar 对战"
            style="margin-right: 0.5rem;"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <!-- 经典钻石形状：上面梯形，下面三角形 -->
              <path d="M12 2 L18 8 L12 14 L6 8 Z"/>
              <path d="M6 8 L12 14 L18 8 L12 20 Z"/>
            </svg>
          </button>
          <!-- 音乐选择按钮 -->
          <div class="music-container-header">
            <button
              ref="musicButton"
              @click="toggleMusicMenu"
              :disabled="!isConnected"
              class="music-icon-btn"
              :class="{ 'playing': isPlaying }"
              title="选择音乐"
            >
              <div class="music-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18V5l12-2v13" transform="translate(-1, 1)"></path>
                  <circle cx="6" cy="18" r="3" transform="translate(-1, 1)"></circle>
                  <circle cx="18" cy="16" r="3" transform="translate(-1, 1)"></circle>
                </svg>
              </div>
            </button>

            <!-- 音乐选择菜单 -->
            <div v-if="showMusicMenu" class="music-menu music-menu-header-position" :style="musicMenuStyle" @click.stop>
              <div class="music-menu-header">
                <span>选择音乐</span>
              </div>
              <div class="music-list">
                <div
                  v-for="(music, id) in musicConfig"
                  :key="id"
                  @click="sendMusic(id)"
                  class="music-item"
                >
                  <span class="music-name">🎵 {{ music.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：消息区域 -->
      <div class="chat-main" @click="hideMobileNavbar(); hideMusicMenu()">
        <!-- 未选择房间时的提示 -->
        <div v-if="!roomId" class="no-room-message">
          <div class="welcome-content">
            <h3>欢迎使用 Just Chat A Moment</h3>
            <p>请从左侧选择一个房间开始聊天，或者输入自定义房间号</p>
          </div>
        </div>

        <!-- 已选择房间时的内容 -->
        <template v-else>
          <!-- 移动端游戏面板（桌面端游戏面板在中间区域） -->
          <div v-if="showGamePanel && isMobile" class="game-panel-mobile">
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
                    class="player-list-toggle pixel-text"
                    @click="showPlayerList = !showPlayerList; showGameRules = false"
                  >
                    {{ showPlayerList ? '▼' : '▶' }} 玩家
                  </button>
                  <button
                    class="game-rules-toggle pixel-text"
                    @click="showGameRules = !showGameRules; showPlayerList = false"
                  >
                    {{ showGameRules ? '▼' : '▶' }} 游戏规则
                  </button>
                </div>
                <!-- 玩家列表展开区域 -->
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
                <!-- 游戏规则展开区域 -->
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
              </div>
            </div>

            <!-- 中间：游戏画布（移动端） -->
            <div class="game-canvas-container">
              <LiveWarCanvas v-if="gameState" :gameState="gameState" />

              <!-- 游戏结束展示（覆盖在画布上方，移动端也显示） -->
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
                    @click="selectAndSpawnUnit(key)"
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
                  @click="leaveGame"
                >
                  退出队伍
                </button>
              </div>
              <!-- 未加入队伍：显示加入按钮 -->
              <div v-else-if="!inGame" class="join-buttons-container">
                <button
                  class="join-team-btn pixel-text join-red-btn"
                  :disabled="!isConnected"
                  @click="joinGame('red')"
                >
                  加入红方
                </button>
                <button
                  class="join-team-btn pixel-text join-blue-btn"
                  :disabled="!isConnected"
                  @click="joinGame('blue')"
                >
                  加入蓝方
                </button>
              </div>
              <!-- 观战者：显示退出游戏按钮 -->
              <button
                v-else-if="inGame"
                class="drawing-btn stop-btn pixel-text"
                :disabled="!isConnected"
                @click="leaveGame"
              >
                退出游戏
              </button>
            </div>
          </div>

          <!-- 移动端：画布在聊天区域内显示（桌面端画布在中间区域） -->
          <div v-if="showDrawingPanel && isMobile" class="drawing-panel mobile-drawing-panel">
            <div class="drawing-header">
              <div class="drawing-status">
                <span v-if="currentDrawer" class="drawer-info">
                  {{ currentDrawer === username ? '你正在画画' : `${currentDrawer} 正在画画` }}
                  <span v-if="currentDrawer === username" class="drawer-timer">
                    (剩余 {{ formatTime(drawerTimeRemaining) }})
                  </span>
                </span>
                <span v-else class="drawer-info">暂无画画人</span>
              </div>
              <div class="drawing-controls">
                <button
                  v-if="currentDrawer !== username"
                  @click="requestDrawing"
                  :disabled="!isConnected"
                  class="drawing-btn request-btn"
                >
                  申请画画
                </button>
                <button
                  v-if="currentDrawer === username"
                  @click="clearDrawing"
                  :disabled="!isConnected"
                  class="drawing-btn clear-btn"
                >
                  清空画布
                </button>
                <button
                  v-if="currentDrawer === username"
                  @click="exitDrawing"
                  :disabled="!isConnected"
                  class="drawing-btn stop-btn"
                >
                  退出画画
                </button>
              </div>
            </div>
            <div class="drawing-tools" v-if="currentDrawer === username">
              <div class="color-picker">
                <span>颜色：</span>
                <button
                  v-for="color in ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']"
                  :key="color"
                  @click="changeDrawingColor(color)"
                  class="color-btn"
                  :class="{ 'active': drawingColor === color && !isEraser }"
                  :style="{ backgroundColor: color }"
                  :title="color"
                ></button>
                <button
                  @click="toggleEraser"
                  class="color-btn eraser-btn"
                  :class="{ 'active': isEraser }"
                  title="橡皮擦"
                >
                  🧹
                </button>
              </div>
              <div class="line-width-picker">
                <span>粗细：</span>
                <button
                  v-for="width in [1, 3, 5, 8, 12]"
                  :key="width"
                  @click="changeDrawingLineWidth(width)"
                  class="width-btn"
                  :class="{ 'active': drawingLineWidth === width }"
                >
                  {{ width }}px
                </button>
              </div>
            </div>
            <div class="drawing-container" ref="drawingContainerMobile">
              <canvas
                ref="drawingCanvasMobile"
                @mousedown="startDrawing"
                @mousemove="draw"
                @mouseup="stopDrawing"
                @mouseleave="stopDrawing"
                @touchstart.prevent="startDrawing"
                @touchmove.prevent="draw"
                @touchend.prevent="stopDrawing"
                class="drawing-canvas"
              ></canvas>
            </div>
          </div>

          <!-- 消息列表：移动端显示游戏面板时隐藏 -->
          <div
            class="messages-container"
            ref="messagesContainer"
            v-if="!(isMobile && showGamePanel)"
          >
            <!-- 系统消息提示条 -->
            <div v-if="systemMessage" ref="systemNotification" class="system-notification" :style="systemNotificationStyle">
              {{ systemMessage }}
            </div>
            <div
              v-for="message in messages"
              :key="message.id"
              :class="['message', message.isOwn ? 'own-message' : 'other-message', { 'grouped': message.showHeader === false }]"
            >
              <div v-if="message.showHeader" class="message-header">
                <span class="username">{{ message.user }}</span>
              </div>
              <div class="message-content">{{ message.content }}</div>
              <!-- 申请画画消息的同意按钮 -->
              <div v-if="message.isDrawingRequest && currentDrawer === username && message.user !== username" class="drawing-request-action">
                <button
                  @click="approveDrawingRequest(message.user)"
                  :disabled="!isConnected"
                  class="approve-btn-inline"
                >
                  同意
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部：输入区域（移动端游戏时隐藏） -->
      <div class="input-wrapper" v-if="roomId && !(isMobile && showGamePanel)" :class="{
        'keyboard-open': isKeyboardOpen && isMobile && !showMobileNavbar,
        'navbar-open': showMobileNavbar && isMobile
      }">
        <input
          v-model="newMessage"
          @keyup.enter="sendMessage"
          placeholder="输入消息..."
          :disabled="!isConnected"
          class="message-input"
        />
        <button
          @click="sendMessage"
          :disabled="!isConnected || !newMessage.trim()"
          class="send-btn"
        >
          发送
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import protobuf from 'protobufjs'
import config from '@/config'
import { api } from '@/utils/request.js'
import drawingMixin from '@/mixins/drawingMixin'
import LiveWarCanvas from '@/components/LiveWarCanvas.vue'
import UnitIcon from '@/components/UnitIcon.vue'
import StarBackground from '@/components/StarBackground.vue'

export default {
  name: 'Chat',
  mixins: [drawingMixin],
  data () {
    return {
      username: '',
      roomId: null,
      messages: [],
      newMessage: '',
      ws: null,
      isConnected: false,
      hasEverConnected: false, // 是否曾经连接成功过
      ChatMessage: null,
      availableRooms: [
        { id: 1 },
        { id: 2 },
        { id: 3 },
        { id: 4 },
        { id: 5 }
      ],
      currentRoomCount: 0,
      systemMessage: '',
      systemNotificationStyle: {},
      jumpRoomId: '',
      recentRooms: [],
      showMobileNavbar: false,
      isMobile: false,
      isKeyboardOpen: false,
      initialViewportHeight: 0,
      sidebarCollapsed: false, // 左侧菜单折叠状态
      musicConfig: {},
      showMusicMenu: false,
      isPlaying: false,
      currentMusicId: null,
      // 音频解锁相关状态
      audioUnlocked: false,
      audioContext: null,
      audioElement: null,
      musicMenuStyle: {},
      // LiveWar / 游戏相关状态
      showGamePanel: false,
      gameState: null,
      gameLogs: [],
      gamePlayers: [],
      gameTeamStats: { red: null, blue: null },
      inGame: false,
      selectedUnitType: 'miner',
      showPlayerList: false,
      showGameRules: false,
      gameOverInfo: null, // { winner: 'red'|'blue', winnerName: 'RED'|'BLUE', winnerPlayers: [] }
      unitTypesConfig: {
        miner: {
          name: '矿工',
          cost: 20,
          icon: '⛏️'
        },
        engineer: {
          name: '工程师',
          cost: 50,
          icon: '🔧'
        },
        heavy_tank: {
          name: '重装坦克',
          cost: 100,
          icon: '🛡️'
        },
        assault_tank: {
          name: '突击坦克',
          cost: 80,
          icon: '⚔️'
        }
      }
    }
  },
  computed: {
    currentRoomId () {
      return this.$route.params.roomId ? parseInt(this.$route.params.roomId) : null
    },
    isGameSpectator () {
      // 没有 gameState 或没有 player.team 视为观战者
      if (!this.gameState || !this.gameState.player) return true
      return !this.gameState.player.team
    },
    currentPlayer () {
      return this.gameState && this.gameState.player ? this.gameState.player : null
    },
    isGameStarted () {
      // 检查游戏是否已开始
      return this.gameState && this.gameState.game_started === true
    },
    currentBase () {
      if (!this.gameState || !this.gameState.room || !this.currentPlayer || !this.currentPlayer.team) return null
      return this.currentPlayer.team === 'red' ? this.gameState.room.redBase : this.gameState.room.blueBase
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
    redTeamUnitCount () {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u => !u.isDead && u.team === 'red').length
    },
    blueTeamUnitCount () {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u => !u.isDead && u.team === 'blue').length
    },
    redTeamPlayers () {
      if (!this.gameState) return []
      // 尝试从多个可能的位置获取玩家列表
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
      // 尝试从多个可能的位置获取玩家列表
      const players = this.gameState.players || []
      const teams = (this.gameState.room && this.gameState.room.teams) || {}

      return players.filter(p => {
        const playerId = p.userId || p.id
        const playerTeam = p.team || teams[playerId]
        return playerTeam === 'blue'
      })
    }
  },
  components: {
    UnitIcon,
    LiveWarCanvas,
    StarBackground
  },
  async mounted () {
    this.roomId = this.currentRoomId
    this.loadRecentRooms()
    this.checkMobileDevice()
    this.setupKeyboardDetection()
    this.initAudio() // 初始化音频系统
    await this.loadUserInfo()
    await this.loadProtobuf()
    if (this.roomId) {
      await this.loadMusicConfig()
      this.connectWebSocket()
    }
  },
  watch: {
    // 监听游戏面板和画画面板，自动收起菜单
    showGamePanel (newVal) {
      if (newVal && !this.isMobile) {
        this.sidebarCollapsed = true
      }
    },
    showDrawingPanel (newVal) {
      if (newVal && !this.isMobile) {
        this.sidebarCollapsed = true
      }
    },
    async '$route.params.roomId' (newRoomId) {
      const roomId = newRoomId ? parseInt(newRoomId) : null
      if (roomId !== this.roomId) {
        this.roomId = roomId
        this.messages = [] // 清空消息
        this.currentRoomCount = 0 // 重置房间人数
        // 清空游戏相关状态
        this.gameState = null
        this.gameLogs = []
        this.gamePlayers = []
        this.gameTeamStats = { red: null, blue: null }
        this.inGame = false
        this.gameOverInfo = null
        this.showGamePanel = false
        // 重置连接状态
        this.isConnected = false
        this.hasEverConnected = false
        if (this.ws) {
          this.ws.close()
        }
        if (this.roomId) {
          // 确保protobuf已加载
          if (!this.ChatMessage) {
            await this.loadProtobuf()
          }
          await this.loadMusicConfig()
          this.connectWebSocket()
        }
      }
    },
    // 监听消息变化，自动滚动到底部
    messages: {
      handler () {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true
    }
  },
  methods: {
    // 初始化音频系统
    initAudio () {
      try {
        // 创建HTML Audio元素
        this.audioElement = document.createElement('audio')
        this.audioElement.setAttribute('playsinline', 'true')
        this.audioElement.setAttribute('preload', 'auto')
        document.body.appendChild(this.audioElement)

        // 创建AudioContext（备用）
        if (window.AudioContext || window.webkitAudioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        }

        // 添加用户交互监听器来解锁音频
        this.addAudioUnlockListeners()

        console.log('音频系统初始化完成')
      } catch (err) {
        console.error('音频系统初始化失败:', err)
      }
    },

    // 添加音频解锁监听器
    addAudioUnlockListeners () {
      const unlockAudio = () => {
        if (!this.audioUnlocked) {
          this.unlockAudio()
        }
      }

      // 监听用户交互事件
      window.addEventListener('touchstart', unlockAudio, { once: true })
      window.addEventListener('click', unlockAudio, { once: true })
      window.addEventListener('keydown', unlockAudio, { once: true })
    },

    // 解锁音频
    unlockAudio () {
      if (!this.audioUnlocked) {
        try {
          // 尝试启动AudioContext
          if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume()
          }

          // 尝试播放音频元素（即使没有src也可以）
          if (this.audioElement) {
            this.audioElement.play().catch(() => {
              // 忽略初始播放失败，这是正常的
            })
          }

          this.audioUnlocked = true
          console.log('音频已解锁')
        } catch (err) {
          console.error('音频解锁失败:', err)
        }
      }
    },

    async loadUserInfo () {
      try {
        const response = await api.user.getMe()
        this.username = response.data.username
        // 保存 username 到 localStorage
        localStorage.setItem('username', response.data.username)
      } catch (err) {
        this.$router.push('/login')
      }
    },

    async loadMusicConfig () {
      if (!this.roomId) return
      try {
        console.log('开始加载音乐配置，房间ID:', this.roomId)
        const response = await api.music.getConfig(this.roomId)
        this.musicConfig = response.data
        console.log('音乐配置加载成功:', this.musicConfig)
      } catch (err) {
        console.error('获取音乐配置失败:', err)
      }
    },

    async loadProtobuf () {
      try {
        // 直接定义 protobuf 消息类型，避免文件加载问题
        const root = protobuf.Root.fromJSON({
          nested: {
            chat: {
              nested: {
                ChatMessage: {
                  fields: {
                    user: { type: 'string', id: 1 },
                    room_id: { type: 'int32', id: 2 },
                    content: { type: 'string', id: 3 },
                    timestamp: { type: 'int64', id: 4 },
                    type: { type: 'MessageType', id: 5 }
                  }
                },
                MessageType: {
                  values: {
                    UNKNOWN: 0,
                    SYSTEM: 1,
                    USER_TEXT: 2,
                    QUERY_COUNT: 3,
                    ROOM_COUNT: 4,
                    MUSIC: 5,
                    DRAWING: 6,
                    DRAWING_REQUEST: 7,
                    DRAWING_CLEAR: 8,
                    DRAWING_STATE: 9,
                    DRAWING_STOP: 10,
                    DRAWING_REQUEST_APPROVE: 11
                  }
                },
                WsEnvelope: {
                  fields: {
                    chat: { type: 'ChatMessage', id: 1 },
                    game: { type: 'livewar.GameMessage', id: 2 }
                  }
                }
              }
            },
            livewar: {
              nested: {
                GameMessage: {
                  fields: {
                    type: { type: 'Type', id: 1 },
                    // oneof payload（protobufjs 用 oneofs 描述）
                    join_game: { type: 'JoinGameRequest', id: 2 },
                    select_team: { type: 'SelectTeamRequest', id: 3 },
                    select_unit: { type: 'SelectUnitRequest', id: 4 },
                    spawn_unit: { type: 'SpawnUnitRequest', id: 5 },
                    leave_game: { type: 'LeaveGameRequest', id: 6 },
                    start_game: { type: 'StartGameRequest', id: 7 },
                    connected: { type: 'ConnectedPayload', id: 20 },
                    game_state: { type: 'GameStatePayload', id: 21 },
                    player_event: { type: 'PlayerEventPayload', id: 22 },
                    game_over: { type: 'GameOverPayload', id: 23 },
                    error: { type: 'ErrorPayload', id: 24 }
                  },
                  oneofs: {
                    payload: {
                      oneof: [
                        'join_game',
                        'select_team',
                        'select_unit',
                        'spawn_unit',
                        'leave_game',
                        'start_game',
                        'connected',
                        'game_state',
                        'player_event',
                        'game_over',
                        'error'
                      ]
                    }
                  },
                  nested: {
                    Type: {
                      values: {
                        UNKNOWN: 0,
                        JOIN_GAME: 1,
                        SELECT_TEAM: 2,
                        SELECT_UNIT: 3,
                        SPAWN_UNIT: 4,
                        LEAVE_GAME: 5,
                        START_GAME: 6,
                        CONNECTED: 10,
                        GAME_STATE: 11,
                        PLAYER_JOINED: 12,
                        PLAYER_LEFT: 13,
                        GAME_STARTED: 14,
                        GAME_OVER: 15,
                        ERROR: 16
                      }
                    }
                  }
                },
                JoinGameRequest: {
                  fields: {
                    name: { type: 'string', id: 1 },
                    team: { type: 'string', id: 2 }
                  }
                },
                SelectTeamRequest: {
                  fields: {
                    team: { type: 'string', id: 1 }
                  }
                },
                SelectUnitRequest: {
                  fields: {
                    unit_type: { type: 'string', id: 1 }
                  }
                },
                SpawnUnitRequest: { fields: {} },
                LeaveGameRequest: { fields: {} },
                StartGameRequest: { fields: {} },
                ConnectedPayload: {
                  fields: {
                    player_id: { type: 'string', id: 1 },
                    player_name: { type: 'string', id: 2 }
                  }
                },
                PlayerEventPayload: {
                  fields: {
                    player_id: { type: 'string', id: 1 },
                    player_name: { type: 'string', id: 2 },
                    team: { type: 'string', id: 3 }
                  }
                },
                GameOverPayload: {
                  fields: {
                    winner: { type: 'string', id: 1 },
                    winner_name: { type: 'string', id: 2 }
                  }
                },
                ErrorPayload: {
                  fields: {
                    message: { type: 'string', id: 1 }
                  }
                },
                Player: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    name: { type: 'string', id: 2 },
                    team: { type: 'string', id: 3 },
                    selected_unit_type: { type: 'string', id: 4 },
                    energy: { type: 'int32', id: 5 }
                  }
                },
                PlayerSummary: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    name: { type: 'string', id: 2 },
                    team: { type: 'string', id: 3 }
                  }
                },
                TeamStats: {
                  fields: {
                    units: { type: 'int32', id: 1 },
                    miners: { type: 'int32', id: 2 },
                    engineers: { type: 'int32', id: 3 },
                    tanks: { type: 'int32', id: 4 }
                  }
                },
                TeamStatsMap: {
                  fields: {
                    red: { type: 'TeamStats', id: 1 },
                    blue: { type: 'TeamStats', id: 2 }
                  }
                },
                Position: {
                  fields: {
                    x: { type: 'double', id: 1 },
                    y: { type: 'double', id: 2 }
                  }
                },
                TerrainCell: {
                  fields: {
                    x: { type: 'int32', id: 1 },
                    y: { type: 'int32', id: 2 },
                    type: { type: 'int32', id: 3 }
                  }
                },
                Base: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    x: { type: 'double', id: 2 },
                    y: { type: 'double', id: 3 },
                    hp: { type: 'int32', id: 4 },
                    hpMax: { type: 'int32', id: 5 }
                  }
                },
                MineField: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    x: { type: 'double', id: 2 },
                    y: { type: 'double', id: 3 },
                    energy: { type: 'int32', id: 4 },
                    energyMax: { type: 'int32', id: 5 }
                  }
                },
                EnergyDrop: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    x: { type: 'double', id: 2 },
                    y: { type: 'double', id: 3 },
                    energy: { type: 'int32', id: 4 }
                  }
                },
                HealEffect: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    x: { type: 'double', id: 2 },
                    y: { type: 'double', id: 3 },
                    created_time: { type: 'double', id: 4 },
                    lifetime: { type: 'double', id: 5 },
                    team: { type: 'string', id: 6 }
                  }
                },
                BulletEffect: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    from_x: { type: 'double', id: 2 },
                    from_y: { type: 'double', id: 3 },
                    to_x: { type: 'double', id: 4 },
                    to_y: { type: 'double', id: 5 },
                    created_time: { type: 'double', id: 6 },
                    lifetime: { type: 'double', id: 7 },
                    team: { type: 'string', id: 8 }
                  }
                },
                Unit: {
                  fields: {
                    id: { type: 'string', id: 1 },
                    type: { type: 'string', id: 2 },
                    team: { type: 'string', id: 3 },
                    owner_id: { type: 'string', id: 4 },
                    x: { type: 'double', id: 5 },
                    y: { type: 'double', id: 6 },
                    hp: { type: 'int32', id: 7 },
                    hp_max: { type: 'int32', id: 8 },
                    attack: { type: 'int32', id: 9 },
                    speed: { type: 'double', id: 10 },
                    is_dead: { type: 'bool', id: 11 },
                    carrying_energy: { type: 'int32', id: 12 },
                    target_x: { type: 'double', id: 13 },
                    target_y: { type: 'double', id: 14 }
                  }
                },
                Room: {
                  fields: {
                    name: { type: 'string', id: 1 },
                    width: { type: 'int32', id: 2 },
                    height: { type: 'int32', id: 3 },
                    walls: { rule: 'repeated', type: 'Position', id: 4 },
                    redBase: { type: 'Base', id: 5 },
                    blueBase: { type: 'Base', id: 6 },
                    mineFields: { rule: 'repeated', type: 'MineField', id: 7 },
                    units: { rule: 'repeated', type: 'Unit', id: 8 },
                    energyDrops: { rule: 'repeated', type: 'EnergyDrop', id: 9 },
                    healEffects: { rule: 'repeated', type: 'HealEffect', id: 10 },
                    bulletEffects: { rule: 'repeated', type: 'BulletEffect', id: 11 },
                    lakes: { rule: 'repeated', type: 'Position', id: 12 },
                    terrain: { rule: 'repeated', type: 'TerrainCell', id: 13 }
                  }
                },
                GameStatePayload: {
                  fields: {
                    tick: { type: 'int32', id: 1 },
                    game_time: { type: 'double', id: 2 },
                    game_started: { type: 'bool', id: 3 },
                    winner: { type: 'string', id: 4 },
                    player: { type: 'Player', id: 5 },
                    room: { type: 'Room', id: 6 },
                    logs: { rule: 'repeated', type: 'string', id: 7 },
                    team_stats: { type: 'TeamStatsMap', id: 8 },
                    players: { rule: 'repeated', type: 'PlayerSummary', id: 9 }
                  }
                }
              }
            }
          }
        })
        this.ChatMessage = root.lookupType('chat.ChatMessage')
        this.WsEnvelope = root.lookupType('chat.WsEnvelope')
        this.GameMessage = root.lookupType('livewar.GameMessage')

        if (!this.ChatMessage || !this.WsEnvelope || !this.GameMessage) {
          throw new Error('Failed to lookup protobuf types')
        }

        console.log('Protobuf loaded successfully', {
          hasChatMessage: !!this.ChatMessage,
          hasWsEnvelope: !!this.WsEnvelope,
          hasGameMessage: !!this.GameMessage
        })
      } catch (err) {
        console.error('Failed to load protobuf:', err)
        this.showSystemMessage('Protobuf 加载失败，请刷新页面重试')
      }
    },

    connectWebSocket () {
      const token = localStorage.getItem('token')
      const wsUrl = config.getWsUrl(this.roomId, token)

      // 重置连接状态
      this.isConnected = false
      // 注意：hasEverConnected 只在切换房间时重置，重连时不重置

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnected = true
        this.hasEverConnected = true
        console.log('WebSocket connected')
      }

      this.ws.onmessage = async (event) => {
        try {
          // 检查protobuf是否已加载
          if (!this.WsEnvelope || !this.ChatMessage) {
            console.warn('Protobuf types not loaded yet, skipping message')
            return
          }

          let data
          if (event.data instanceof Blob) {
            // 如果是 Blob，需要先转换为 ArrayBuffer
            const arrayBuffer = await event.data.arrayBuffer()
            data = new Uint8Array(arrayBuffer)
          } else {
            data = new Uint8Array(event.data)
          }

          const envelope = this.WsEnvelope.decode(data)

          // 先处理游戏消息（如果有）
          if (envelope.game && this.GameMessage) {
            console.log('[WebSocket] Received game message:', envelope.game.type, envelope.game)
            this.handleGameMessage(envelope.game)
          }

          // 再处理聊天/画图消息
          if (!envelope.chat) {
            return
          }

          const message = envelope.chat

          // 根据消息类型决定是否显示
          if (message.type === 4) {
            // ROOM_COUNT 消息更新房间人数
            this.updateRoomCount(message.content)
          } else if (message.type === 1) {
            // SYSTEM 消息显示在顶部提示条
            this.showSystemMessage(message.content)
          } else if (message.type === 5) {
            // MUSIC 消息
            console.log('收到音乐消息:', message)
            const musicInfo = this.musicConfig[message.content]
            console.log('音乐信息:', musicInfo)

            const newMessage = {
              id: Date.now() + Math.random(),
              user: message.user,
              content: musicInfo ? `🎵 ${musicInfo.name}` : `🎵 音乐: ${message.content}`,
              timestamp: message.timestamp,
              isOwn: message.user === this.username,
              showHeader: true,
              isMusic: true,
              musicId: message.content,
              musicUrl: musicInfo ? musicInfo.url : null
            }

            // 检查是否需要隐藏用户名（与上一条消息是同一用户）
            if (this.messages.length > 0) {
              const lastMessage = this.messages[this.messages.length - 1]
              if (lastMessage.user === newMessage.user && lastMessage.isOwn === newMessage.isOwn) {
                newMessage.showHeader = false
              }
            }

            this.messages.push(newMessage)

            // 自动播放音乐（如果有音乐信息）
            if (musicInfo) {
              console.log('准备延迟播放音乐:', message.content, '播放时间戳:', message.timestamp)
              this.playMusicWithDelay(message.content, message.timestamp)
            } else {
              console.log('不播放音乐，原因: 没有音乐信息')
            }

            this.$nextTick(() => {
              setTimeout(() => {
                this.scrollToBottom()
              }, 100)
            })
          } else if (message.type === 6) {
            // DRAWING 消息 - 画图数据
            // 如果用户正在绘制，忽略接收到的画图数据（避免覆盖正在绘制的内容）
            if (this.isDrawingActive && message.user === this.username) {
              return
            }
            // 如果画图面板未打开，先打开画图面板
            if (!this.showDrawingPanel) {
              this.showDrawingPanel = true
              this.$nextTick(() => {
                this.initCanvas()
                // 监听窗口大小变化，重新初始化画布
                window.addEventListener('resize', this.handleResize)
                // 画布初始化后加载图片
                setTimeout(() => {
                  this.handleDrawingData(message.content)
                }, 100)
              })
            } else {
              // 画图面板已打开，直接加载图片
              this.handleDrawingData(message.content)
            }
          } else if (message.type === 7) {
            // DRAWING_REQUEST 消息 - 申请画画
            // 在聊天框中显示申请消息
            if (message.user !== this.username) {
              // 如果当前用户是画画人，添加到申请列表（用于跟踪）
              if (this.currentDrawer === this.username) {
                if (!this.drawingRequests.includes(message.user)) {
                  this.drawingRequests.push(message.user)
                }
              }
              // 在聊天框中显示申请消息，标记为申请画画消息
              const requestMessage = {
                id: Date.now() + Math.random(),
                user: message.user,
                content: `${message.user} 申请画画`,
                timestamp: message.timestamp,
                isOwn: message.user === this.username,
                type: 'system',
                isDrawingRequest: true // 标记为申请画画消息
              }
              this.messages.push(requestMessage)
              this.$nextTick(() => {
                this.scrollToBottom()
              })
            }
          } else if (message.type === 8) {
            // DRAWING_CLEAR 消息 - 清空画布
            this.clearCanvas()
          } else if (message.type === 9) {
            // DRAWING_STATE 消息 - 画画人状态
            const newDrawer = message.content || null
            const wasDrawer = this.currentDrawer === this.username
            const oldDrawer = this.currentDrawer
            this.currentDrawer = newDrawer

            // 如果画画人变更，清理申请列表
            if (newDrawer !== oldDrawer) {
              this.drawingRequests = []
              // 如果当前用户不再是drawer，隐藏所有申请消息的同意按钮
              if (newDrawer !== this.username) {
                this.messages.forEach(m => {
                  if (m.isDrawingRequest) {
                    m.isDrawingRequest = false
                  }
                })
              }
            }

            // 如果当前用户成为画画人，启动倒计时
            if (newDrawer === this.username && !wasDrawer) {
              this.drawerStartTime = Date.now()
              this.drawerTimeRemaining = 600 // 10分钟
              this.startDrawerTimer()
            } else if (newDrawer !== this.username) {
              // 如果当前用户不再是画画人，停止倒计时
              this.stopDrawerTimer()
            }

            // 如果有画画人且画图面板未打开，自动打开画图面板
            if (this.currentDrawer && !this.showDrawingPanel) {
              this.showDrawingPanel = true
              this.$nextTick(() => {
                this.initCanvas()
                // 监听窗口大小变化，重新初始化画布
                window.addEventListener('resize', this.handleResize)
              })
            }
            // 如果没有画画人了，清空画布（如果当前用户是退出者）
            if (!this.currentDrawer && this.showDrawingPanel) {
              this.clearCanvas()
            }
          } else {
            // 用户文本消息
            const newMessage = {
              id: Date.now() + Math.random(),
              user: message.user,
              content: message.content,
              timestamp: message.timestamp,
              isOwn: message.user === this.username,
              showHeader: true
            }

            // 检查是否需要隐藏用户名（与上一条消息是同一用户）
            if (this.messages.length > 0) {
              const lastMessage = this.messages[this.messages.length - 1]
              if (lastMessage.user === newMessage.user && lastMessage.isOwn === newMessage.isOwn) {
                newMessage.showHeader = false
              }
            }

            this.messages.push(newMessage)

            this.$nextTick(() => {
              setTimeout(() => {
                this.scrollToBottom()
              }, 100)
            })
          }
        } catch (err) {
          console.error('Failed to decode message:', err)
        }
      }

      this.ws.onclose = () => {
        this.isConnected = false
        console.log('WebSocket disconnected')
      }

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        this.isConnected = false
      }
    },

    sendMessage () {
      if (!this.newMessage.trim() || !this.isConnected || !this.ChatMessage) {
        console.log('Cannot send message:', {
          hasMessage: !!this.newMessage.trim(),
          isConnected: this.isConnected,
          hasChatMessage: !!this.ChatMessage
        })
        return
      }

      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: this.newMessage,
          timestamp: Date.now(),
          type: 2 // USER_TEXT
        })

        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        this.newMessage = ''
        // 发送消息后自动滚动到底部
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (err) {
        console.error('Failed to send message:', err)
      }
    },

    scrollToBottom () {
      const container = this.$refs.messagesContainer
      if (container) {
        // 使用 smooth 滚动，提供更好的用户体验
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        })
      }
    },

    formatTime (timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },

    logout () {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      this.$router.push('/')
    },

    goToHome () {
      // 跳转到主页，但不退出登录（保留 token）
      // 添加标记表示用户主动返回主页，避免自动跳转回聊天页
      console.log('goToHome 被调用')
      this.$router.push({
        path: '/',
        query: { returnFromChat: 'true' }
      })
    },

    switchRoom (roomId) {
      if (roomId !== this.roomId) {
        this.currentRoomCount = 0 // 重置房间人数
        this.addToRecentRooms(roomId)
        this.$router.push(`/chat/${roomId}`)
        // 移动端切换房间后隐藏导航栏
        if (this.isMobile) {
          this.showMobileNavbar = false
        }
      }
    },

    updateRoomCount (content) {
      // 解析 "当前房间人数: X" 格式的消息
      const match = content.match(/当前房间人数: (\d+)/)
      if (match) {
        const count = parseInt(match[1])
        this.currentRoomCount = count
      }
    },

    showSystemMessage (content) {
      this.systemMessage = content
      // 更新系统通知的位置和宽度，使其与聊天区域一致
      this.$nextTick(() => {
        this.updateSystemNotificationStyle()
      })
      // 3秒后自动隐藏系统消息
      setTimeout(() => {
        this.systemMessage = ''
      }, 3000)
    },
    updateSystemNotificationStyle () {
      // 获取messages-container元素
      const messagesContainer = this.$refs.messagesContainer
      if (!messagesContainer) {
        // 如果找不到消息容器，使用默认样式
        this.systemNotificationStyle = {}
        return
      }

      // 由于system-notification现在在messages-container内部，使用absolute定位
      // 样式已经在CSS中设置，这里只需要确保容器有相对定位
      this.systemNotificationStyle = {}
    },

    reconnect () {
      if (this.ws) {
        this.ws.close()
      }
      this.isConnected = false
      this.connectWebSocket()
    },

    loadRecentRooms () {
      const saved = localStorage.getItem('recentRooms')
      if (saved) {
        this.recentRooms = JSON.parse(saved)
      } else {
        // 默认显示前5个房间
        this.recentRooms = this.availableRooms.slice(0, 5)
      }
    },

    addToRecentRooms (roomId) {
      // 移除已存在的相同房间
      this.recentRooms = this.recentRooms.filter(room => room.id !== roomId)
      // 添加到开头
      this.recentRooms.unshift({ id: roomId })
      // 限制最多5个
      this.recentRooms = this.recentRooms.slice(0, 5)
      // 保存到localStorage
      localStorage.setItem('recentRooms', JSON.stringify(this.recentRooms))
    },

    jumpToRoom () {
      const roomId = parseInt(this.jumpRoomId)
      if (roomId && roomId > 0) {
        this.jumpRoomId = ''
        this.addToRecentRooms(roomId)
        this.switchRoom(roomId)
      }
    },

    filterNumbers (event) {
      // 只保留数字
      const value = event.target.value.replace(/[^0-9]/g, '')
      this.jumpRoomId = value
    },

    checkMobileDevice () {
      // 检测是否为移动设备
      this.isMobile = window.innerWidth <= 768
      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        this.isMobile = window.innerWidth <= 768
        // 如果不是移动端，隐藏移动端导航栏
        if (!this.isMobile) {
          this.showMobileNavbar = false
        }
        // 更新系统通知样式
        if (this.systemMessage) {
          this.updateSystemNotificationStyle()
        }
      })
    },

    toggleMobileNavbar () {
      this.showMobileNavbar = !this.showMobileNavbar
    },

    hideMobileNavbar () {
      if (this.isMobile) {
        this.showMobileNavbar = false
      }
    },
    toggleSidebar () {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },

    setupKeyboardDetection () {
      // 记录初始视口高度，使用更准确的方法
      this.initialViewportHeight = Math.max(window.innerHeight, window.screen.height)

      // 监听窗口大小变化来检测键盘
      window.addEventListener('resize', this.handleKeyboardToggle)

      // 监听视口变化事件（移动端浏览器）
      if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', this.handleKeyboardToggle)
      }
    },

    handleKeyboardToggle () {
      if (!this.isMobile) return

      // 使用更准确的视口高度检测
      const currentHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight
      const heightDifference = this.initialViewportHeight - currentHeight

      // 如果高度减少超过100px，认为是键盘弹起
      if (heightDifference > 100) {
        this.isKeyboardOpen = true
      } else {
        this.isKeyboardOpen = false
      }
    },

    toggleMusicMenu () {
      this.showMusicMenu = !this.showMusicMenu
      if (this.showMusicMenu && this.$refs.musicButton) {
        this.$nextTick(() => {
          const buttonRect = this.$refs.musicButton.getBoundingClientRect()
          this.musicMenuStyle = {
            top: `${buttonRect.bottom + 8}px`,
            right: `${window.innerWidth - buttonRect.right}px`
          }
        })
      }
    },

    hideMusicMenu () {
      this.showMusicMenu = false
    },

    sendMusic (musicId) {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope) {
        console.log('Cannot send music:', {
          isConnected: this.isConnected,
          hasChatMessage: !!this.ChatMessage
        })
        return
      }

      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: musicId,
          timestamp: Date.now(),
          type: 5 // MUSIC
        })

        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        this.showMusicMenu = false
        console.log('音乐消息发送成功:', musicId)
      } catch (err) {
        console.error('Failed to send music message:', err)
      }
    },

    // 清理音频资源
    cleanupAudio () {
      try {
        // 停止当前播放
        if (this.audioElement) {
          this.audioElement.pause()
          this.audioElement.currentTime = 0
          this.audioElement.src = ''
          if (this.audioElement.parentNode) {
            this.audioElement.parentNode.removeChild(this.audioElement)
          }
          this.audioElement = null
        }

        // 清理AudioContext
        if (this.audioContext) {
          this.audioContext.close()
          this.audioContext = null
        }

        // 重置状态
        this.isPlaying = false
        this.currentMusicId = null
        this.audioUnlocked = false

        console.log('音频资源已清理')
      } catch (err) {
        console.error('清理音频资源失败:', err)
      }
    },

    // 新的音乐播放方法
    playMusicFromServer (musicUrl, musicId) {
      console.log('准备播放服务端推送的音乐:', musicUrl, musicId)

      if (!this.audioUnlocked) {
        console.warn('音频尚未解锁，播放可能会失败')
      }

      if (!musicUrl) {
        console.warn('音乐URL为空，无法播放')
        return
      }

      try {
        // 停止当前播放的音乐
        this.stopCurrentMusic()

        // 设置新的音频源
        this.audioElement.src = musicUrl
        this.currentMusicId = musicId
        this.isPlaying = true

        // 添加事件监听器
        this.setupAudioEventListeners()

        // 开始播放
        const playPromise = this.audioElement.play()

        if (playPromise !== undefined) {
          playPromise.then(() => {
            console.log('音乐开始播放:', musicUrl)
          }).catch(err => {
            console.error('音乐播放失败:', err)

            // 播放失败，直接清理状态
            this.stopCurrentMusic()
          })
        }
      } catch (err) {
        console.error('播放音乐时发生错误:', err)
        this.stopCurrentMusic()
      }
    },

    // 设置音频事件监听器
    setupAudioEventListeners () {
      if (!this.audioElement) return

      // 移除旧的事件监听器
      this.removeAudioEventListeners()

      // 添加新的事件监听器
      this.audioElement.addEventListener('loadstart', () => {
        console.log('开始加载音乐')
      })

      this.audioElement.addEventListener('canplay', () => {
        console.log('音乐可以播放')
      })

      this.audioElement.addEventListener('play', () => {
        console.log('音乐开始播放')
      })

      this.audioElement.addEventListener('ended', () => {
        console.log('音乐播放结束')
        this.stopCurrentMusic()
      })

      this.audioElement.addEventListener('error', (e) => {
        console.error('音乐播放错误:', e)
        this.stopCurrentMusic()
      })
    },

    // 移除音频事件监听器
    removeAudioEventListeners () {
      if (!this.audioElement) return

      const events = ['loadstart', 'canplay', 'play', 'ended', 'error']
      events.forEach(event => {
        this.audioElement.removeEventListener(event, () => {})
      })
    },

    // 停止当前音乐播放
    stopCurrentMusic () {
      try {
        if (this.audioElement) {
          this.audioElement.pause()
          this.audioElement.currentTime = 0
          this.audioElement.src = ''
        }

        this.removeAudioEventListeners()

        this.isPlaying = false
        this.currentMusicId = null

        console.log('当前音乐已停止')
      } catch (err) {
        console.error('停止音乐播放失败:', err)
      }
    },

    // 延迟播放音乐（根据服务端设置的时间戳）
    playMusicWithDelay (musicId, targetTimestamp) {
      console.log('尝试延迟播放音乐:', musicId, '目标时间戳:', targetTimestamp)
      console.log('当前音乐配置:', this.musicConfig)

      const musicInfo = this.musicConfig[musicId]
      if (!musicInfo || !musicInfo.url) {
        console.warn('音乐信息不存在或URL为空:', musicId, musicInfo)
        return
      }

      console.log('找到音乐信息:', musicInfo)

      // 计算延迟时间
      const currentTime = Date.now()
      const delay = targetTimestamp - currentTime

      console.log('当前时间:', currentTime, '延迟时间:', delay, 'ms')

      if (delay <= 0) {
        // 如果延迟时间已过，立即播放
        console.log('延迟时间已过，立即播放音乐')
        this.playMusicFromServer(musicInfo.url, musicId)
      } else {
        // 设置延迟播放
        console.log('设置延迟播放，等待', delay, 'ms')
        setTimeout(() => {
          console.log('延迟时间到达，开始播放音乐')
          this.playMusicFromServer(musicInfo.url, musicId)
        }, delay)
      }
    },

    // 播放音乐（从音乐ID）
    playMusic (musicId) {
      console.log('尝试播放音乐:', musicId)
      console.log('当前音乐配置:', this.musicConfig)

      const musicInfo = this.musicConfig[musicId]
      if (!musicInfo || !musicInfo.url) {
        console.warn('音乐信息不存在或URL为空:', musicId, musicInfo)
        return
      }

      console.log('找到音乐信息:', musicInfo)

      // 使用新的播放方法
      this.playMusicFromServer(musicInfo.url, musicId)
    },

    // 停止音乐播放
    stopMusic () {
      this.stopCurrentMusic()
    },

    // ====== LiveWar 简化逻辑 ======
    toggleGamePanel () {
      // 如果打开游戏面板，先关闭画画面板（互斥）
      if (!this.showGamePanel && this.showDrawingPanel) {
        this.showDrawingPanel = false
      }
      this.showGamePanel = !this.showGamePanel
    },

    handleGameMessage (msg) {
      if (!this.GameMessage) return

      // 根据类型更新本地状态
      if (msg.type === this.GameMessage.Type.GAME_STATE && msg.game_state) {
        this.gameState = msg.game_state
        this.gameLogs = msg.game_state.logs || []
        this.gamePlayers = msg.game_state.players || []
        this.gameTeamStats = msg.game_state.team_stats || { red: null, blue: null }
        this.inGame = !!(msg.game_state.player && msg.game_state.player.team)
      } else if (msg.type === this.GameMessage.Type.ERROR && msg.error) {
        // 只显示自己的错误消息，不显示其他人的能量不足等提醒
        const errorMessage = msg.error.message || ''
        // 如果是能量不足的错误，不显示（因为错误消息是广播给所有玩家的，其他人的能量不足不应该显示）
        if (errorMessage.includes('能量不足')) {
          // 不显示其他人的能量不足提醒
          return
        }
        // 其他错误消息正常显示
        this.showSystemMessage(errorMessage)
      } else if (msg.type === this.GameMessage.Type.GAME_OVER && msg.game_over) {
        const info = msg.game_over
        const winner = info.winner || 'red'
        const winnerName = info.winner_name || (winner === 'red' ? 'RED' : 'BLUE')

        // 获取胜利方队员列表
        const winnerPlayers = winner === 'red' ? this.redTeamPlayers : this.blueTeamPlayers

        this.gameOverInfo = {
          winner,
          winnerName,
          winnerPlayers: winnerPlayers.map(p => p.name || p.username || 'Unknown'),
          gameOverTime: Date.now()
        }

        this.showSystemMessage(`LiveWar 结束，${winnerName} 获胜`)

        // 10秒后清除游戏结束信息
        setTimeout(() => {
          this.gameOverInfo = null
        }, 10000)
      }

      // 更新gameState中的winner信息
      if (msg.type === this.GameMessage.Type.GAME_STATE && msg.game_state) {
        if (msg.game_state.winner && !this.gameOverInfo) {
          // 如果游戏已结束但还没有显示结束信息，设置结束信息
          const winner = msg.game_state.winner
          const winnerName = winner === 'red' ? 'RED' : 'BLUE'
          const winnerPlayers = winner === 'red' ? this.redTeamPlayers : this.blueTeamPlayers

          this.gameOverInfo = {
            winner,
            winnerName,
            winnerPlayers: winnerPlayers.map(p => p.name || p.username || 'Unknown'),
            gameOverTime: Date.now()
          }

          // 10秒后清除游戏结束信息
          setTimeout(() => {
            this.gameOverInfo = null
          }, 10000)
        }
      }
    },

    joinGame (team) {
      console.log('joinGame called', { team, isConnected: this.isConnected, hasWsEnvelope: !!this.WsEnvelope, hasGameMessage: !!this.GameMessage, username: this.username })

      if (!this.isConnected) {
        console.warn('Cannot join game: WebSocket not connected')
        this.showSystemMessage('WebSocket 未连接，无法加入游戏')
        return
      }

      if (!this.WsEnvelope) {
        console.warn('Cannot join game: WsEnvelope not loaded')
        this.showSystemMessage('Protobuf 未加载，请刷新页面重试')
        return
      }

      if (!this.GameMessage) {
        console.warn('Cannot join game: GameMessage not loaded')
        this.showSystemMessage('游戏消息类型未加载，请刷新页面重试')
        return
      }

      if (!this.username) {
        console.warn('Cannot join game: username not set')
        this.showSystemMessage('用户名未设置，无法加入游戏')
        return
      }

      try {
        const joinReq = { name: this.username, team }
        console.log('Creating GameMessage with:', joinReq)

        const gameMsg = this.GameMessage.create({
          type: this.GameMessage.Type.JOIN_GAME,
          join_game: joinReq
        })
        console.log('GameMessage created:', gameMsg)

        const envelope = this.WsEnvelope.create({ game: gameMsg })
        console.log('WsEnvelope created:', envelope)

        const buf = this.WsEnvelope.encode(envelope).finish()
        console.log('Sending game message, buffer length:', buf.length)

        this.ws.send(buf)
        this.showGamePanel = true
        console.log('Game join message sent successfully')
      } catch (e) {
        console.error('joinGame failed', e)
        this.showSystemMessage(`加入游戏失败: ${e.message || '未知错误'}`)
      }
    },

    leaveGame () {
      if (!this.isConnected || !this.WsEnvelope || !this.GameMessage) return
      try {
        const gameMsg = this.GameMessage.create({
          type: this.GameMessage.Type.LEAVE_GAME,
          leave_game: {}
        })
        const envelope = this.WsEnvelope.create({ game: gameMsg })
        const buf = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buf)
      } catch (e) {
        console.error('leaveGame failed', e)
      }
    },

    selectUnitType (unitTypeKey) {
      if (!this.isConnected || !this.WsEnvelope || !this.GameMessage) return
      this.selectedUnitType = unitTypeKey
      try {
        const msg = this.GameMessage.create({
          type: this.GameMessage.Type.SELECT_UNIT,
          select_unit: { unit_type: unitTypeKey }
        })
        const env = this.WsEnvelope.create({ game: msg })
        const buf = this.WsEnvelope.encode(env).finish()
        this.ws.send(buf)
      } catch (e) {
        console.error('selectUnitType failed', e)
      }
    },

    spawnUnit () {
      if (!this.isConnected || !this.WsEnvelope || !this.GameMessage) return
      try {
        const msg = this.GameMessage.create({
          type: this.GameMessage.Type.SPAWN_UNIT,
          spawn_unit: {}
        })
        const env = this.WsEnvelope.create({ game: msg })
        const buf = this.WsEnvelope.encode(env).finish()
        this.ws.send(buf)
      } catch (e) {
        console.error('spawnUnit failed', e)
      }
    },
    selectAndSpawnUnit (unitTypeKey) {
      // 先选择单位类型
      this.selectUnitType(unitTypeKey)
      // 然后立即生成
      this.spawnUnit()
    },
    getUnitCount (unitType) {
      // 只显示自己的单位数量
      if (!this.gameState || !this.gameState.room || !this.currentPlayer || !this.currentPlayer.team) return 0
      // Player 的 id 字段是字符串形式的 user_id（后端 build_state_for_user 中设置为 str(user_id)）
      const currentUserId = String(this.currentPlayer.id || '')
      if (!currentUserId) {
        return 0
      }

      const allUnits = this.gameState.room.units || []
      const myUnits = allUnits.filter(u => {
        // 检查单位是否死亡、队伍、类型
        if (u.isDead || u.team !== this.currentPlayer.team || u.type !== unitType) {
          return false
        }
        // protobufjs 会将 snake_case 转换为 camelCase，所以 owner_id 变成 ownerId
        // 同时兼容两种命名方式
        const unitOwnerId = String(u.ownerId || u.owner_id || '')
        return unitOwnerId === currentUserId
      })

      return myUnits.length
    },
    // 获取红方各兵种数量
    getRedTeamUnitCountByType (unitType) {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u =>
        !u.isDead && u.team === 'red' && u.type === unitType
      ).length
    },
    // 获取蓝方各兵种数量
    getBlueTeamUnitCountByType (unitType) {
      if (!this.gameState || !this.gameState.room || !this.gameState.room.units) return 0
      return this.gameState.room.units.filter(u =>
        !u.isDead && u.team === 'blue' && u.type === unitType
      ).length
    }

  },
  beforeUnmount () {
    if (this.ws) {
      this.ws.close()
    }
    // 清理音频资源
    this.cleanupAudio()
    // 清理窗口大小变化监听器（非画图相关）
    window.removeEventListener('resize', this.checkMobileDevice)
    // 清理键盘检测监听器
    window.removeEventListener('resize', this.handleKeyboardToggle)
    // 清理视口变化监听器
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', this.handleKeyboardToggle)
    }
  }
}
</script>

<style>
/* 全局样式：禁止页面滚动 */
html, body {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
  background: transparent; /* 去除默认白色背景 */
}

#app {
  height: 100%;
  overflow: hidden;
  background: transparent; /* 去除默认背景 */
}
</style>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  height: 100dvh; /* 使用动态视口高度，更好地处理移动端 */
  background: transparent; /* 透明背景，显示星空 */
  overflow: hidden; /* 防止整体滚动 */
  position: fixed; /* 固定定位，防止页面滚动 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  padding: 20px; /* 为所有区域留出20px间距 */
  box-sizing: border-box;
  gap: 8px; /* 区域之间的间距 */
}

/* 左侧导航栏 */
.left-sidebar {
  width: 250px;
  background: #ffffff;
  color: #000000;
  display: flex;
  flex-direction: column;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  transition: width 0.3s ease, transform 0.3s ease;
  z-index: 1000;
  position: relative;
  overflow: hidden;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* 折叠状态 */
.left-sidebar.collapsed {
  width: 40px;
}

.left-sidebar.collapsed .sidebar-content {
  display: none;
}

.left-sidebar.collapsed .sidebar-collapsed-label {
  display: flex;
}

/* 折叠/展开按钮 */
.sidebar-toggle-btn {
  position: absolute;
  top: 1rem;
  right: 0.5rem;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 0;
  color: #000000;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  transition: color 0.2s;
  padding: 0;
}

.sidebar-toggle-btn:hover {
  color: #000000;
}

/* 折叠状态下，按钮居中显示 */
.left-sidebar.collapsed .sidebar-toggle-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  right: auto;
  transform: translate(-50%, -50%);
  margin: 0;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
}

/* 移动端遮罩层 */
.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 999;
  touch-action: none; /* 防止移动端触摸手势 */
}

/* 防止移动端双击缩放 - 针对按钮和可交互元素 */
button,
.unit-spawn-btn,
.join-team-btn,
.game-exit-btn,
.player-list-toggle,
.sidebar-toggle-btn,
.drawing-btn,
.menu-btn {
  touch-action: manipulation; /* 禁用双击缩放，但保留点击 */
}

/* 对于需要滚动的容器，允许垂直滚动 */
.messages-container,
.player-list-container {
  touch-action: pan-y; /* 允许垂直滚动 */
}

/* 移动端导航栏显示/隐藏 */
@media (max-width: 768px) {
  .left-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    height: 100dvh; /* 移动端使用动态视口高度 */
    transform: translateX(-100%);
    z-index: 1000;
    display: flex;
    flex-direction: column;
  }

  .left-sidebar.mobile-show {
    transform: translateX(0);
  }
}

.logo-section {
  padding: 0.5rem 0; /* 减小padding，让logo更大 */
  border-bottom: 1px solid #000000;
  /* 与chat-header高度保持一致：统一设置为65px */
  height: 65px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  pointer-events: auto;
  position: relative;
  z-index: 1002;
}

.logo-text {
  margin: 0;
  text-align: center;
  color: #000000;
  font-size: 1.25rem;
  font-weight: 600;
  position: relative;
  z-index: 2;
  line-height: 1.2;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  pointer-events: auto;
  -webkit-tap-highlight-color: transparent;
  /* 默认状态：黑色文字 */
  background: #000000;
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: #000000;
}

.logo-section:hover .logo-text {
  /* hover 状态：彩色渐变文字 */
  background: linear-gradient(
    90deg,
    #ff0096,
    #ff6400,
    #ffff00,
    #00ff96,
    #0096ff,
    #9600ff,
    #ff0096
  );
  background-size: 200% 100%;
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 1.5s ease infinite;
  transform: translate(-1px, -1px);
}

@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.rooms-section {
  flex: 1;
  padding: 1rem;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
  overflow-y: auto; /* 如果内容过多，允许滚动 */
  overflow-x: hidden; /* 隐藏横向滚动条 */
}

/* 左侧菜单栏滚动条美化 - WebKit浏览器（Chrome, Safari, Edge） */
.rooms-section::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}

.rooms-section::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.03); /* 滚动条轨道背景，更透明 */
  border-radius: 3px;
  margin: 0.5rem 0; /* 上下留出一些空间 */
}

.rooms-section::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15); /* 滚动条滑块背景 */
  border-radius: 3px;
  transition: background 0.2s ease, width 0.2s ease;
}

.rooms-section::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25); /* 悬停时更亮 */
}

.rooms-section::-webkit-scrollbar-thumb:active {
  background: rgba(255, 255, 255, 0.35); /* 点击时更亮 */
}

/* Firefox 滚动条样式 */
.rooms-section {
  scrollbar-width: thin; /* Firefox: thin, auto, none */
  scrollbar-color: rgba(255, 255, 255, 0.15) rgba(255, 255, 255, 0.03); /* Firefox: thumb track */
}

.rooms-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #000000;
  font-weight: 500;
}

.room-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.room-item {
  padding: 0.75rem;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  color: #000000;
}

.room-item.active {
  background: #000000;
  color: #ffffff;
}

.room-name {
  font-weight: 500;
}

.room-jump {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.room-jump h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #000000;
  font-weight: 500;
}

.jump-input-group {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  transition: all 0.3s ease;
}

.jump-input {
  flex: 1;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  color: #000000;
  font-size: 1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  text-align: center;
  min-width: 0;
}

.jump-input::placeholder {
  color: rgba(0, 0, 0, 0.5);
  font-weight: 500;
}

.jump-input:focus {
  background: transparent;
}

.jump-btn {
  flex: 1;
  padding: 0;
  background: transparent;
  color: #000000;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.3s ease;
  text-align: center;
  min-width: 40px;
  max-width: 60px;
  flex-shrink: 0;
}

.jump-btn:hover {
  background: transparent;
}

.user-section {
  padding: 1rem;
  border-top: 1px solid #000000;
  flex-shrink: 0; /* 防止用户区域被压缩 */
}

.user-info {
  margin-bottom: 1rem;
}

.user-info .username {
  font-weight: 500;
  color: #000000;
}

/* 导航栏连接状态 */
.connection-status-navbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.8rem;
}

.connection-status-navbar .status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.connection-status-navbar .status-indicator.connected {
  background: #22c55e;
}

.connection-status-navbar .status-text {
  color: #000000;
  font-weight: 500;
}

.connection-status-navbar .status-text.connecting {
  color: #000000;
}

.connection-status-navbar .reconnect-btn {
  padding: 0.25rem 0.5rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.25s ease;
}

.connection-status-navbar .reconnect-btn:hover {
  background: #000000;
}

.logout-btn {
  width: 100%;
  padding: 0.75rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.25s ease;
}

.logout-btn:hover {
  background: #000000;
}

/* 中间画布区域 */
.drawing-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0; /* 允许收缩 */
  overflow: hidden;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  /* 确保画布区域始终在可见区域内 */
  max-height: 100vh;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* 中间游戏区域（类似 drawing-area） */
.game-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0; /* 允许收缩 */
  overflow: hidden;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  /* 确保游戏区域始终在可见区域内 */
  max-height: 100vh;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* 右侧聊天区域 */
.right-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
  overflow: hidden; /* 防止内容溢出 */
  position: relative;
  z-index: 1;
  gap: 8px; /* 聊天区域内部三个气泡之间的间距 */
}

/* 当有画图面板时，右侧聊天区域固定宽度（仅桌面端） */
@media (min-width: 769px) {
  .right-chat.with-drawing {
    flex: 0 0 400px; /* 固定宽度400px */
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.02);
  }

  /* 当有游戏面板时，右侧聊天区域固定宽度（仅桌面端） */
  .right-chat.with-game {
    flex: 0 0 400px; /* 固定宽度400px */
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.02);
  }

  /* 宽屏自适应：VS对战信息在不同宽度下的响应式调整 */
  @media (min-width: 1200px) {
    .top-bar-double-row {
      gap: clamp(1rem, 2vw, 1.5rem); /* 宽屏时增加间距 */
    }

    .vs-divider-double {
      font-size: clamp(1rem, 2.5vw, 1.4rem); /* 宽屏时字体稍大 */
      margin: 0 clamp(1rem, 2vw, 1.5rem); /* 宽屏时增加间距 */
    }

    .units-by-type {
      gap: clamp(0.5rem, 1.5vw, 0.75rem); /* 宽屏时增加间距 */
    }
  }

  @media (min-width: 1600px) {
    .top-bar-double-row {
      gap: clamp(1.5rem, 3vw, 2rem); /* 超宽屏时进一步增加间距 */
    }

    .vs-divider-double {
      font-size: clamp(1.2rem, 3vw, 1.6rem); /* 超宽屏时字体更大 */
      margin: 0 clamp(1.5rem, 3vw, 2rem); /* 超宽屏时进一步增加间距 */
    }
  }
}

/* 系统消息提示条 */
.system-notification {
  position: absolute; /* 绝对定位，相对于messages-container */
  top: 0.5rem; /* 位于messages-container顶部，与边缘保持间距 */
  left: 0.5rem; /* 从左侧开始，与边缘保持间距 */
  right: 0.5rem; /* 延伸到右侧，与边缘保持间距 */
  z-index: 9999; /* 确保在最上层 */
  min-height: 30px;
  padding: 8px 20px; /* 内边距，使内容不贴边 */
  background: #000000;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
  pointer-events: none; /* 不阻挡鼠标事件 */
  border-radius: var(--px-border-radius, 15px);
  border: var(--px-border, 3px) solid #000000;
  box-sizing: border-box; /* 确保边框包含在宽度内 */
}

.chat-header {
  background: #ffffff;
  padding: 1rem 1.5rem;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 100;
  overflow: visible;
  box-sizing: border-box;
  /* 统一高度为65px */
  height: 65px;
  flex-shrink: 0; /* 防止被压缩 */
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  transition: all 0.25s ease;
}

.menu-btn:hover {
  background: #000000;
}

.menu-btn svg {
  stroke: currentColor;
}

.chat-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.5rem;
  line-height: 1.2; /* 明确设置line-height，确保高度计算准确 */
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #000000;
  position: relative;
  z-index: 101;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.connected {
  background: #22c55e;
}

.status-text {
  color: #000000;
  font-weight: 500;
}

.reconnect-btn {
  padding: 0.5rem 1rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.25s ease;
}

.reconnect-btn:hover {
  background: #000000;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  position: relative;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* 移动端游戏面板样式 */
.game-panel-mobile {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent; /* 在气泡容器内，使用父容器背景 */
  border: none; /* 在气泡容器内，不需要边框 */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  margin-bottom: 1rem;
  border-radius: 0; /* 在气泡容器内，不需要圆角 */
  overflow: hidden;
}

/* 画图面板样式 */
.drawing-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: none;
  overflow: hidden;
  min-width: 0;
  min-height: 0;
  border-radius: 0; /* 画图面板在气泡容器内，不需要额外圆角 */
}

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
  height: 28px;
  background: rgba(0, 0, 0, 0.7);
  overflow: hidden; /* 隐藏溢出，确保边框不被覆盖 */
  border: 3px solid rgba(255, 255, 255, 0.3);
  position: relative;
  box-sizing: border-box; /* 确保边框包含在高度内 */
  padding: 0; /* 确保没有内边距 */
}

.pixel-border {
  border-radius: 0;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.2),
    0 2px 0 rgba(0, 0, 0, 0.5);
}

.hp-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  min-width: 50px; /* 确保有足够空间显示文字 */
  box-sizing: border-box; /* 确保padding包含在宽度内 */
  max-width: 100%; /* 确保不会超出容器 */
}

.pixel-fill {
  border-radius: 0;
}

.hp-bar-fill.red {
  background: #ef4444;
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(0, 0, 0, 0.3);
  justify-content: flex-start;
  padding-left: 4px;
}

.hp-bar-fill.blue {
  background: #3b82f6;
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(0, 0, 0, 0.3);
  justify-content: flex-end;
  padding-right: 4px;
}

.hp-value-inside {
  font-size: 0.9rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  z-index: 10;
  position: relative;
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
  gap: 0.5rem;
  width: 100%;
}

/* 玩家列表下拉按钮 */
.player-list-toggle {
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  color: #000000;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  flex: 1;
  height: 40px; /* 固定高度 */
  text-align: left;
  box-sizing: border-box;
  display: flex;
  align-items: center; /* 垂直居中文字 */
  border-radius: var(--px-border-radius, 15px);
  text-shadow: none;
}

.player-list-toggle:hover {
  background: #ffffff;
  border-color: #000000;
}

/* 游戏规则按钮 */
.game-rules-toggle {
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  color: #000000;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  flex: 1;
  height: 40px; /* 固定高度 */
  text-align: left;
  box-sizing: border-box;
  display: flex;
  align-items: center; /* 垂直居中文字 */
  border-radius: var(--px-border-radius, 15px);
  text-shadow: none;
}

.game-rules-toggle:hover {
  background: #ffffff;
  border-color: #000000;
}

/* 玩家列表展开区域（悬浮在上层） */
.player-list-container {
  position: absolute;
  top: calc(100% + 0.5rem); /* 距离按钮下方0.5rem */
  left: 0; /* 相对于 top-bar-row 左对齐 */
  right: 0; /* 相对于 top-bar-row 右对齐 */
  width: auto; /* 使用 left/right 来控制宽度 */
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-top: var(--px-border, 3px) solid #000000; /* 添加上边框 */
  padding: 1rem;
  box-sizing: border-box;
  z-index: 1000; /* 确保在上层 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  max-height: 300px; /* 限制最大高度 */
  overflow-y: auto; /* 如果内容过多，可以滚动 */
  /* 确保不影响父元素高度计算 */
  pointer-events: auto; /* 确保可以交互 */
  /* 美化滚动条 - Webkit (Chrome, Safari, Edge) */
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent; /* Firefox */
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
  gap: 1rem;
  align-items: stretch;
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
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  box-sizing: border-box;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.player-list-empty {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
  padding: 0.5rem;
}

/* 游戏规则展开区域（悬浮在上层） */
.game-rules-container {
  position: absolute;
  top: 100%; /* 紧贴在 top-bar-row 下方 */
  left: 0; /* 相对于 top-bar-row 左对齐 */
  right: 0; /* 相对于 top-bar-row 右对齐 */
  width: auto; /* 使用 left/right 来控制宽度 */
  background: rgba(0, 0, 0, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: none;
  padding: 1rem;
  box-sizing: border-box;
  z-index: 1000; /* 确保在上层 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  max-height: 500px; /* 限制最大高度 */
  overflow-y: auto; /* 如果内容过多，可以滚动 */
  /* 确保不影响父元素高度计算 */
  pointer-events: auto; /* 确保可以交互 */
  margin-top: 0; /* 确保没有额外间距 */
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.75rem;
  border-radius: 0;
}

.unit-rule-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
  color: #fff;
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

/* 巨大的退出按钮 */
.game-exit-btn {
  width: 100%;
  max-width: 400px;
  height: auto;
  min-height: 60px;
  padding: 0.75rem 1rem;
  border: var(--px-border, 3px) solid #000000;
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--px-border-radius, 15px);
}

/* 红方退出按钮 */
.game-exit-btn.red-team {
  background: #ef4444;
}

.game-exit-btn.red-team:hover:not(:disabled) {
  background: #dc2626;
  border-color: #000000;
}

/* 蓝方退出按钮 */
.game-exit-btn.blue-team {
  background: #3b82f6;
}

.game-exit-btn.blue-team:hover:not(:disabled) {
  background: #2563eb;
  border-color: #000000;
}

.game-exit-btn:active:not(:disabled) {
  background: #000000;
}

.game-exit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

.player-stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.energy-display {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0.5rem;
  padding-left: 1.5rem; /* 为背景图标留出空间 */
  background: rgba(251, 191, 36, 0.2);
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 8px;
  position: relative;
}

.energy-display::before {
  content: '⚡';
  position: absolute;
  left: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  opacity: 0.3;
  pointer-events: none;
  z-index: 0;
}

.energy-value {
  position: relative;
  z-index: 1;
}

.energy-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fbbf24;
}

.unit-counts {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.unit-count-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
}

.unit-count-icon {
  opacity: 0.8;
}

.unit-count-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: #000000;
}

/* 四个兵种按钮 */
.unit-spawn-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.unit-spawn-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  transition: all 0.2s ease;
}

.unit-spawn-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.unit-spawn-btn.red-team:hover:not(.disabled) {
  border-color: #ef4444;
}

.unit-spawn-btn.blue-team:hover:not(.disabled) {
  border-color: #3b82f6;
}

.unit-spawn-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  font-weight: 600;
  color: #000000;
}

.unit-spawn-cost {
  font-size: 0.75rem;
  color: #fbbf24;
  font-weight: 600;
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
  flex: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 700;
  border: var(--px-border, 3px) solid #000000;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: var(--px-border-radius, 15px);
  box-sizing: border-box;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.join-team-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

.join-team-btn:not(:disabled):hover {
  background: #000000;
}

.join-red-btn {
  background: #ef4444;
  color: #fff;
  border-color: #000000;
}

.join-red-btn:not(:disabled):hover {
  background: #dc2626;
}

.join-blue-btn {
  background: #3b82f6;
  color: #fff;
  border-color: #000000;
}

.join-blue-btn:not(:disabled):hover {
  background: #2563eb;
}

/* LiveWar 游戏面板 - 旧布局（保留兼容） */
.game-panel {
  margin: 0 1.5rem 1rem 1.5rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.game-status-left {
  color: #e5e7eb;
  font-size: 0.9rem;
}

.game-status-right {
  display: flex;
  gap: 0.5rem;
}

.game-body {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.game-column {
  flex: 1 1 180px;
}

.game-column h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #cbd5f5;
}

.game-player-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.game-player-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  font-size: 0.85rem;
  color: #e5e7eb;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-red {
  background: rgba(248, 113, 113, 0.2);
  color: #fecaca;
}

.badge-blue {
  background: rgba(96, 165, 250, 0.2);
  color: #bfdbfe;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.2);
  color: #e5e7eb;
}

.player-name {
  flex: 1;
}

.team-stats {
  display: flex;
  gap: 0.75rem;
}

.team-stat {
  flex: 1;
  padding: 0.5rem 0.6rem;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.6);
}

.team-stat.red {
  border: 1px solid rgba(248, 113, 113, 0.5);
}

.team-stat.blue {
  border: 1px solid rgba(96, 165, 250, 0.5);
}

.team-title {
  font-size: 0.8rem;
  color: #e5e7eb;
  margin-bottom: 0.25rem;
}

.team-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f9fafb;
}

/* 能量 / 基地 / 生成单位（简化版） */
.energy-display-mini {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.5rem;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(250, 204, 21, 0.3);
  margin-bottom: 0.4rem;
}

.energy-value-mini {
  font-size: 0.95rem;
  font-weight: 600;
  color: #facc15;
}

.base-hp-mini {
  margin-bottom: 0.5rem;
}

.hp-bar-mini {
  width: 100%;
  height: 6px;
  background: rgba(15, 23, 42, 0.9);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.5);
}

.hp-fill-mini {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.hp-text-mini {
  margin-top: 2px;
  font-size: 0.75rem;
  color: #e5e7eb;
}

.unit-spawn-panel {
  margin-top: 0.25rem;
}

.unit-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.3rem;
}

.unit-btn-mini {
  flex: 1 1 45%;
  padding: 0.25rem 0.3rem;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(15, 23, 42, 0.9);
  color: #e5e7eb;
  font-size: 0.7rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  align-items: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.unit-btn-mini.selected {
  border-color: rgba(59, 130, 246, 0.9);
  background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.4), transparent),
              rgba(15, 23, 42, 0.95);
}

.unit-icon-mini {
  display: block;
  margin: 0 auto;
  flex-shrink: 0;
}

.unit-name-mini {
  font-weight: 500;
}

.unit-cost-mini {
  font-size: 0.7rem;
  color: #facc15;
}

.spawn-btn-mini {
  width: 100%;
  padding: 0.35rem 0.4rem;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #f9fafb;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.spawn-btn-mini:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spawn-btn-mini:not(:disabled):hover {
  filter: brightness(1.05);
}

.messages-container {
  flex: 1;
  padding: 1rem 1.5rem;
  overflow-y: auto;
  background: transparent;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 允许收缩 */
  min-height: 0;
  position: relative;
  z-index: 1;
  /* 允许聊天消息文字选择 */
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}

/* 美化滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 8px; /* 滚动条宽度 */
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05); /* 滚动条轨道背景 */
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2); /* 滚动条滑块背景 */
  border-radius: 4px;
  transition: background 0.2s ease;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3); /* 悬停时更亮 */
}

/* Firefox 滚动条样式 */
.messages-container {
  scrollbar-width: thin; /* Firefox: thin, auto, none */
  scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05); /* Firefox: thumb track */
}

.message {
  margin-bottom: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 18px;
  max-width: 70%;
  word-wrap: break-word;
  position: relative;
  /* 允许消息文字选择 */
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}

.own-message {
  background: #000000;
  color: white;
  margin-left: auto;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  border-bottom-right-radius: 4px;
}

.other-message {
  background: #ffffff;
  color: #000000;
  border: var(--px-border, 3px) solid #000000;
  margin-right: auto;
  border-radius: var(--px-border-radius, 15px);
  border-bottom-left-radius: 4px;
}

.message.grouped {
  margin-top: 0.25rem;
}

.message.grouped.own-message {
  border-top-right-radius: 4px;
}

.message.grouped.other-message {
  border-top-left-radius: 4px;
}

.message-header {
  margin-bottom: 0.25rem;
  font-size: 0.8rem;
  opacity: 0.7;
}

.own-message .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.other-message .message-header {
  color: rgba(0, 0, 0, 0.6);
}

.username {
  font-weight: 600;
}

.message-content {
  line-height: 1.4;
}

/* 输入区域包装器（无背景，只负责布局） */
.input-wrapper {
  display: flex;
  gap: 8px; /* 与其他气泡间距保持一致 */
  flex-shrink: 0; /* 防止被压缩 */
  width: 100%;
  box-sizing: border-box;
  align-items: stretch; /* 确保输入框和按钮高度一致 */
}

/* 音乐容器（头部） */
.music-container-header {
  position: relative;
  display: flex;
  align-items: center;
}

/* 音乐选择菜单（头部位置） */
.music-menu-header-position {
  position: fixed;
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  z-index: 2000;
  min-width: 200px;
  max-width: 300px;
  animation: slideDown 0.2s ease-out;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.music-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #000000;
  color: #000000;
  font-weight: 600;
}

.music-list {
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 音乐列表滚动条美化 - WebKit浏览器（Chrome, Safari, Edge） */
.music-list::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}

.music-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05); /* 滚动条轨道背景 */
  border-radius: 3px;
  margin: 0.5rem 0; /* 上下留出一些空间 */
}

.music-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2); /* 滚动条滑块背景 */
  border-radius: 3px;
  transition: background 0.2s ease;
}

.music-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3); /* 悬停时更亮 */
}

.music-list::-webkit-scrollbar-thumb:active {
  background: rgba(0, 0, 0, 0.4); /* 点击时更亮 */
}

/* Firefox 滚动条样式 */
.music-list {
  scrollbar-width: thin; /* Firefox: thin, auto, none */
  scrollbar-color: rgba(0, 0, 0, 0.2) rgba(0, 0, 0, 0.05); /* Firefox: thumb track */
}

.music-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #000000;
  border-bottom: 1px solid #000000;
}

.music-item:last-child {
  border-bottom: none;
}

.music-item:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #000000;
}

.music-name {
  font-weight: 500;
}

/* 移动端键盘弹起时的输入框样式 */
.input-wrapper.keyboard-open {
  /* 保持正常的 flex 布局，不使用 fixed 定位 */
  padding: 0;
  background: transparent; /* 确保没有背景色 */
  /* 确保保留原有的 flex 布局属性 */
  display: flex;
  gap: 8px;
  align-items: stretch;
  width: 100%;
  box-sizing: border-box;
}

.message-input {
  flex: 1;
  min-width: 0; /* 允许输入框在小屏幕上收缩，避免挤出发送按钮 */
  padding: 0.75rem 1rem;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  font-size: 1rem;
  outline: none;
  transition: all 0.25s ease;
  background: #ffffff;
  color: #000000;
  box-sizing: border-box;
}

.message-input:focus {
  background: #ffffff;
  border-color: #000000;
}

.message-input:disabled {
  background: #ffffff;
  cursor: not-allowed;
  opacity: 0.5;
}

.message-input::placeholder {
  color: rgba(0, 0, 0, 0.5);
}

.send-btn {
  flex-shrink: 0;
  padding: 0.75rem 1.5rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.25s ease;
  box-sizing: border-box;
  white-space: nowrap;
  min-width: fit-content; /* 确保按钮有足够宽度显示文字 */
}

.send-btn:hover:not(:disabled) {
  background: #000000;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

/* 未选择房间时的提示样式 */
.no-room-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: transparent;
}

.welcome-content {
  text-align: center;
  padding: 2rem;
  max-width: 500px;
}

.welcome-content h3 {
  color: #000000;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.welcome-content p {
  color: #000000;
  margin-bottom: 2rem;
  font-size: 1rem;
  line-height: 1.5;
}

.room-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.quick-room-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.quick-room-btn:hover {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

/* 中等宽度屏幕响应式设计 */
@media (min-width: 769px) and (max-width: 1024px) {
  .input-wrapper {
    gap: 8px;
    width: 100%;
    display: flex;
    align-items: stretch;
  }

  .message-input {
    flex: 1;
    min-width: 0;
    padding: 0.625rem 0.875rem;
    font-size: 0.95rem;
  }

  .send-btn {
    flex-shrink: 0;
    padding: 0.625rem 1.25rem;
    font-size: 0.95rem;
    min-width: fit-content;
  }

  .chat-header {
    padding: 0.875rem 1.25rem;
  }

  .chat-header h2 {
    font-size: 1.3rem;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-container {
    position: relative;
    height: 100vh;
    height: 100dvh; /* 移动端使用动态视口高度 */
    overflow: hidden;
    padding: 20px; /* 保持20px间距 */
    gap: 8px;
  }

  .right-chat {
    width: 100%;
    min-height: 0;
    gap: 8px; /* 保持气泡间距 */
  }

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

  .left-sidebar {
    width: 280px; /* 移动端导航栏宽度 */
    border-radius: 12px; /* 保持圆角 */
  }

  /* 确保移动端用户区域正确显示 */
  .user-section {
    padding: 0.75rem 1rem;
    margin-top: auto; /* 确保用户区域在底部 */
  }

  .user-info {
    margin-bottom: 0.75rem;
  }

  .logout-btn {
    font-size: 0.9rem;
    padding: 0.6rem 0.75rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .chat-header {
    padding: 1rem;
    border-radius: 12px; /* 保持圆角 */
  }

  .chat-header h2 {
    font-size: 1.2rem;
  }

  .menu-btn {
    width: 36px;
    height: 36px;
  }

  .menu-btn svg {
    width: 18px;
    height: 18px;
  }

  .welcome-content {
    padding: 1rem;
  }

  .welcome-content h3 {
    font-size: 1.2rem;
  }

  .room-buttons {
    grid-template-columns: repeat(2, 1fr);
  }

  .message {
    max-width: 85%;
  }

  .input-wrapper {
    gap: 8px; /* 与其他气泡间距保持一致 */
    width: 100%;
    display: flex;
    align-items: stretch; /* 确保输入框和按钮高度一致 */
  }

  .message-input {
    flex: 1;
    min-width: 0; /* 允许收缩 */
    padding: 0.75rem 1rem;
    font-size: 1rem;
  }

  .send-btn {
    flex-shrink: 0;
    padding: 0.75rem 1rem; /* 移动端减小左右padding */
    font-size: 1rem;
    min-width: 60px; /* 确保按钮有最小宽度 */
  }

  .chat-main {
    border-radius: 12px; /* 保持圆角 */
  }

  /* 移动端键盘弹起时调整输入框样式 */
  .input-wrapper.keyboard-open {
    /* 保持正常的 flex 布局，不使用 fixed 定位 */
    padding: 0;
    margin: 0;
    /* 确保保留原有的 flex 布局属性 */
    display: flex;
    gap: 8px;
    align-items: stretch;
    width: 100%;
    box-sizing: border-box;
  }

  /* 确保移动端消息容器正确滚动 */
  .messages-container {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch; /* iOS平滑滚动 */
  }

  /* 移动端：当有画图面板时，消息容器需要固定高度 */
  .room-content.with-drawing .messages-container {
    flex: none;
    height: 40%;
  }

  .connection-status {
    font-size: 0.8rem;
  }

  .reconnect-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }

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

/* 音乐图标按钮 */
.music-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #ffffff;
  color: #000000;
  border: var(--px-border, 3px) solid #000000;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.music-icon-btn:hover:not(:disabled) {
  background: #ffffff;
}

.music-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #ffffff;
}

.music-icon {
  position: relative;
  z-index: 2;
}

.music-icon svg {
  stroke: currentColor;
}

.music-icon-btn.playing .music-icon svg {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 画图按钮样式 */
.drawing-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #ffffff;
  color: #000000;
  border: var(--px-border, 3px) solid #000000;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-right: 0.5rem;
}

.drawing-icon-btn:hover:not(:disabled) {
  background: #ffffff;
}

.drawing-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #ffffff;
}

.drawing-icon-btn.active {
  background: #ffffff;
}

/* 画图面板样式已在上面定义 */

.drawing-header {
  padding: 1rem 1.5rem; /* 与chat-header的padding保持一致 */
  background: #ffffff;
  border-bottom: 1px solid #000000;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  box-sizing: border-box;
  /* 与chat-header和logo-section高度保持一致：统一设置为65px */
  height: 65px;
}

.drawing-status {
  flex: 1;
}

.drawer-info {
  color: #000000;
  font-weight: 500;
  font-size: 0.9rem;
}

.drawing-controls {
  display: flex;
  gap: 0.5rem;
}

.drawing-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.25s ease;
}

.request-btn {
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
}

.request-btn:hover:not(:disabled) {
  background: #000000;
}

.clear-btn {
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
}

.clear-btn:hover:not(:disabled) {
  background: #000000;
}

.stop-btn {
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
}

.stop-btn:hover:not(:disabled) {
  background: #000000;
}

.approve-btn {
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
}

.approve-btn:hover:not(:disabled) {
  background: #000000;
}

.drawing-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.drawer-timer {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 0.5rem;
}

/* 申请画画消息的内联同意按钮 */
.drawing-request-action {
  margin-top: 0.5rem;
  display: flex;
  justify-content: flex-start;
}

.approve-btn-inline {
  padding: 0.4rem 1rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.approve-btn-inline:hover:not(:disabled) {
  background: #000000;
}

.approve-btn-inline:active:not(:disabled) {
  background: #000000;
}

.approve-btn-inline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

.drawing-tools {
  padding: 0.75rem 1rem;
  background: #ffffff;
  border-bottom: 1px solid #000000;
  display: flex;
  gap: 1.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.color-picker,
.line-width-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.color-picker span,
.line-width-picker span {
  color: #000000;
  font-size: 0.9rem;
}

.color-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%; /* 圆形，更像调色盘 */
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 添加阴影，增加立体感 */
  position: relative;
}

.color-btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  pointer-events: none;
}

.color-btn:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.color-btn.active {
  transform: scale(1.2);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.6), 0 4px 8px rgba(0, 0, 0, 0.3);
}

.color-btn.active::after {
  border-color: rgba(255, 255, 255, 0.8);
  border-width: 2.5px;
}

.eraser-btn {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border-radius: 50%; /* 圆形 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.eraser-btn::after {
  display: none; /* 橡皮擦不需要内圈 */
}

.eraser-btn:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.eraser-btn.active {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%) !important;
  transform: scale(1.2);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.6), 0 4px 8px rgba(0, 0, 0, 0.3);
}

.width-btn {
  padding: 0.4rem 0.75rem;
  background: #ffffff;
  color: #000000;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.width-btn:hover {
  background: #ffffff;
  border-color: #000000;
}

.width-btn.active {
  background: #000000;
  border-color: #000000;
  color: white;
}

.drawing-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3); /* 不可绘制区域背景（PC端） */
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 确保容器本身也保持4:3比例，但不超过可用空间 */
  width: 100%;
  max-width: 100%;
  max-height: 100%;
  /* 使用aspect-ratio保持4:3比例，同时确保在可见区域内 */
  aspect-ratio: 4 / 3;
  /* 确保容器不会超出父容器 */
  box-sizing: border-box;
}

/* 确保canvas-wrapper和drawing-canvas完全在drawing-container内 */
.drawing-container .canvas-wrapper,
.drawing-container .drawing-canvas {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
}

/* 移动端画布容器 */
@media (max-width: 768px) {
  .drawing-container {
    background: transparent; /* 移动端无背景 */
    padding: 0; /* 移动端无padding */
    width: 100%; /* 占满宽度 */
    flex: 0 0 auto; /* 不自动伸缩，根据aspect-ratio计算高度 */
    min-height: 0; /* 允许收缩 */
    overflow: hidden; /* 防止溢出 */
    display: flex; /* 使用flex布局 */
    align-items: center; /* 垂直居中 */
    justify-content: center; /* 水平居中 */
    /* 移动端也保持4:3比例，但确保在可见区域内 */
    aspect-ratio: 4 / 3;
    max-height: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }

  .drawing-canvas {
    /* 移动端：width和height由JavaScript动态设置，确保完整显示 */
    max-width: 100% !important;
    max-height: 100% !important; /* 限制最大高度，防止超出容器 */
  }
}

.canvas-wrapper {
  position: relative;
  background: white; /* 可绘制区域背景 */
  border: 2px solid rgba(255, 255, 255, 0.3); /* 可绘制区域边框 */
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px; /* PC端至少5px的padding */
  /* 保持4:3比例，考虑padding，但不超过容器 */
  aspect-ratio: 4 / 3;
  width: calc(100% - 10px); /* 减去左右padding */
  max-width: calc(100% - 10px);
  max-height: calc(100% - 10px);
  box-sizing: border-box;
  /* 确保不超出drawing-container */
  overflow: hidden;
}

.drawing-canvas {
  position: relative;
  display: block;
  cursor: crosshair;
  touch-action: none;
  /* 保持4:3比例，但不超过容器 */
  aspect-ratio: 4 / 3;
  /* width和height由JavaScript动态设置，确保在所有设备上都能完整显示 */
  max-width: 100%;
  max-height: 100%;
  background: white; /* 画布白色背景 */
  box-sizing: border-box;
  /* 固定逻辑尺寸800x600，JavaScript会根据容器大小计算合适的显示尺寸 */
  /* 使用contain策略，确保画布内容不被裁剪 */
}

/* 移动端画图面板样式 */
@media (max-width: 768px) {
  /* 移动端：隐藏中间画布区域，画布在右侧聊天区域内 */
  .drawing-area {
    display: none;
  }

  /* 移动端：右侧聊天区域恢复全宽 */
  .right-chat.with-drawing {
    flex: 1;
  }

  /* 移动端：在右侧聊天区域内，画布和消息列表纵向排列 */
  .right-chat.with-drawing .chat-main {
    display: flex;
    flex-direction: column;
    min-height: 0; /* 允许收缩 */
    overflow: hidden; /* 防止整体溢出 */
  }

  .right-chat.with-drawing .mobile-drawing-panel {
    flex: 0 0 auto; /* 不自动伸缩，根据内容计算高度 */
    min-height: 0;
    border: none; /* 在气泡容器内，不需要边框 */
    border-bottom: 1px solid #000000;
    border-radius: 0; /* 在气泡容器内，不需要圆角 */
    display: flex;
    flex-direction: column;
    overflow: visible; /* 允许内容显示 */
    background: transparent; /* 使用父容器背景 */
  }

  /* 移动端：确保drawing-container保持4:3比例，但允许在flex布局中正确显示 */
  .right-chat.with-drawing .mobile-drawing-panel .drawing-container {
    flex: 0 0 auto; /* 根据aspect-ratio自动计算高度，不伸缩 */
    width: 100%;
    /* 确保画布不会超出可见区域 */
    max-width: 100%;
    /* 不设置max-height，让aspect-ratio自然计算高度 */
  }

  /* 移动端：确保header、tools不占用过多空间 */
  .mobile-drawing-panel .drawing-header,
  .mobile-drawing-panel .drawing-tools {
    flex-shrink: 0; /* 不收缩，保持内容高度 */
  }

  .right-chat.with-drawing .messages-container {
    flex: 1; /* 自适应高度，占用剩余空间 */
    min-height: 0; /* 允许收缩 */
    max-height: none; /* 不限制最大高度，让画布优先 */
    overflow-y: auto; /* 允许滚动 */
  }

  .drawing-header {
    padding: 0.75rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    height: auto; /* 移动端取消固定高度，让内容自然撑开 */
    min-height: 65px; /* 保持最小高度 */
  }

  .drawing-status {
    width: 100%;
  }

  .drawing-controls {
    width: 100%;
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .drawing-btn {
    flex: 1;
    padding: 0.6rem 0.75rem;
    font-size: 0.85rem;
  }

  .drawing-tools {
    padding: 0.5rem 0.75rem;
    gap: 1rem;
  }

  .color-picker,
  .line-width-picker {
    flex-wrap: wrap;
  }
}

</style>
