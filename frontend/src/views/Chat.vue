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

    <!-- 右侧聊天区域 -->
    <div class="right-chat">
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

        <!-- 已选择房间时的消息列表 -->
        <div v-else class="messages-container" ref="messagesContainer">
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

export default {
  name: 'Chat',
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
  beforeUnmount () {
    if (this.ws) {
      this.ws.close()
    }
    // 清理音频资源
    this.cleanupAudio()
    // 清理窗口大小变化监听器
    window.removeEventListener('resize', this.checkMobileDevice)
    // 清理键盘检测监听器
    window.removeEventListener('resize', this.handleKeyboardToggle)
    // 清理视口变化监听器
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', this.handleKeyboardToggle)
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
                    MUSIC: 5
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
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.logo-image {
  width: 100%;
  height: auto;
  max-height: 60px;
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

.messages-container {
  flex: 1;
  padding: 1rem 1.5rem;
  overflow-y: auto;
  background: transparent;
  display: flex;
  flex-direction: column;
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

</style>
