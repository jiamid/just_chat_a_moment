<template>
  <div class="chat-container">
    <!-- 皇室战争风格背景 -->
    <ClashBackground />
    <!-- 移动端遮罩层 -->
    <div
      v-if="isMobile && showMobileNavbar"
      class="mobile-overlay"
      @click="hideMobileNavbar"
    ></div>

    <!-- 左侧导航栏 -->
    <div class="left-sidebar" :class="{
      'mobile-show': showMobileNavbar && isMobile
    }" v-show="!sidebarCollapsed || isMobile">

      <!-- 完整内容 -->
      <div class="sidebar-content">
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
      <GamePanel
        :gameState="gameState"
        :gameOverInfo="gameOverInfo"
        :isConnected="isConnected"
        :unitTypesConfig="unitTypesConfig"
        @join-game="joinGame"
        @leave-game="leaveGame"
        @select-and-spawn-unit="selectAndSpawnUnit"
      />
    </div>

    <!-- 中间画布区域（仅在画图面板打开时显示，桌面端，且不在游戏模式） -->
    <div v-if="showDrawingPanel && roomId && !isMobile && !showGamePanel" class="drawing-area">
      <DrawingPanel
        :currentDrawer="currentDrawer"
        :username="username"
        :isConnected="isConnected"
        :isMobile="isMobile"
        :drawerTimeRemaining="drawerTimeRemaining"
        :roomId="roomId"
        :ChatMessage="ChatMessage"
        :WsEnvelope="WsEnvelope"
        :ws="ws"
      />
    </div>

    <!-- 右侧聊天区域 -->
    <div class="right-chat" :class="{
      'with-drawing': showDrawingPanel && roomId && !showGamePanel,
      'with-game': showGamePanel && roomId
    }">
      <!-- 顶部：房间信息 -->
      <div class="chat-header">
        <div class="header-left">
          <!-- 菜单按钮（桌面端和移动端都显示） -->
          <button @click="isMobile ? toggleMobileNavbar() : toggleSidebar()" class="menu-btn">
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
            <h3>欢迎进入 Just Chat A Moment</h3>
            <p>请从左侧选择一个房间开始聊天，或者输入自定义房间号</p>
          </div>
        </div>

        <!-- 已选择房间时的内容 -->
        <template v-else>
          <!-- 移动端游戏面板（桌面端游戏面板在中间区域） -->
          <div v-if="showGamePanel && isMobile" class="game-panel-mobile">
            <GamePanel
              :gameState="gameState"
              :gameOverInfo="gameOverInfo"
              :isConnected="isConnected"
              :unitTypesConfig="unitTypesConfig"
              @join-game="joinGame"
              @leave-game="leaveGame"
              @select-and-spawn-unit="selectAndSpawnUnit"
            />
          </div>

          <div v-if="showDrawingPanel && isMobile" class="drawing-panel mobile-drawing-panel">
            <DrawingPanel
              :currentDrawer="currentDrawer"
              :username="username"
              :isConnected="isConnected"
              :isMobile="isMobile"
              :drawerTimeRemaining="drawerTimeRemaining"
              :roomId="roomId"
              :ChatMessage="ChatMessage"
              :WsEnvelope="WsEnvelope"
              :ws="ws"
            />
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
import ClashBackground from '@/components/ClashBackground.vue'
import GamePanel from '@/components/GamePanel.vue'
import DrawingPanel from '@/components/DrawingPanel.vue'

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
    ClashBackground,
    GamePanel,
    DrawingPanel
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
            // 过滤掉用户进入和退出房间的提醒
            const content = message.content || ''
            const isJoinLeaveMessage = /(进入|退出|加入|离开)房间/.test(content)
            if (!isJoinLeaveMessage) {
              this.showSystemMessage(content)
            }
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

    selectAndSpawnUnit (unitTypeKey) {
      if (!this.isConnected || !this.WsEnvelope || !this.GameMessage) return
      try {
        // 先选择单位类型
        const selectMsg = this.GameMessage.create({
          type: this.GameMessage.Type.SELECT_UNIT,
          select_unit: { unit_type: unitTypeKey }
        })
        const selectEnv = this.WsEnvelope.create({ game: selectMsg })
        const selectBuf = this.WsEnvelope.encode(selectEnv).finish()
        this.ws.send(selectBuf)

        // 然后立即生成
        const spawnMsg = this.GameMessage.create({
          type: this.GameMessage.Type.SPAWN_UNIT,
          spawn_unit: {}
        })
        const spawnEnv = this.WsEnvelope.create({ game: spawnMsg })
        const spawnBuf = this.WsEnvelope.encode(spawnEnv).finish()
        this.ws.send(spawnBuf)
      } catch (e) {
        console.error('selectAndSpawnUnit failed', e)
      }
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
  padding: 5.5em; /* 为所有区域留出20px间距 */
  box-sizing: border-box;
  gap: 8px; /* 区域之间的间距 */
}

/* 左侧导航栏 */
.left-sidebar {
  width: 250px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  display: flex;
  flex-direction: column;
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  transition: width 0.3s ease, transform 0.3s ease;
  z-index: 1000;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
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
    top: 0.5em;
    bottom: 0.5em;
    left: -8px;
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
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
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
  color: #2C3E50;
  font-size: 1.5rem;
  font-weight: 900;
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
  text-shadow: 0 1px 2px rgb(255, 255, 255);
}

.logo-section:hover .logo-text {
  /* hover 状态：简单的颜色变化 */
  color: #4A90E2;
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
  color: #2C3E50;
  font-weight: 700;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
}

.room-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.room-item {
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 3px solid rgba(200, 200, 200, 0.6);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  color: #2C3E50;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgb(255, 255, 255);
}

.room-item:hover {
  border-color: #4A90E2;
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.2),
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgb(255, 255, 255);
}

.room-item.active {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: #ffffff;
  border-color: rgb(255, 255, 255);
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.room-name {
  font-weight: 500;
}

.room-jump {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(200, 200, 200, 0.3);
}

.room-jump h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #2C3E50;
  font-weight: 700;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
}

.jump-input-group {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 3px solid rgba(200, 200, 200, 0.6);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgb(255, 255, 255);
}

.jump-input {
  flex: 1;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  color: #2C3E50;
  font-size: 1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  text-align: center;
  min-width: 0;
}

.jump-input::placeholder {
  color: rgba(127, 140, 141, 0.6);
  font-weight: 500;
}

.jump-input:focus {
  background: transparent;
}

.jump-btn {
  flex: 1;
  padding: 0;
  background: transparent;
  color: #4A90E2;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  min-width: 40px;
  max-width: 60px;
  flex-shrink: 0;
}

.jump-btn:hover {
  color: #357ABD;
  transform: scale(1.05);
}

.user-section {
  padding: 1rem;
  border-top: 1px solid rgba(200, 200, 200, 0.3);
  flex-shrink: 0; /* 防止用户区域被压缩 */
}

.user-info {
  margin-bottom: 1rem;
}

.user-info .username {
  font-weight: 700;
  color: #2C3E50;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
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
  color: #2C3E50;
  font-weight: 500;
}

.connection-status-navbar .status-text.connecting {
  color: #7F8C8D;
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
  background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
  color: white;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 16px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 4px 8px rgba(231, 76, 60, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.logout-btn:hover {
  background: linear-gradient(135deg, #EC7063 0%, #E74C3C 100%);
  transform: translateY(-2px);
  box-shadow:
    0 6px 12px rgba(231, 76, 60, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

/* 中间画布区域 */
.drawing-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0; /* 允许收缩 */
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  /* 确保画布区域始终在可见区域内 */
  max-height: 100vh;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

/* 中间游戏区域（类似 drawing-area） */
.game-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0; /* 允许收缩 */
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  /* 确保游戏区域始终在可见区域内 */
  max-height: 100vh;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  padding: 1rem 1.5rem;
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
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
  backdrop-filter: blur(10px);
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
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: white;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-btn:hover {
  background: linear-gradient(135deg, #5B9BD5 0%, #4A90E2 100%);
  transform: translateY(-2px);
}

.menu-btn svg {
  stroke: currentColor;
}

.chat-header h2 {
  margin: 0;
  color: #2C3E50;
  font-size: 1.5rem;
  line-height: 1.2; /* 明确设置line-height，确保高度计算准确 */
  font-weight: 700;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
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
  color: #2C3E50;
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  position: relative;
  backdrop-filter: blur(10px);
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
  border: none;
  overflow: hidden;
  min-width: 0;
  min-height: 0;
  border-radius: 0; /* 画图面板在气泡容器内，不需要额外圆角 */
}

.messages-container {
  flex: 1;
  padding: 1rem;
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
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: white;
  margin-left: auto;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 18px;
  border-bottom-right-radius: 4px;
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.other-message {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  border: 3px solid rgba(200, 200, 200, 0.6);
  margin-right: auto;
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgb(255, 255, 255);
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
  color: rgba(255, 255, 255, 0.9);
}

.other-message .message-header {
  color: rgba(44, 62, 80, 0.7);
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.95) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  z-index: 2000;
  min-width: 200px;
  max-width: 300px;
  animation: slideDown 0.2s ease-out;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
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
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
  color: #2C3E50;
  font-weight: 700;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
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
  color: #2C3E50;
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
}

.music-item:last-child {
  border-bottom: none;
}

.music-item:hover {
  background: rgba(74, 144, 226, 0.1);
  color: #357ABD;
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
  border: 4px solid rgb(255, 255, 255);
  border-radius: 16px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  box-sizing: border-box;
  backdrop-filter: blur(10px);
}

.message-input:disabled {
  background: rgba(245, 245, 245, 0.8);
  cursor: not-allowed;
  opacity: 0.6;
}

.message-input::placeholder {
  color: rgba(127, 140, 141, 0.6);
}

.send-btn {
  flex-shrink: 0;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: white;
  border: 4px solid rgb(255, 255, 255);
  border-radius: 16px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  white-space: nowrap;
  min-width: fit-content; /* 确保按钮有足够宽度显示文字 */
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5B9BD5 0%, #4A90E2 100%);
  transform: translateY(-2px);
}

.send-btn:disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #CCCCCC 0%, #999999 100%);
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
  color: #2C3E50;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
}

.welcome-content p {
  color: #7F8C8D;
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
    padding: 1em; /* 保持20px间距 */
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.music-icon-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0.95) 100%);
  transform: translateY(-2px);
}

.music-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(245, 245, 245, 0.8);
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-right: 0.5rem;
}

.drawing-icon-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0.95) 100%);
  transform: translateY(-2px);
}

.drawing-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(245, 245, 245, 0.8);
}

.drawing-icon-btn.active {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: white;
  border-color: rgb(255, 255, 255);
}

.drawing-icon-btn.active:hover:not(:disabled) {
  background: linear-gradient(135deg, #5B9BD5 0%, #4A90E2 100%);
  color: white;
  transform: translateY(-2px);
}

/* 画图面板样式已在上面定义 */

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
}

</style>
