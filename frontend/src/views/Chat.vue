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
        <h1>Just Chat A Moment</h1>
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
          <span v-if="isConnected" class="status-indicator connected"></span>
          <span v-if="isConnected" class="status-text">已连接</span>
          <button v-else @click="reconnect" class="reconnect-btn">重连</button>
        </div>
      </div>

      <!-- 系统消息提示条 -->
      <div v-if="systemMessage" class="system-notification">
        {{ systemMessage }}
      </div>

      <!-- 中间：消息区域 -->
      <div class="chat-main" @click="hideMobileNavbar">
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
      <div class="input-container" v-if="roomId">
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
import axios from 'axios'
import protobuf from 'protobufjs'
import config from '@/config'

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
      isMobile: false
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
    await this.loadUserInfo()
    await this.loadProtobuf()
    if (this.roomId) {
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
          this.connectWebSocket()
        }
      }
    }
  },
  beforeUnmount () {
    if (this.ws) {
      this.ws.close()
    }
    // 清理窗口大小变化监听器
    window.removeEventListener('resize', this.checkMobileDevice)
  },
  methods: {
    async loadUserInfo () {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(config.getApiUrl('/me'), {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.username = response.data.username
      } catch (err) {
        this.$router.push('/login')
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
                    ROOM_COUNT: 4
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
          } else {
            // 用户消息
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
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

/* 左侧导航栏 */
.left-sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
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
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

/* 移动端导航栏显示/隐藏 */
@media (max-width: 768px) {
  .left-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    transform: translateX(-100%);
    z-index: 1000;
  }

  .left-sidebar.mobile-show {
    transform: translateX(0);
  }
}

.logo-section {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid #34495e;
}

.logo-section h1 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #ecf0f1;
}

.rooms-section {
  flex: 1;
  padding: 1rem;
}

.rooms-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #bdc3c7;
  font-weight: 500;
}

.room-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.room-item {
  padding: 0.75rem;
  background: #34495e;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.room-item:hover {
  background: #3498db;
}

.room-item.active {
  background: #e74c3c;
}

.room-name {
  font-weight: 500;
}

.room-jump {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #34495e;
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
  background: #34495e;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.jump-input {
  flex: 1;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  text-align: center;
  min-width: 0;
}

.jump-input::placeholder {
  color: #7f8c8d;
  font-weight: 500;
}

.jump-input:focus {
  background: transparent;
}

.jump-btn {
  flex: 1;
  padding: 0;
  background: transparent;
  color: white;
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
  border-top: 1px solid #34495e;
}

.user-info {
  margin-bottom: 1rem;
}

.user-info .username {
  font-weight: 500;
  color: #ecf0f1;
}

.logout-btn {
  width: 100%;
  padding: 0.75rem;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
}

.logout-btn:hover {
  background: #c0392b;
}

/* 右侧聊天区域 */
.right-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

/* 系统消息提示条 */
.system-notification {
  height: 30px;
  background: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.chat-header {
  background: white;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.menu-btn:hover {
  background: #2980b9;
}

.menu-btn svg {
  stroke: currentColor;
}

.chat-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.connected {
  background: #27ae60;
}

.status-text {
  color: #27ae60;
  font-weight: 500;
}

.reconnect-btn {
  padding: 0.5rem 1rem;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.3s ease;
}

.reconnect-btn:hover {
  background: #c0392b;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  padding: 1rem 1.5rem;
  overflow-y: auto;
  background: #ffffff;
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
  background: #3498db;
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.other-message {
  background: #f1f3f4;
  color: #2c3e50;
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
  color: rgba(44, 62, 80, 0.6);
}

.username {
  font-weight: 600;
}

.message-content {
  line-height: 1.4;
}

.input-container {
  padding: 1rem 1.5rem;
  background: white;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 1rem;
  box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
}

.message-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #ecf0f1;
  border-radius: 25px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s ease;
}

.message-input:focus {
  border-color: #3498db;
}

.message-input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.send-btn {
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.3s ease;
}

.send-btn:hover:not(:disabled) {
  background: #2980b9;
}

.send-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* 未选择房间时的提示样式 */
.no-room-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f8f9fa;
}

.welcome-content {
  text-align: center;
  padding: 2rem;
  max-width: 500px;
}

.welcome-content h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.welcome-content p {
  color: #7f8c8d;
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
  }

  .right-chat {
    width: 100%;
  }

  .left-sidebar {
    width: 280px; /* 移动端导航栏宽度 */
  }

  .logo-section h1 {
    font-size: 1.1rem;
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

  .connection-status {
    font-size: 0.8rem;
  }

  .reconnect-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }
}

</style>
