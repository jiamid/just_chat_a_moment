<template>
  <div class="chat-container">
    <!-- 皇室战争风格背景 -->
    <ClashBackground />
    <!-- 遮罩层（移动端和桌面端共用） -->
    <div
      v-if="(isMobile && showMobileNavbar) || (!isMobile && !sidebarCollapsed)"
      class="mobile-overlay"
      @click="isMobile ? hideMobileNavbar() : toggleSidebar()"
    ></div>

    <!-- 左侧导航栏 -->
    <div class="left-sidebar" :class="{
      'mobile-show': (showMobileNavbar && isMobile) || (!sidebarCollapsed && !isMobile),
      'desktop-show': !sidebarCollapsed && !isMobile
    }">

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
          <button @click="goToHome" class="logout-btn">返回大厅</button>
        </div>
      </div>
    </div>

    <!-- 中间棋盘区域（桌面端显示） -->
    <div v-if="roomId && !isMobile" class="game-area">
      <div class="gobang-panel-desktop">
        <GobangBoard
          :board="board"
          :role="role"
          :started="started"
          :currentTurn="currentTurn"
          :finished="finished"
          :winner="winner"
          @cell-click="handleCellClick"
        />
        <!-- 加入对局按钮：仅在对局未开始或已结束时显示 -->
        <div v-if="!started || finished" class="gobang-join-container">
          <button
            class="gobang-join-btn pixel-text"
            :class="{'joined': hasJoinedQueue }"
            :disabled="!isConnected || finished"
            @click="hasJoinedQueue && !finished ? leaveGame() : joinGame()"
          >
            {{ !finished && hasJoinedQueue ? '退出对局' : '加入对局' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="right-chat" :class="{
      'with-game': roomId
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
          <!-- 移动端：在聊天区域内显示棋盘（位置对应 LiveWar 的游戏按钮） -->
          <button
            v-if="isMobile"
            @click="showMobileBoard = !showMobileBoard"
            :disabled="!isConnected"
            class="drawing-icon-btn"
            :class="{ 'active': showMobileBoard }"
            title="显示/隐藏棋盘"
          >
            ♟
          </button>
          <!-- 音乐选择按钮 -->
          <div class="music-container-header">
            <button
              ref="musicButton"
              @click="toggleMusicMenu"
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
            <div v-if="showMusicMenu" class="music-menu music-menu-header-position" @click.stop>
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

      <!-- 中间：棋盘（移动端） + 消息区域 -->
      <div class="chat-main" @click="hideMobileNavbar(); hideMusicMenu()">
        <!-- 未选择房间时的提示 -->
        <div v-if="!roomId" class="no-room-message">
          <div class="welcome-content">
            <h3>欢迎进入五子棋房间</h3>
            <p>请从左侧选择一个房间开始对战，或者输入自定义房间号</p>
          </div>
        </div>

        <!-- 已选择房间时的内容 -->
        <template v-else>
          <!-- 移动端：棋盘（消息和输入在底部 chat-bottom-panel 中） -->
          <div v-if="isMobile && showMobileBoard" class="mobile-board-with-chat">
            <div class="game-panel-mobile">
              <GobangBoard
                :board="board"
                :role="role"
                :started="started"
                :currentTurn="currentTurn"
                :finished="finished"
                :winner="winner"
                @cell-click="handleCellClick"
              />
              <!-- 加入对局按钮：仅在对局未开始或已结束时显示（与桌面端一致） -->
              <div v-if="!started || finished" class="gobang-join-container">
                <button
                  class="gobang-join-btn pixel-text"
                  :class="{'joined': hasJoinedQueue }"
                  :disabled="!isConnected || finished"
                  @click="hasJoinedQueue && !finished ? leaveGame() : joinGame()"
                >
                  {{ !finished && hasJoinedQueue ? '退出对局' : '加入对局' }}
                </button>
              </div>
            </div>
            <!-- 棋盘下方空闲区域显示聊天 -->
            <div class="messages-container messages-below-board" ref="messagesContainer">
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
              </div>
            </div>
          </div>

          <!-- 消息列表：非移动端棋盘模式时显示（桌面端或移动端未展开棋盘时） -->
          <div
            v-else
            class="messages-container"
            ref="messagesContainer"
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
            </div>
          </div>
        </template>
      </div>

      <!-- 底部：输入区域（移动端棋盘模式下也显示，便于在棋盘下方聊天） -->
      <div class="input-wrapper" v-if="roomId" :class="{
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
import ClashBackground from '@/components/ClashBackground.vue'
import GobangBoard from '@/components/GobangBoard.vue'

// 与后端约定的五子棋消息类型（ChatMessage.type 数值）
const GOBANG_STATE_TYPE = 20
const GOBANG_MOVE_TYPE = 21
const GOBANG_JOIN_TYPE = 22
const GOBANG_LEAVE_TYPE = 23

export default {
  name: 'GobangRoom',
  components: {
    ClashBackground,
    GobangBoard
  },
  data () {
    return {
      roomType: 'gobang', // 房间类型
      username: '',
      roomId: null,
      messages: [],
      newMessage: '',
      ws: null,
      isConnected: false,
      hasEverConnected: false, // 是否曾经连接成功过
      ChatMessage: null,
      MessageType: null,
      WsEnvelope: null,
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
      sidebarCollapsed: true, // 左侧菜单折叠状态（默认隐藏）
      musicConfig: {},
      showMusicMenu: false,
      isPlaying: false,
      currentMusicId: null,
      // 音频解锁相关状态
      audioUnlocked: false,
      audioContext: null,
      audioElement: null,
      musicMenuStyle: {},

      // 五子棋状态
      board: Array.from({ length: 15 }, () => Array(15).fill(0)),
      role: 'spectator', // 'black' | 'white' | 'waiting_player' | 'spectator'
      currentTurn: 1,
      finished: false,
      winner: '', // 'black' | 'white' | ''

      // 移动端棋盘显示控制
      showMobileBoard: true,
      // 对局是否已开始（由服务端状态决定）
      started: false,
      // 是否已点击加入对局（用于未开局前显示“退出对局”）
      hasJoinedQueue: false
    }
  },
  computed: {
    currentRoomId () {
      return this.$route.params.roomId ? parseInt(this.$route.params.roomId) : null
    }
  },
  async mounted () {
    this.roomId = this.currentRoomId
    this.loadRecentRooms()
    this.checkMobileDevice()
    this.setupKeyboardDetection()
    this.initAudio()
    await this.loadUserInfo()
    await this.loadProtobuf()
    if (this.roomId) {
      await this.loadMusicConfig()
      this.connectWebSocket()
    }
  },
  watch: {
    async '$route.params.roomId' (newRoomId) {
      const roomId = newRoomId ? parseInt(newRoomId) : null
      if (roomId !== this.roomId) {
        this.roomId = roomId
        this.messages = [] // 清空消息
        this.currentRoomCount = 0 // 重置房间人数
        // 重置棋盘状态
        this.board = Array.from({ length: 15 }, () => Array(15).fill(0))
        this.role = 'spectator'
        this.currentTurn = 1
        this.finished = false
        this.winner = ''
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
    // 初始化音频系统（复用 ChatRoom / DrawingRoom 中的逻辑）
    initAudio () {
      try {
        this.audioElement = document.createElement('audio')
        this.audioElement.setAttribute('playsinline', 'true')
        this.audioElement.setAttribute('preload', 'auto')
        document.body.appendChild(this.audioElement)

        if (window.AudioContext || window.webkitAudioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        }

        this.addAudioUnlockListeners()
      } catch (err) {
        console.error('音频系统初始化失败:', err)
      }
    },
    addAudioUnlockListeners () {
      const unlockAudio = () => {
        if (!this.audioUnlocked) {
          this.unlockAudio()
        }
      }
      window.addEventListener('touchstart', unlockAudio, { once: true })
      window.addEventListener('click', unlockAudio, { once: true })
      window.addEventListener('keydown', unlockAudio, { once: true })
    },
    unlockAudio () {
      if (!this.audioUnlocked) {
        try {
          if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume()
          }
          if (this.audioElement) {
            this.audioElement.play().catch(() => {})
          }
          this.audioUnlocked = true
        } catch (err) {
          console.error('音频解锁失败:', err)
        }
      }
    },
    async loadUserInfo () {
      try {
        const response = await api.user.getMe()
        this.username = response.data.username
        localStorage.setItem('username', response.data.username)
      } catch (err) {
        this.$router.push('/login')
      }
    },
    async loadMusicConfig () {
      if (!this.roomId) return
      try {
        const response = await api.music.getConfig(this.roomId)
        this.musicConfig = response.data
      } catch (err) {
        console.error('获取音乐配置失败:', err)
      }
    },
    async loadProtobuf () {
      try {
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
                    DRAWING_REQUEST_APPROVE: 11,
                    // 新增：五子棋相关消息类型
                    GOBANG_STATE: GOBANG_STATE_TYPE,
                    GOBANG_MOVE: GOBANG_MOVE_TYPE,
                    GOBANG_JOIN: GOBANG_JOIN_TYPE
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
            // 为了兼容 WsEnvelope 的结构，简要定义 livewar.GameMessage
            livewar: {
              nested: {
                GameMessage: {
                  fields: {
                    type: { type: 'Type', id: 1 }
                  },
                  nested: {
                    Type: {
                      values: {
                        UNKNOWN: 0
                      }
                    }
                  }
                }
              }
            }
          }
        })
        this.ChatMessage = root.lookupType('chat.ChatMessage')
        this.MessageType = root.lookupEnum('chat.MessageType')
        this.WsEnvelope = root.lookupType('chat.WsEnvelope')
      } catch (err) {
        console.error('Failed to load protobuf for Gobang:', err)
        this.showSystemMessage('Protobuf 加载失败，请刷新页面重试')
      }
    },
    connectWebSocket () {
      const token = localStorage.getItem('token')
      const wsUrl = config.getWsUrl(this.roomType, this.roomId, token)

      this.isConnected = false

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnected = true
        this.hasEverConnected = true
      }

      this.ws.onmessage = async (event) => {
        try {
          if (!this.WsEnvelope || !this.ChatMessage) {
            console.warn('Protobuf types not loaded yet, skipping message')
            return
          }

          let data
          if (event.data instanceof Blob) {
            const arrayBuffer = await event.data.arrayBuffer()
            data = new Uint8Array(arrayBuffer)
          } else {
            data = new Uint8Array(event.data)
          }

          const envelope = this.WsEnvelope.decode(data)

          if (!envelope.chat) {
            return
          }

          const message = envelope.chat

          // 房间人数
          if (message.type === this.MessageType.values.ROOM_COUNT) {
            this.updateRoomCount(message.content)
            return
          }

          // 系统消息
          if (message.type === this.MessageType.values.SYSTEM) {
            const content = message.content || ''
            const isJoinLeaveMessage = /(进入|退出|加入|离开)房间/.test(content)
            if (!isJoinLeaveMessage) {
              this.showSystemMessage(content)
            }
            return
          }

          // 音乐消息
          if (message.type === this.MessageType.values.MUSIC) {
            const musicInfo = this.musicConfig[message.content]
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
            if (this.messages.length > 0) {
              const lastMessage = this.messages[this.messages.length - 1]
              if (lastMessage.user === newMessage.user && lastMessage.isOwn === newMessage.isOwn) {
                newMessage.showHeader = false
              }
            }
            this.messages.push(newMessage)
            if (musicInfo) {
              this.playMusicWithDelay(message.content, message.timestamp)
            }
            this.$nextTick(() => {
              setTimeout(() => {
                this.scrollToBottom()
              }, 100)
            })
            return
          }

          // 五子棋状态更新
          if (message.type === GOBANG_STATE_TYPE) {
            if (message.content) {
              try {
                const state = JSON.parse(message.content)
                if (Array.isArray(state.board)) {
                  this.board = state.board
                }
                if (state.current_turn === 1 || state.current_turn === 2) {
                  this.currentTurn = state.current_turn
                }
                this.finished = !!state.finished
                this.winner = state.winner || ''
                if (state.role) {
                  this.role = state.role
                  // 已加入等待队列时同步 hasJoinedQueue（含重连场景）
                  if (state.role === 'waiting_player') {
                    this.hasJoinedQueue = true
                  }
                }
                if (typeof state.started === 'boolean') {
                  this.started = state.started
                  // 一旦对局开始或已有结果，本地的等待队列标记清空
                  if (this.started || this.finished) {
                    this.hasJoinedQueue = false
                  }
                }
              } catch (e) {
                console.error('解析五子棋状态失败:', e, message.content)
              }
            }
            return
          }

          // 普通用户文本消息
          if (message.type === this.MessageType.values.USER_TEXT) {
            const newMessage = {
              id: Date.now() + Math.random(),
              user: message.user,
              content: message.content,
              timestamp: message.timestamp,
              isOwn: message.user === this.username,
              showHeader: true
            }
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
      }

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        this.isConnected = false
      }
    },
    sendMessage () {
      if (!this.newMessage.trim() || !this.isConnected || !this.ChatMessage) {
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: this.newMessage,
          timestamp: Date.now(),
          type: this.MessageType.values.USER_TEXT
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        this.newMessage = ''
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (err) {
        console.error('Failed to send message:', err)
      }
    },
    handleCellClick ({ x, y }) {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope) return
      if (this.finished) {
        this.showSystemMessage('本局已结束，不能再落子')
        return
      }
      if (!this.started) {
        this.showSystemMessage('对局尚未开始，请先点击“加入对局”')
        return
      }
      if (this.role !== 'black' && this.role !== 'white') {
        this.showSystemMessage('你是观战者，不能落子')
        return
      }
      const meColor = this.role === 'black' ? 1 : 2
      if (this.currentTurn !== meColor) {
        this.showSystemMessage('还没轮到你落子')
        return
      }
      if (this.board[y] && this.board[y][x] !== 0) {
        this.showSystemMessage('该位置已有棋子，请选择其他位置')
        return
      }

      try {
        const payload = JSON.stringify({ x, y })
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: payload,
          timestamp: Date.now(),
          type: GOBANG_MOVE_TYPE
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send gobang move:', err)
      }
    },
    scrollToBottom () {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        })
      }
    },
    goToHome () {
      this.$router.push({
        path: '/',
        query: { returnFromChat: 'true' }
      })
    },
    switchRoom (roomId) {
      if (roomId !== this.roomId) {
        this.currentRoomCount = 0
        this.addToRecentRooms(roomId)
        this.$router.push(`/room/gobang/${roomId}`)
        if (this.isMobile) {
          this.showMobileNavbar = false
        }
      }
    },
    updateRoomCount (content) {
      const match = content.match(/当前房间人数: (\d+)/)
      if (match) {
        const count = parseInt(match[1])
        this.currentRoomCount = count
      }
    },
    showSystemMessage (content) {
      this.systemMessage = content
      this.$nextTick(() => {
        this.updateSystemNotificationStyle()
      })
      setTimeout(() => {
        this.systemMessage = ''
      }, 3000)
    },
    updateSystemNotificationStyle () {
      const messagesContainer = this.$refs.messagesContainer
      if (!messagesContainer) {
        this.systemNotificationStyle = {}
        return
      }
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
      const saved = localStorage.getItem('recentRoomsGobang')
      if (saved) {
        this.recentRooms = JSON.parse(saved)
      } else {
        this.recentRooms = this.availableRooms.slice(0, 5)
      }
    },
    addToRecentRooms (roomId) {
      this.recentRooms = this.recentRooms.filter(room => room.id !== roomId)
      this.recentRooms.unshift({ id: roomId })
      this.recentRooms = this.recentRooms.slice(0, 5)
      localStorage.setItem('recentRoomsGobang', JSON.stringify(this.recentRooms))
    },
    jumpToRoom () {
      const roomId = parseInt(this.jumpRoomId)
      if (roomId && roomId > 0) {
        this.jumpRoomId = ''
        this.addToRecentRooms(roomId)
        this.$router.push(`/room/gobang/${roomId}`)
      }
    },
    filterNumbers (event) {
      const value = event.target.value.replace(/[^0-9]/g, '')
      this.jumpRoomId = value
    },
    checkMobileDevice () {
      this.isMobile = window.innerWidth <= 768
      window.addEventListener('resize', () => {
        this.isMobile = window.innerWidth <= 768
        if (!this.isMobile) {
          this.showMobileNavbar = false
        }
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
      this.initialViewportHeight = Math.max(window.innerHeight, window.screen.height)
      window.addEventListener('resize', this.handleKeyboardToggle)
      if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', this.handleKeyboardToggle)
      }
    },
    handleKeyboardToggle () {
      if (!this.isMobile) return
      const currentHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight
      const heightDifference = this.initialViewportHeight - currentHeight
      if (heightDifference > 100) {
        this.isKeyboardOpen = true
      } else {
        this.isKeyboardOpen = false
      }
    },
    toggleMusicMenu () {
      this.showMusicMenu = !this.showMusicMenu
    },
    hideMusicMenu () {
      this.showMusicMenu = false
    },
    sendMusic (musicId) {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope) {
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: musicId,
          timestamp: Date.now(),
          type: this.MessageType.values.MUSIC
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        this.showMusicMenu = false
      } catch (err) {
        console.error('Failed to send music message:', err)
      }
    },
    cleanupAudio () {
      try {
        if (this.audioElement) {
          this.audioElement.pause()
          this.audioElement.currentTime = 0
          this.audioElement.src = ''
          if (this.audioElement.parentNode) {
            this.audioElement.parentNode.removeChild(this.audioElement)
          }
          this.audioElement = null
        }
        if (this.audioContext) {
          this.audioContext.close()
          this.audioContext = null
        }
        this.isPlaying = false
        this.currentMusicId = null
        this.audioUnlocked = false
      } catch (err) {
        console.error('清理音频资源失败:', err)
      }
    },
    playMusicFromServer (musicUrl, musicId) {
      if (!this.audioUnlocked) {
        console.warn('音频尚未解锁，播放可能会失败')
      }
      if (!musicUrl) {
        console.warn('音乐URL为空，无法播放')
        return
      }
      try {
        this.stopCurrentMusic()
        this.audioElement.src = musicUrl
        this.currentMusicId = musicId
        this.isPlaying = true
        this.setupAudioEventListeners()
        const playPromise = this.audioElement.play()
        if (playPromise !== undefined) {
          playPromise.then(() => {}).catch(err => {
            console.error('音乐播放失败:', err)
            this.stopCurrentMusic()
          })
        }
      } catch (err) {
        console.error('播放音乐时发生错误:', err)
        this.stopCurrentMusic()
      }
    },
    setupAudioEventListeners () {
      if (!this.audioElement) return
      this.removeAudioEventListeners()
      this.audioElement.addEventListener('ended', () => {
        this.stopCurrentMusic()
      })
      this.audioElement.addEventListener('error', (e) => {
        console.error('音乐播放错误:', e)
        this.stopCurrentMusic()
      })
    },
    removeAudioEventListeners () {
      if (!this.audioElement) return
      const events = ['loadstart', 'canplay', 'play', 'ended', 'error']
      events.forEach(event => {
        this.audioElement.removeEventListener(event, () => {})
      })
    },
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
      } catch (err) {
        console.error('停止音乐播放失败:', err)
      }
    },
    playMusicWithDelay (musicId, targetTimestamp) {
      const musicInfo = this.musicConfig[musicId]
      if (!musicInfo || !musicInfo.url) {
        return
      }
      const currentTime = Date.now()
      const delay = targetTimestamp - currentTime
      if (delay <= 0) {
        this.playMusicFromServer(musicInfo.url, musicId)
      } else {
        setTimeout(() => {
          this.playMusicFromServer(musicInfo.url, musicId)
        }, delay)
      }
    },
    playMusic (musicId) {
      const musicInfo = this.musicConfig[musicId]
      if (!musicInfo || !musicInfo.url) {
        return
      }
      this.playMusicFromServer(musicInfo.url, musicId)
    },
    stopMusic () {
      this.stopCurrentMusic()
    },
    // ===== 五子棋：加入对局 =====
    joinGame () {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope) {
        this.showSystemMessage('WebSocket 未连接，无法加入对局')
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: GOBANG_JOIN_TYPE
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        // 本地标记已加入等待队列（在状态同步前用于切换为“退出对局”按钮）
        this.hasJoinedQueue = true
      } catch (err) {
        console.error('Failed to send gobang join:', err)
        this.showSystemMessage('加入对局失败')
      }
    },
    // ===== 五子棋：退出对局等待队列 =====
    leaveGame () {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope) {
        this.showSystemMessage('WebSocket 未连接，无法退出对局')
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: GOBANG_LEAVE_TYPE
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        // 本地立即重置等待标记
        this.hasJoinedQueue = false
      } catch (err) {
        console.error('Failed to send gobang leave:', err)
        this.showSystemMessage('退出对局失败')
      }
    }
  },
  beforeUnmount () {
    if (this.ws) {
      this.ws.close()
    }
    this.cleanupAudio()
    window.removeEventListener('resize', this.checkMobileDevice)
    window.removeEventListener('resize', this.handleKeyboardToggle)
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', this.handleKeyboardToggle)
    }
  }
}
</script>

<style>
/* 复用其它房间的全局防滚动样式 */
html, body {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
  background: transparent;
}

#app {
  height: 100%;
  overflow: hidden;
  background: transparent;
}
</style>

<style scoped>
/* 复用 DrawingRoom / LiveWarRoom 的布局与美术风格（略裁剪非必要部分） */
.chat-container {
  display: flex;
  height: 100vh;
  height: 100dvh;
  background: transparent;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  padding: 5.5em;
  box-sizing: border-box;
  gap: 8px;
}

.left-sidebar {
  width: 250px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  display: flex;
  flex-direction: column;
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  transition: transform 0.3s ease;
  z-index: 1000;
  position: fixed;
  top: 0.5em;
  bottom: 0.5em;
  left: -8px;
  transform: translateX(-100%);
  overflow: hidden;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

.left-sidebar.mobile-show,
.left-sidebar.desktop-show {
  transform: translateX(0);
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
}

/* 菜单样式（与 LiveWarRoom 一致） */
.logo-section {
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
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
  color: #4A90E2;
}

.rooms-section {
  flex: 1;
  padding: 1rem;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.rooms-section::-webkit-scrollbar {
  width: 6px;
}

.rooms-section::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 3px;
  margin: 0.5rem 0;
}

.rooms-section::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  transition: background 0.2s ease, width 0.2s ease;
}

.rooms-section::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

.rooms-section::-webkit-scrollbar-thumb:active {
  background: rgba(255, 255, 255, 0.35);
}

.rooms-section {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) rgba(255, 255, 255, 0.03);
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
  flex-shrink: 0;
}

.user-info {
  margin-bottom: 1rem;
}

.user-info .username {
  font-weight: 700;
  color: #2C3E50;
  text-shadow: 0 1px 2px rgb(255, 255, 255);
}

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
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 999;
  touch-action: none;
}

button,
.menu-btn {
  touch-action: manipulation;
}

.messages-container {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  background: transparent;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  position: relative;
  z-index: 1;
  touch-action: pan-y;
  /* 允许聊天消息文字选择 */
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}

/* 美化滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: background 0.2s ease;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Firefox 滚动条样式 */
.messages-container {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05);
}

.message {
  margin-bottom: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 18px;
  max-width: 70%;
  word-wrap: break-word;
  position: relative;
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

.game-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  max-height: 100vh;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

.right-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
  min-height: 0;
  overflow: hidden;
  position: relative;
  z-index: 1;
  gap: 8px;
}

@media (min-width: 769px) {
  .right-chat.with-game {
    flex: 0 0 400px;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.02);
  }
}

/* 系统消息提示条（与 LiveWarRoom 一致） */
.system-notification {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  right: 0.5rem;
  z-index: 9999;
  min-height: 30px;
  padding: 8px 20px;
  background: #000000;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
  pointer-events: none;
  border-radius: var(--px-border-radius, 15px);
  border: var(--px-border, 3px) solid #000000;
  box-sizing: border-box;
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
  height: 65px;
  flex-shrink: 0;
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
  line-height: 1.2;
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

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgb(255, 255, 255);
  border-radius: 24px;
  position: relative;
  backdrop-filter: blur(10px);
}

.input-wrapper {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  align-items: stretch;
}

.message-input {
  flex: 1;
  min-width: 0;
  padding: 0.75rem 1rem;
  border: 4px solid rgb(255, 255, 255);
  border-radius: 16px;
  font-size: 1rem;
  outline: none;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  box-sizing: border-box;
  backdrop-filter: blur(10px);
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
  min-width: fit-content;
}

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

/* 移动端：棋盘 + 下方聊天区域（共用一屏） */
.mobile-board-with-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.mobile-board-with-chat .game-panel-mobile {
  flex-shrink: 0;
  margin-bottom: 0;
}

.mobile-board-with-chat .messages-below-board {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0.75rem 1rem;
}

.game-panel-mobile {
  display: flex;
  flex-direction: column;
  height: auto;
  background: transparent;
  border: none;
  margin-bottom: 1rem;
  border-radius: 0;
  overflow: hidden;
  padding: 1rem;
  box-sizing: border-box;
  gap: 0.75rem;
}

.game-panel-mobile .gobang-join-container {
  flex-shrink: 0;
}

/* 桌面端五子棋面板：棋盘 + 加入按钮 */
.gobang-panel-desktop {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  padding: 1rem;
  box-sizing: border-box;
  gap: 0.75rem;
}

.gobang-join-container {
  display: flex;
  width: 100%;
  justify-content: center;
  align-items: center;
}

.gobang-join-btn {
  position: relative;
  padding: 0.875rem 2rem;
  font-size: 1rem;
  font-weight: 900;
  border: none;
  cursor: pointer;
  transition: all 0.1s ease-out;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 12px;
  box-sizing: border-box;
  min-height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  text-shadow:
    2px 2px 0px rgba(0, 0, 0, 0.8),
    4px 4px 0px rgba(0, 0, 0, 0.6),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #3b82f6 100%);
  box-shadow:
    0 6px 0px rgba(25, 113, 194, 0.8),
    0 4px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.gobang-join-btn:not(:disabled):hover,
.gobang-join-btn:not(:disabled):active {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(25, 113, 194, 0.8),
    0 1px 0px rgba(25, 113, 194, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.gobang-join-btn.joined {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 50%, #22c55e 100%);
  box-shadow:
    0 6px 0px rgba(22, 101, 52, 0.8),
    0 4px 0px rgba(22, 101, 52, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
}

.gobang-join-btn.joined:not(:disabled):hover,
.gobang-join-btn.joined:not(:disabled):active {
  transform: translateY(4px);
  box-shadow:
    0 2px 0px rgba(22, 101, 52, 0.8),
    0 1px 0px rgba(22, 101, 52, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.gobang-join-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #666666;
  box-shadow:
    0 2px 0px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 音乐容器（头部）- 参考 LiveWarRoom / GamePanel 所在房间 */
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
  top: 80px;
  right: 32px;
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

.music-list::-webkit-scrollbar {
  width: 6px;
}

.music-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  margin: 0.5rem 0;
}

.music-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
  transition: background 0.2s ease;
}

.music-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.music-list::-webkit-scrollbar-thumb:active {
  background: rgba(0, 0, 0, 0.4);
}

.music-list {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) rgba(0, 0, 0, 0.05);
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

/* 棋盘切换按钮（移动端，与 LiveWarRoom 的 drawing-icon-btn 样式一致） */
.drawing-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-right: 0.5rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2C3E50;
  border: 3px solid rgb(255, 255, 255);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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

@media (max-width: 768px) {
  .chat-container {
    position: relative;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
    padding: 1em;
    gap: 8px;
  }

  .right-chat {
    width: 100%;
    min-height: 0;
    gap: 8px;
  }

  .left-sidebar {
    width: 280px;
    border-radius: 12px;
  }

  .left-sidebar.mobile-show {
    transform: translateX(0);
  }

  .user-section {
    padding: 0.75rem 1rem;
    margin-top: auto;
  }

  .user-info {
    margin-bottom: 0.75rem;
  }

  .logout-btn {
    font-size: 0.9rem;
    padding: 0.6rem 0.75rem;
  }

  /* 确保移动端消息容器正确滚动（与 LiveWarRoom 一致） */
  .messages-container {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
