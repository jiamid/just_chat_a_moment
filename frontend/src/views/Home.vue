<template>
  <div class="home-container" :class="{ 'tree-mode-active': isTreeMode }">
    <!-- 顶部三个气泡 -->
    <div class="top-bubbles">
      <!-- Logo气泡 -->
      <div class="bubble logo-bubble">
        <div class="logo-section">
          <h1 class="logo-text">JustChatAMoment</h1>
        </div>
      </div>

      <!-- 中间气泡：时间显示 -->
      <div class="bubble intro-bubble">
        <div class="intro-content">
          <div class="time-display">
            <div class="date-section">
              <template v-for="(char, index) in dateString" :key="`date-${index}`">
                <span
                  v-if="isDigit(char)"
                  class="flip-digit"
                  :class="{ 'is-flipping': dateFlippingIndexes.includes(index) }"
                >
                  <span class="digit-front">{{ char }}</span>
                  <span class="digit-back">{{ char }}</span>
                </span>
                <span v-else class="time-char">{{ char }}</span>
              </template>
            </div>
            <div class="time-section">
              <template v-for="(char, index) in timeString" :key="`time-${index}`">
                <span
                  v-if="isDigit(char)"
                  class="flip-digit"
                  :class="{ 'is-flipping': timeFlippingIndexes.includes(index) }"
                >
                  <span class="digit-front">{{ char }}</span>
                  <span class="digit-back">{{ char }}</span>
                </span>
                <span v-else class="time-char">{{ char }}</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧气泡：登录按钮 -->
      <button class="bubble login-btn-bubble" @click="handleEnterClick">
        <span class="btn-text">Enter</span>
      </button>
    </div>

    <!-- 底部一个气泡：详细介绍 -->
    <div class="bottom-bubble">
      <div class="bubble content-bubble" :class="{ 'tree-mode': isTreeMode }">
        <ParticleText :text="displayUsername" @gesture-mode-changed="handleGestureModeChanged" />
      </div>
    </div>

    <!-- 登录模态框 -->
    <div v-if="showLoginModal" class="modal-overlay" @click.self="showLoginModal = false">
      <div class="login-box">
        <button class="close-btn" @click="showLoginModal = false">×</button>

        <div class="form-tabs">
          <button
            :class="{ active: isLogin }"
            @click="isLogin = true"
          >
            登录
          </button>
          <button
            :class="{ active: !isLogin }"
            @click="isLogin = false"
          >
            注册
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="login-form">
          <div class="form-group">
            <label>邮箱</label>
            <input
              v-model="form.email"
              type="email"
              required
              placeholder="请输入邮箱"
            />
          </div>

          <div v-if="!isLogin" class="form-group">
            <label>用户名</label>
            <input
              v-model="form.username"
              type="text"
              required
              placeholder="请输入用户名"
            />
          </div>

          <div class="form-group">
            <label>密码</label>
            <input
              v-model="form.password"
              type="password"
              required
              placeholder="请输入密码"
            />
          </div>

          <div v-if="!isLogin" class="form-group">
            <label>验证码</label>
            <div class="code-row">
              <input
                v-model="form.code"
                type="text"
                required
                placeholder="请输入邮箱验证码"
              />
              <button
                type="button"
                class="code-btn"
                :disabled="countdown > 0 || loading || !form.email"
                @click="getCode"
              >
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </button>
            </div>
          </div>

          <button type="submit" :disabled="loading" class="submit-btn">
            {{ loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
          </button>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/utils/request.js'
import ParticleText from '@/components/ParticleText.vue'

export default {
  name: 'Home',
  components: {
    ParticleText
  },
  data () {
    return {
      showLoginModal: false,
      isLogin: true,
      loading: false,
      error: '',
      dateString: '',
      timeString: '',
      previousDateString: '',
      previousTimeString: '',
      dateFlippingIndexes: [],
      timeFlippingIndexes: [],
      timeTimer: null,
      form: {
        email: '',
        username: '',
        password: '',
        code: '',
        sign: '',
        expires_at: 0
      },
      countdown: 0,
      timer: null,
      isTreeMode: false // 是否为圣诞树模式
    }
  },
  computed: {
    displayUsername () {
      // 如果已登录，显示 username，否则显示 JIAMID
      const username = localStorage.getItem('username')
      return username || 'JIAMID'
    }
  },
  async mounted () {
    // 检查是否有token，如果有则尝试自动登录
    await this.checkAutoLogin()
    // 初始化时间显示
    this.updateTime()
    this.timeTimer = setInterval(() => {
      this.updateTime()
    }, 1000)
  },
  beforeUnmount () {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
    if (this.timeTimer) {
      clearInterval(this.timeTimer)
      this.timeTimer = null
    }
  },
  methods: {
    // 处理手势模式变化
    handleGestureModeChanged (mode) {
      this.isTreeMode = mode === 'tree'
    },
    isDigit (char) {
      return /[0-9]/.test(char)
    },

    updateTime () {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')

      const newDateString = `${year}年${month}月${day}日`
      const newTimeString = `${hours}:${minutes}:${seconds}`

      // 检测日期哪些位置的数字发生了变化
      if (this.previousDateString && this.previousDateString !== newDateString) {
        this.dateFlippingIndexes = []
        for (let i = 0; i < newDateString.length; i++) {
          if (this.previousDateString[i] !== newDateString[i] && /[0-9]/.test(newDateString[i])) {
            this.dateFlippingIndexes.push(i)
          }
        }
        setTimeout(() => {
          this.dateFlippingIndexes = []
        }, 600)
      }

      // 检测时间哪些位置的数字发生了变化
      if (this.previousTimeString && this.previousTimeString !== newTimeString) {
        this.timeFlippingIndexes = []
        for (let i = 0; i < newTimeString.length; i++) {
          if (this.previousTimeString[i] !== newTimeString[i] && /[0-9]/.test(newTimeString[i])) {
            this.timeFlippingIndexes.push(i)
          }
        }
        setTimeout(() => {
          this.timeFlippingIndexes = []
        }, 600)
      }

      this.previousDateString = this.dateString
      this.previousTimeString = this.timeString
      this.dateString = newDateString
      this.timeString = newTimeString
    },

    async checkAutoLogin () {
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      // 如果是从聊天页主动返回的，清除查询参数
      if (this.$route.query.returnFromChat === 'true') {
        this.$router.replace({ path: '/', query: {} })
      }

      // 验证token是否有效，如果无效则清除
      try {
        const userResponse = await api.user.getMe()
        // token有效，更新 username 到 localStorage（如果不存在）
        if (!localStorage.getItem('username') && userResponse.data.username) {
          localStorage.setItem('username', userResponse.data.username)
        }
      } catch (error) {
        // token无效或过期，清除localStorage中的token和username
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        console.log('token无效，已清除:', error.message)
      }
    },

    async handleEnterClick () {
      console.log('handleEnterClick 被调用')
      // 检查是否已登录
      const token = localStorage.getItem('token')
      if (!token) {
        // 未登录，显示登录模态框
        console.log('未登录，显示登录模态框')
        this.showLoginModal = true
        return
      }

      try {
        // 验证token是否有效
        console.log('验证token有效性')
        await api.user.getMe()
        // token有效，直接跳转到聊天页面
        console.log('token有效，跳转到聊天页面')
        this.$router.push('/chat')
      } catch (error) {
        // token无效或过期，清除localStorage中的token和username并显示登录模态框
        console.log('token无效，已清除:', error.message)
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        this.showLoginModal = true
      }
    },

    async handleSubmit () {
      this.loading = true
      this.error = ''

      try {
        if (this.isLogin) {
          await this.login()
        } else {
          await this.register()
        }
      } catch (err) {
        this.error = err.message || '操作失败'
      } finally {
        this.loading = false
      }
    },

    async login () {
      const response = await api.auth.login({
        username: this.form.email,
        password: this.form.password
      })

      localStorage.setItem('token', response.data.access_token)
      // 登录成功后获取用户信息并保存 username
      try {
        const userResponse = await api.user.getMe()
        localStorage.setItem('username', userResponse.data.username)
      } catch (err) {
        console.error('获取用户信息失败:', err)
      }
      this.showLoginModal = false
      this.$router.push('/chat')
    },

    async register () {
      await api.auth.register({
        email: this.form.email,
        username: this.form.username,
        password: this.form.password,
        code: this.form.code,
        sign: this.form.sign,
        expires_at: this.form.expires_at
      })

      // 注册成功后保存 username（注册时使用的是 form.username）
      localStorage.setItem('username', this.form.username)

      // 注册成功后切换到登录模式，并自动填充邮箱和密码
      this.isLogin = true
      // 保持邮箱和密码不变，清空用户名和验证码
      this.form.username = ''
      this.form.code = ''

      // 显示成功消息
      this.error = ''
      this.$nextTick(() => {
        console.log('注册成功，请登录')
      })
    },

    async getCode () {
      if (!this.form.email) {
        this.error = '请先输入邮箱'
        return
      }
      try {
        this.loading = true
        const resp = await api.auth.getSmsCode({ email: this.form.email })
        // 后端返回 { email, expires_at, sign }
        this.form.expires_at = resp.data.expires_at
        this.form.sign = resp.data.sign
        this.error = ''
        // 开始倒计时 120s
        this.countdown = 120
        if (this.timer) clearInterval(this.timer)
        this.timer = setInterval(() => {
          if (this.countdown > 0) {
            this.countdown -= 1
          }
          if (this.countdown <= 0) {
            clearInterval(this.timer)
            this.timer = null
          }
        }, 1000)
      } catch (err) {
        this.error = err.message || '获取验证码失败'
      } finally {
        this.loading = false
      }
    }

  }
}
</script>

<style scoped>
.home-container {
  height: 100vh;
  padding: 2rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  overflow: hidden;
  position: relative;
  z-index: 1;
  background: #ffffff;
}

/* 气泡基础样式 */
.bubble {
  background: #ffffff;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  padding: 2rem;
  transition: all 0.2s ease;
  box-sizing: border-box;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* 圣诞树模式下，所有气泡边框变为红色 */
.home-container.tree-mode-active .bubble {
  border-color: #ff0000 !important;
}

/* 顶部三个气泡布局 */
.top-bubbles {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 2rem;
}

/* 顶部气泡导航栏样式 */
.top-bubbles > .bubble {
  padding: 0.75rem 1.25rem;
}

/* Logo气泡 */
.logo-bubble {
  display: flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  max-width: 200px;
}

.logo-section {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  box-shadow: none;
  position: relative;
}

/* 介绍气泡 */
.intro-bubble {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo-text {
  margin: 0;
  text-align: center;
  color: #000000;
  font-size: 1.25rem;
  font-weight: 600;
  position: relative;
  z-index: 1;
  line-height: 1.2;
  white-space: nowrap;
}

.intro-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.5rem;
}

.clock-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.time-display {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  font-family: 'Courier New', 'Courier', monospace;
  text-rendering: optimizeSpeed;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: auto;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.date-section,
.time-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.time-char {
  font-size: 2rem;
  font-weight: 900;
  display: inline-block;
  color: #000000;
  text-shadow: none;
  letter-spacing: 0.1em;
}

.flip-digit {
  display: inline-block;
  position: relative;
  width: 1.2em;
  height: 2em;
  text-align: center;
  vertical-align: middle;
  perspective: 200px;
}

.digit-front,
.digit-back {
  position: absolute;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  backface-visibility: hidden;
  transition: transform 0.6s;
  font-size: 2rem;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  color: #000000;
  text-shadow: none;
  letter-spacing: 0.1em;
}

.digit-front {
  transform: rotateX(0deg);
}

.digit-back {
  transform: rotateX(180deg);
}

.flip-digit.is-flipping .digit-front {
  transform: rotateX(-180deg);
}

.flip-digit.is-flipping .digit-back {
  transform: rotateX(0deg);
}

.flip-digit:not(.is-flipping) .digit-front,
.flip-digit:not(.is-flipping) .digit-back {
  transition: none;
}

/* 登录按钮气泡 */
.login-btn-bubble {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #000000;
  border: var(--px-border, 3px) solid #000000;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: fit-content;
  min-width: 120px;
  border-radius: var(--px-border-radius, 15px);
}

.login-btn-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-btn-bubble:hover::before {
  left: 100%;
}

.login-btn-bubble:hover {
  transform: translate(-2px, -2px);
  background: #000000;
}

.login-btn-bubble:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.btn-text {
  font-size: 1.25rem;
  font-weight: 700;
}

/* 底部气泡 */
.bottom-bubble {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-bubble {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: auto;
  padding: 0;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: #ffffff;
  border-radius: 6px;
  border: var(--px-border, 3px) solid #000000;
  transition: all 0.2s ease;
}

.feature-icon {
  font-size: 2.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.feature-text h3 {
  margin: 0 0 0.5rem 0;
  color: #000000;
  font-size: 1.25rem;
  font-weight: 600;
}

.feature-text p {
  margin: 0;
  color: #333333;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* 登录模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.login-box {
  background: #ffffff;
  padding: 2.5rem 2rem;
  border-radius: 8px;
  border: var(--px-border, 3px) solid #000000;
  width: 100%;
  max-width: 420px;
  position: relative;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.close-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #000000;
  border-radius: 50%;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: transparent;
  color: #000000;
  transform: rotate(90deg);
}

.form-tabs {
  display: flex;
  margin-bottom: 1.5rem;
  gap: 0.5rem;
  background: #ffffff;
  padding: 0.25rem;
  border-radius: 4px;
  border: var(--px-border, 3px) solid #000000;
}

.form-tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  color: #333333;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.95rem;
}

.form-tabs button.active {
  background: #000000;
  color: #ffffff;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #000000;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: var(--px-border, 3px) solid #000000;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
  background: #ffffff;
  color: #000000;
  transition: all 0.2s ease;
}

.form-group input:hover {
  border-color: #000000;
  background: #ffffff;
}

.form-group input:focus {
  outline: none;
  border-color: #000000;
  background: #ffffff;
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  margin-top: 0.5rem;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.submit-btn:hover:not(:disabled)::before {
  left: 100%;
}

.submit-btn:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  background: #000000;
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

.error-message {
  margin-top: 1rem;
  padding: 0.875rem;
  background: linear-gradient(135deg, rgba(196, 30, 58, 0.2) 0%, rgba(196, 30, 58, 0.15) 100%);
  color: #ffb3b3;
  border: var(--px-border, 3px) solid #000000;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
}

.code-row {
  display: flex;
  gap: 0.5rem;
}

.code-row input {
  flex: 1;
}

.code-btn {
  padding: 0.75rem 1rem;
  border: var(--px-border, 3px) solid #000000;
  background: #ffffff;
  color: #000000;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.code-btn:hover:not(:disabled) {
  background: #ffffff;
  color: #000000;
  transform: translate(-1px, -1px);
}

.code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
  border-color: #cccccc;
}

.login-form {
  margin-top: 1rem;
}

/* 占位符颜色 */
::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .time-display {
    flex-direction: column;
    gap: 0.5rem;
  }

  .home-container {
    padding: 1rem;
    gap: 1rem;
  }

  .top-bubbles {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .top-bubbles > .bubble {
    width: 100%;
  }

  .logo-bubble {
    max-width: 100%;
    width: 100%;
  }

  .bubble {
    padding: 1.5rem;
  }

  .btn-icon {
    font-size: 1.1rem;
  }

  .btn-text {
    font-size: 1.1rem;
    font-weight: 700;
  }

  .features {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .feature-item {
    padding: 1.25rem;
  }

  .time-char {
    font-size: 1.5rem;
  }

  .digit-front,
  .digit-back {
    font-size: 1.5rem;
  }

  .flip-digit {
    width: 1em;
    height: 1.8em;
  }

  .content-title {
    font-size: 1.5rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .login-box {
    padding: 2rem 1.5rem;
    max-width: 100%;
    border-radius: 6px;
  }
}
</style>
