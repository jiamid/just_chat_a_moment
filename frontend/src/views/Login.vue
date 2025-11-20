<template>
  <div class="login-container">
    <div class="login-box">
      <div class="logo-section">
        <img
          v-show="logoLoaded"
          src="https://cdn.jiamid.com/just_chat_a_moment.webp"
          alt="Just Chat A Moment"
          class="logo-image"
          @load="logoLoaded = true"
          @error="logoLoaded = false"
        />
        <h2 v-show="!logoLoaded" class="logo-text">Just Chat A Moment</h2>
      </div>
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
</template>

<script>
import { api } from '@/utils/request.js'

export default {
  name: 'Login',
  data () {
    return {
      isLogin: true,
      loading: false,
      error: '',
      logoLoaded: false,
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
  },
  beforeUnmount () {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  },
  methods: {
    async checkAutoLogin () {
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      try {
        // 验证token是否有效
        await api.user.getMe()
        // token有效，直接跳转到聊天页面
        this.$router.push('/chat')
      } catch (error) {
        // token无效或过期，清除localStorage中的token
        localStorage.removeItem('token')
        console.log('token无效，已清除:', error.message)
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

      // 注册成功后切换到登录模式，并自动填充邮箱和密码
      this.isLogin = true
      // 保持邮箱和密码不变，清空用户名和头像
      this.form.username = ''
      this.form.code = ''

      // 显示成功消息
      this.error = ''
      this.$nextTick(() => {
        // 可以添加一个成功提示
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
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: radial-gradient(1200px 800px at 10% 20%, rgba(139, 92, 246, 0.25), rgba(139, 92, 246, 0) 60%),
              radial-gradient(1000px 700px at 90% 30%, rgba(236, 72, 153, 0.25), rgba(236, 72, 153, 0) 60%),
              radial-gradient(1100px 600px at 50% 80%, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0) 60%),
              radial-gradient(900px 500px at 30% 70%, rgba(168, 85, 247, 0.15), rgba(168, 85, 247, 0) 50%),
              linear-gradient(135deg, #1a1625 0%, #2a1f3e 20%, #1e1b2e 40%, #251f35 60%, #1a1625 80%, #1a1625 100%);
}

.login-box {
  background: rgba(30, 41, 59, 0.6);
  padding: 2.5rem 2rem;
  border-radius: 20px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: 0 25px 70px rgba(0, 0, 0, 0.5),
              0 10px 30px rgba(0, 0, 0, 0.3),
              inset 0 1px 0 rgba(255, 255, 255, 0.05);
  width: 100%;
  max-width: 420px;
}

.logo-section {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 2rem;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  box-shadow: none;
  position: relative;
}

.logo-image {
  width: 100%;
  height: auto;
  object-fit: contain;
  display: block;
  position: relative;
  z-index: 1;
}

.logo-text {
  margin: 0;
  text-align: center;
  color: #ffffff;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 40%, #c026d3 70%, #dc2626 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 1.5rem;
  font-weight: 600;
  position: relative;
  z-index: 1;
  line-height: 1.2;
}

.form-tabs {
  display: flex;
  margin-bottom: 1.5rem;
  gap: 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  padding: 0.25rem;
  border-radius: 12px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.form-tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.95rem;
}

.form-tabs button:hover {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(71, 85, 105, 0.3);
}

.form-tabs button.active {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 40%, #c026d3 70%, #dc2626 100%);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.5),
              0 2px 8px rgba(220, 38, 127, 0.3);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(30, 41, 59, 0.6);
  color: #ffffff;
  transition: all 0.3s ease;
}

.form-group input:hover {
  border-color: rgba(100, 116, 139, 0.5);
  background: rgba(30, 41, 59, 0.7);
}

.form-group input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.8);
  background: rgba(30, 41, 59, 0.8);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3),
              0 0 0 6px rgba(220, 38, 127, 0.15),
              inset 0 1px 2px rgba(255, 255, 255, 0.05);
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 30%, #c026d3 60%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4),
              0 4px 12px rgba(220, 38, 127, 0.3),
              inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
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
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(139, 92, 246, 0.5),
              0 6px 16px rgba(220, 38, 127, 0.4),
              inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(139, 92, 246, 0.3);
}

.error-message {
  margin-top: 1rem;
  padding: 0.875rem;
  background: linear-gradient(135deg, rgba(220, 38, 127, 0.2) 0%, rgba(220, 38, 127, 0.15) 100%);
  color: #ffb3d9;
  border: 1px solid rgba(220, 38, 127, 0.4);
  border-radius: 12px;
  text-align: center;
  font-size: 0.9rem;
  box-shadow: inset 0 1px 2px rgba(220, 38, 127, 0.2);
}

.beian-info {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  font-size: 12px;
  color: white;
  z-index: 1000;
}

.beian-info a {
  color: white;
  text-decoration: none;
  transition: color 0.3s;
}

.beian-info a:hover {
  color: #f0f0f0;
  text-decoration: underline;
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
  border: 1px solid rgba(71, 85, 105, 0.4);
  background: rgba(30, 41, 59, 0.6);
  color: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.code-btn:hover:not(:disabled) {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(100, 116, 139, 0.6);
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(30, 41, 59, 0.3);
  border-color: rgba(71, 85, 105, 0.2);
}

/* 占位符颜色在暗色背景下更柔和 */
::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 1rem;
  }

  .login-box {
    padding: 2rem 1.5rem;
    max-width: 100%;
    border-radius: 16px;
  }

  .logo-image {
    max-width: 240px;
  }

  .logo-text {
    font-size: 1.2rem;
  }

  .logo-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
  }

  .form-tabs {
    margin-bottom: 1.25rem;
  }

  .form-tabs button {
    padding: 0.625rem;
    font-size: 0.9rem;
  }
}
</style>
