<template>
  <div class="chat-container">
    <!-- 移动端遮罩层 -->
    <div
      v-if="isMobile && showMobileNavbar"
      class="mobile-overlay"
      @click="hideMobileNavbar"
    ></div>

    <!-- 左侧导航栏 -->
    <div class="left-sidebar" :class="{ 'mobile-show': showMobileNavbar && isMobile }">
      <!-- Logo -->
      <div class="logo-section">
        <img src="https://cdn.jiamid.com/just_chat_a_moment.webp" alt="Just Chat A Moment" class="logo-image" />
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
            <button v-else-if="roomId" @click="reconnect" class="reconnect-btn">重连</button>
          </div>
        </div>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <!-- 中间画布区域（仅在画图面板打开时显示，桌面端） -->
    <div v-if="showDrawingPanel && roomId && !isMobile" class="drawing-area">
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
    <div class="right-chat" :class="{ 'with-drawing': showDrawingPanel && roomId }">
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
                  <path d="M9 18V5l12-2v13"></path>
                  <circle cx="6" cy="18" r="3"></circle>
                  <circle cx="18" cy="16" r="3"></circle>
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

      <!-- 系统消息提示条 -->
      <div v-if="systemMessage" class="system-notification">
        {{ systemMessage }}
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

          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
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

      <!-- 底部：输入区域 -->
      <div class="input-container" v-if="roomId" :class="{
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
      jumpRoomId: '',
      recentRooms: [],
      showMobileNavbar: false,
      isMobile: false,
      isKeyboardOpen: false,
      initialViewportHeight: 0,
      musicConfig: {},
      showMusicMenu: false,
      isPlaying: false,
      currentMusicId: null,
      // 音频解锁相关状态
      audioUnlocked: false,
      audioContext: null,
      audioElement: null,
      musicMenuStyle: {}
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
    this.initAudio() // 初始化音频系统
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
                }
              }
            }
          }
        })
        this.ChatMessage = root.lookupType('chat.ChatMessage')
        console.log('Protobuf loaded successfully')
      } catch (err) {
        console.error('Failed to load protobuf:', err)
      }
    },

    connectWebSocket () {
      const token = localStorage.getItem('token')
      const wsUrl = config.getWsUrl(this.roomId, token)

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnected = true
        console.log('WebSocket connected')
      }

      this.ws.onmessage = async (event) => {
        try {
          // 检查protobuf是否已加载
          if (!this.ChatMessage) {
            console.warn('ChatMessage not loaded yet, skipping message')
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

          const message = this.ChatMessage.decode(data)

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

        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
        this.newMessage = ''
      } catch (err) {
        console.error('Failed to send message:', err)
      }
    },

    scrollToBottom () {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    formatTime (timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },

    logout () {
      localStorage.removeItem('token')
      this.$router.push('/login')
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
      // 3秒后自动隐藏系统消息
      setTimeout(() => {
        this.systemMessage = ''
      }, 3000)
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
      if (!this.isConnected || !this.ChatMessage) {
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

        const buffer = this.ChatMessage.encode(message).finish()
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
}

#app {
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  height: 100dvh; /* 使用动态视口高度，更好地处理移动端 */
  background: radial-gradient(1200px 800px at 10% 20%, rgba(139, 92, 246, 0.25), rgba(139, 92, 246, 0) 60%),
              radial-gradient(1000px 700px at 90% 30%, rgba(236, 72, 153, 0.25), rgba(236, 72, 153, 0) 60%),
              radial-gradient(1100px 600px at 50% 80%, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0) 60%),
              radial-gradient(900px 500px at 30% 70%, rgba(168, 85, 247, 0.15), rgba(168, 85, 247, 0) 50%),
              linear-gradient(135deg, #1a1625 0%, #2a1f3e 20%, #1e1b2e 40%, #251f35 60%, #1a1625 80%, #1a1625 100%);
  overflow: hidden; /* 防止整体滚动 */
  position: fixed; /* 固定定位，防止页面滚动 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
}

/* 左侧导航栏 */
.left-sidebar {
  width: 250px;
  background: rgba(255, 255, 255, 0.06);
  color: #e6e6f0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 8px 0 32px rgba(0,0,0,0.3);
  transition: transform 0.3s ease;
  z-index: 1000;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  /* 与chat-header高度保持一致：统一设置为65px */
  height: 65px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.logo-image {
  width: 100%;
  height: auto;
  max-height: 49px; /* 65px (logo-section高度) - 16px (上下padding 0.5rem * 2) = 49px */
  object-fit: contain;
  display: block;
}

.rooms-section {
  flex: 1;
  padding: 1rem;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
  overflow-y: auto; /* 如果内容过多，允许滚动 */
}

.rooms-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #cdd0e5;
  font-weight: 500;
}

.room-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.room-item {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.room-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.room-item.active {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.7) 0%, rgba(168, 85, 247, 0.7) 30%, rgba(192, 38, 211, 0.7) 60%, rgba(220, 38, 38, 0.7) 100%);
  border-color: transparent;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
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
  color: #bdc3c7;
  font-weight: 500;
}

.jump-input-group {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.jump-input {
  flex: 1;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  color: #e6e6f0;
  font-size: 1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  text-align: center;
  min-width: 0;
}

.jump-input::placeholder {
  color: rgba(230, 230, 240, 0.55);
  font-weight: 500;
}

.jump-input:focus {
  background: transparent;
}

.jump-btn {
  flex: 1;
  padding: 0;
  background: transparent;
  color: #ffffff;
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
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  flex-shrink: 0; /* 防止用户区域被压缩 */
}

.user-info {
  margin-bottom: 1rem;
}

.user-info .username {
  font-weight: 500;
  color: #ffffff;
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
  color: #86efac;
  font-weight: 500;
}

.connection-status-navbar .reconnect-btn {
  padding: 0.25rem 0.5rem;
  background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.25s ease;
}

.connection-status-navbar .reconnect-btn:hover {
  filter: brightness(1.05);
}

.logout-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.25s ease;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4), 0 4px 12px rgba(220, 38, 127, 0.3);
}

.logout-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

/* 中间画布区域 */
.drawing-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0; /* 允许收缩 */
  overflow: hidden;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  /* 确保画布区域始终在可见区域内 */
  max-height: 100vh;
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
}

/* 当有画图面板时，右侧聊天区域固定宽度（仅桌面端） */
@media (min-width: 769px) {
  .right-chat.with-drawing {
    flex: 0 0 400px; /* 固定宽度400px */
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.02);
  }
}

/* 系统消息提示条 */
.system-notification {
  height: 30px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.9) 0%, rgba(168, 85, 247, 0.9) 30%, rgba(192, 38, 211, 0.9) 60%, rgba(220, 38, 38, 0.9) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
}

.chat-header {
  background: rgba(255, 255, 255, 0.06);
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  position: relative;
  z-index: 100;
  overflow: visible;
  box-sizing: border-box;
  /* 统一高度为65px */
  height: 65px;
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
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.4), 0 4px 12px rgba(220, 38, 127, 0.3);
}

.menu-btn:hover {
  filter: brightness(1.05);
}

.menu-btn svg {
  stroke: currentColor;
}

.chat-header h2 {
  margin: 0;
  color: #e6e6f0;
  font-size: 1.5rem;
  line-height: 1.2; /* 明确设置line-height，确保高度计算准确 */
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #cdd0e5;
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
  color: #86efac;
  font-weight: 500;
}

.reconnect-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.25s ease;
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.25);
}

.reconnect-btn:hover {
  filter: brightness(1.05);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
}

/* 画图面板样式 */
.drawing-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  min-width: 0;
  min-height: 0;
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
}

.message {
  margin-bottom: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 18px;
  max-width: 70%;
  word-wrap: break-word;
  position: relative;
}

.own-message {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.9) 0%, rgba(168, 85, 247, 0.9) 30%, rgba(192, 38, 211, 0.9) 60%, rgba(220, 38, 38, 0.9) 100%);
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.other-message {
  background: rgba(255, 255, 255, 0.06);
  color: #e6e6f0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  margin-right: auto;
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
  color: rgba(230, 230, 240, 0.6);
}

.username {
  font-weight: 600;
}

.message-content {
  line-height: 1.4;
}

.input-container {
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.06);
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  gap: 1rem;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.25);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transition: transform 0.3s ease;
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
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 2000;
  min-width: 200px;
  max-width: 300px;
  animation: slideDown 0.2s ease-out;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: #1f2937;
  font-weight: 600;
}

.music-list {
  max-height: 200px;
  overflow-y: auto;
}

.music-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #374151;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.music-item:last-child {
  border-bottom: none;
}

.music-item:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.music-name {
  font-weight: 500;
}

/* 移动端键盘弹起时的输入框样式 */
.input-container.keyboard-open {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 998; /* 降低z-index，确保不会遮挡导航栏 */
  transform: translateY(0);
}

/* 移动端导航栏展开时隐藏键盘弹起状态的输入框 */
.input-container.navbar-open.keyboard-open {
  display: none;
}

.message-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  font-size: 1rem;
  outline: none;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.06);
  color: #e6e6f0;
}

.message-input:focus {
  border-color: transparent;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.45), 0 0 0 6px rgba(236, 72, 153, 0.25);
}

.message-input:disabled {
  background: rgba(255, 255, 255, 0.04);
  cursor: not-allowed;
}

.send-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.25s ease;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4), 0 4px 12px rgba(220, 38, 127, 0.3);
}

.send-btn:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  color: #e6e6f0;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.welcome-content p {
  color: #cdd0e5;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-container {
    position: relative;
    height: 100vh;
    height: 100dvh; /* 移动端使用动态视口高度 */
    overflow: hidden;
  }

  .right-chat {
    width: 100%;
    min-height: 0;
  }

  .left-sidebar {
    width: 280px; /* 移动端导航栏宽度 */
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

  .logo-image {
    max-height: 50px;
  }

  .chat-header {
    padding: 1rem;
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

  .input-container {
    padding: 1rem;
  }

  /* 移动端键盘弹起时调整输入框样式 */
  .input-container.keyboard-open {
    padding: 0.75rem 1rem;
    border-radius: 0;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 998; /* 确保不会遮挡导航栏(z-index: 1000) */
    transform: translateY(0);
  }

  /* 移动端导航栏展开时隐藏键盘弹起状态的输入框 */
  .input-container.navbar-open.keyboard-open {
    display: none;
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
}

/* 音乐图标按钮 */
.music-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  position: relative;
  overflow: hidden;
}

.music-icon-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.music-icon-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  margin-right: 0.5rem;
}

.drawing-icon-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.drawing-icon-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.drawing-icon-btn.active {
  background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.5);
}

/* 画图面板样式已在上面定义 */

.drawing-header {
  padding: 1rem 1.5rem; /* 与chat-header的padding保持一致 */
  background: rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
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
  color: #e6e6f0;
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
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: white;
}

.request-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.clear-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.clear-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.stop-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.stop-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.approve-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.approve-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.approve-btn-inline:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.approve-btn-inline:active:not(:disabled) {
  transform: translateY(0);
}

.approve-btn-inline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.drawing-tools {
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
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
  color: #cdd0e5;
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
  background: rgba(255, 255, 255, 0.08);
  color: #e6e6f0;
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px; /* 更圆润的按钮 */
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.width-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.width-btn.active {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.4);
  transform: translateY(-1px);
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
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    display: flex;
    flex-direction: column;
    overflow: visible; /* 允许内容显示 */
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
