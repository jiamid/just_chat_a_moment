<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Just Chat A Moment</h2>
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
  background: radial-gradient(1200px 600px at 10% 10%, rgba(99, 102, 241, 0.18), rgba(99, 102, 241, 0) 60%),
              radial-gradient(900px 500px at 90% 20%, rgba(236, 72, 153, 0.18), rgba(236, 72, 153, 0) 60%),
              linear-gradient(135deg, #0f1020 0%, #1b1c34 50%, #0c0d1a 100%);
}

.login-box {
  background: rgba(255, 255, 255, 0.06);
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 420px;
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #ffffff;
  background: linear-gradient(90deg, #e5e7ff, #c7d2fe, #fbcfe8);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.form-tabs {
  display: flex;
  margin-bottom: 1.5rem;
}

.form-tabs button {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: #cdd0e5;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 10px;
}

.form-tabs button.active {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #cdd0e5;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.06);
  color: #e6e6f0;
}

.form-group input:focus {
  outline: none;
  border-color: transparent;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.45), 0 0 0 6px rgba(236, 72, 153, 0.25);
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.35), 0 6px 16px rgba(236, 72, 153, 0.25);
}

.submit-btn:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.15);
  color: #fecaca;
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 10px;
  text-align: center;
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
  padding: 0.75rem 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: #cdd0e5;
  border-radius: 10px;
  cursor: pointer;
}

.code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 占位符颜色在暗色背景下更柔和 */
::placeholder {
  color: rgba(230, 230, 240, 0.55);
}
</style>
