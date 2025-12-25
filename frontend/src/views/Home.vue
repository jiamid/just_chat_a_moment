<template>
  <div class="home-container">
    <!-- 皇室战争风格背景 -->
    <ClashBackground />
    <!-- 顶部三个气泡 -->
    <div class="top-bubbles">
      <!-- Logo气泡 -->
      <div class="bubble logo-bubble">
        <div class="logo-section">
          <h1 class="logo-text">JIAMID</h1>
        </div>
      </div>

      <!-- 中间：时间显示 -->
      <div class="time-container">
        <div class="time-display">
          <div class="date-section">
            <template v-for="(char, index) in dateString" :key="`date-${index}`">
              <span class="time-char">{{ char }}</span>
            </template>
          </div>
          <div class="time-section">
            <template v-for="(char, index) in timeString" :key="`time-${index}`">
              <span class="time-char">{{ char }}</span>
            </template>
          </div>
        </div>
      </div>

      <!-- 右侧气泡：登录按钮 -->
      <button class="bubble login-btn-bubble" @click="handleEnterClick">
        <span class="btn-text">Enter</span>
      </button>
    </div>

    <!-- 底部展示区域 -->
    <div class="bottom-display-area">
    </div>

    <!-- 登录模态框 -->
    <div v-if="showLoginModal" class="modal-overlay" @click.self="showLoginModal = false">
      <div class="login-box">
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
import ClashBackground from '@/components/ClashBackground.vue'

export default {
  name: 'Home',
  components: {
    ClashBackground
  },
  data () {
    return {
      showLoginModal: false,
      isLogin: true,
      loading: false,
      error: '',
      dateString: '',
      timeString: '',
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
      timer: null
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
    updateTime () {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')

      this.dateString = `${year}年${month}月${day}日`
      this.timeString = `${hours}:${minutes}:${seconds}`
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
  background: linear-gradient(135deg, #87CEEB 0%, #4A90E2 50%, #87CEEB 100%);
  background-size: 200% 200%;
  animation: skyGradient 15s ease infinite;
  transition: background-color 0.3s ease;
}

@keyframes skyGradient {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* 气泡基础样式 - Supercell风格 */
.bubble {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  padding: 2rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
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

/* 时间容器 */
.time-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.logo-text {
  margin: 0;
  text-align: center;
  color: #FFD700;
  font-size: 2rem;
  font-weight: 900;
  position: relative;
  z-index: 1;
  line-height: 1.2;
  white-space: nowrap;
  letter-spacing: 0.15em;
  /* 3D 字体效果 - 多层阴影创造立体感 */
  text-shadow:
    /* 主阴影 - 右下深色，创造深度 */
    2px 2px 0px rgba(184, 134, 11, 0.9),
    4px 4px 0px rgba(184, 134, 11, 0.7),
    6px 6px 0px rgba(184, 134, 11, 0.5),
    8px 8px 0px rgba(184, 134, 11, 0.3),
    /* 高光 - 左上亮色，创造高光 */
    -1px -1px 0px rgba(255, 255, 255, 1),
    -2px -2px 0px rgba(255, 255, 200, 0.8),
    /* 外发光效果 */
    0 0 10px rgba(255, 215, 0, 0.6),
    0 0 20px rgba(255, 215, 0, 0.4),
    0 0 30px rgba(255, 215, 0, 0.2);
  /* 使用 filter 增强 3D 效果 */
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.3));
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
  font-size: 2.2rem;
  font-weight: 900;
  display: inline-block;
  color: #FFD700;
  letter-spacing: 0.1em;
  /* 固定宽度，防止数字变化时跳动 */
  width: 1em;
  text-align: center;
  font-variant-numeric: tabular-nums;
  /* 3D 字体效果 - 金色主题，与Logo呼应，在蓝色背景上清晰可见 */
  text-shadow:
    /* 主阴影 - 右下深色，创造深度 */
    2px 2px 0px rgba(184, 134, 11, 0.9),
    4px 4px 0px rgba(184, 134, 11, 0.7),
    6px 6px 0px rgba(184, 134, 11, 0.5),
    8px 8px 0px rgba(184, 134, 11, 0.3),
    /* 高光 - 左上亮色，创造高光 */
    -1px -1px 0px rgba(255, 255, 255, 1),
    -2px -2px 0px rgba(255, 255, 200, 0.8),
    /* 外发光效果 - 金色光晕 */
    0 0 10px rgba(255, 215, 0, 0.6),
    0 0 20px rgba(255, 215, 0, 0.4),
    0 0 30px rgba(255, 215, 0, 0.2);
  /* 使用 filter 增强 3D 效果 */
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.3));
}

/* 登录按钮气泡 - Supercell金色按钮风格 */
.login-btn-bubble {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
  border: 4px solid rgba(255, 255, 255, 0.9);
  color: #2C3E50;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: fit-content;
  min-width: 140px;
  border-radius: 20px;
  box-shadow:
    0 6px 12px rgba(255, 215, 0, 0.4),
    0 3px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-btn-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s;
}

.login-btn-bubble:hover::before {
  left: 100%;
}

.login-btn-bubble:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow:
    0 8px 16px rgba(255, 215, 0, 0.5),
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #FFE44D 0%, #FFB347 50%, #FFE44D 100%);
}

.login-btn-bubble:active {
  transform: translateY(-1px) scale(1.02);
}

.btn-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.btn-text {
  font-size: 1.3rem;
  font-weight: 800;
  text-shadow:
    1px 1px 2px rgba(255, 255, 255, 0.8),
    0 0 4px rgba(255, 255, 255, 0.4);
  letter-spacing: 0.05em;
}

/* 底部展示区域 */
.bottom-display-area {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  /* 空白展示区域，暂时无样式 */
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.95) 100%);
  padding: 2.5rem 2rem;
  border-radius: 24px;
  border: 4px solid rgba(255, 255, 255, 0.9);
  width: 100%;
  max-width: 420px;
  position: relative;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.2),
    0 10px 20px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
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

.form-tabs {
  display: flex;
  margin-bottom: 1.5rem;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  padding: 0.4rem;
  border-radius: 16px;
  border: 3px solid rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  color: #7F8C8D;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
}

.form-tabs button.active {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: #ffffff;
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 700;
  color: #2C3E50;
  font-size: 0.95rem;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 3px solid rgba(200, 200, 200, 0.6);
  border-radius: 12px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.9);
  color: #2C3E50;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgba(255, 255, 255, 0.8);
}

.form-group input:focus {
  outline: none;
  border-color: #4A90E2;
  background: rgba(255, 255, 255, 1);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 0 0 3px rgba(74, 144, 226, 0.2),
    0 2px 8px rgba(74, 144, 226, 0.3);
}

.submit-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
  color: #2C3E50;
  border: 4px solid rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  margin-top: 0.5rem;
  box-shadow:
    0 6px 12px rgba(255, 215, 0, 0.4),
    0 3px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  text-shadow:
    1px 1px 2px rgba(255, 255, 255, 0.8),
    0 0 4px rgba(255, 255, 255, 0.4);
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s;
}

.submit-btn:hover:not(:disabled)::before {
  left: 100%;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow:
    0 8px 16px rgba(255, 215, 0, 0.5),
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #FFE44D 0%, #FFB347 50%, #FFE44D 100%);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #CCCCCC 0%, #999999 100%);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.error-message {
  margin-top: 1rem;
  padding: 0.875rem;
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.15) 0%, rgba(192, 57, 43, 0.15) 100%);
  color: #E74C3C;
  border: 3px solid rgba(231, 76, 60, 0.4);
  border-radius: 12px;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 600;
  box-shadow:
    inset 0 2px 4px rgba(231, 76, 60, 0.1),
    0 2px 4px rgba(0, 0, 0, 0.1);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
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
  border: 3px solid rgba(74, 144, 226, 0.6);
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.1) 0%, rgba(53, 122, 189, 0.1) 100%);
  color: #4A90E2;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  box-shadow:
    0 2px 4px rgba(74, 144, 226, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.code-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.2) 0%, rgba(53, 122, 189, 0.2) 100%);
  color: #357ABD;
  border-color: rgba(74, 144, 226, 0.8);
  transform: translateY(-2px);
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(245, 245, 245, 0.8);
  border-color: rgba(200, 200, 200, 0.6);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.login-form {
  margin-top: 1rem;
}

/* 占位符颜色 */
::placeholder {
  color: rgba(127, 140, 141, 0.6);
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

  .content-title {
    font-size: 1.5rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .login-box {
    padding: 2rem 1.5rem;
    max-width: 100%;
    border-radius: 20px;
  }
}
</style>
