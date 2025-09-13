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
          <label>头像URL（可选）</label>
          <input
            v-model="form.avatar_url"
            type="url"
            placeholder="请输入头像URL"
          />
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
import axios from 'axios'
import config from '../config.js'

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
        avatar_url: ''
      }
    }
  },
  methods: {
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
        this.error = err.response?.data?.detail || '操作失败'
      } finally {
        this.loading = false
      }
    },

    async login () {
      const formData = new FormData()
      formData.append('username', this.form.email)
      formData.append('password', this.form.password)

      const response = await axios.post(config.getApiUrl('/auth/login'), formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      localStorage.setItem('token', response.data.access_token)
      this.$router.push('/chat')
    },

    async register () {
      await axios.post(config.getApiUrl('/auth/register'), {
        email: this.form.email,
        username: this.form.username,
        password: this.form.password,
        avatar_url: this.form.avatar_url || null
      })

      // 注册成功后切换到登录模式，并自动填充邮箱和密码
      this.isLogin = true
      // 保持邮箱和密码不变，清空用户名和头像
      this.form.username = ''
      this.form.avatar_url = ''

      // 显示成功消息
      this.error = ''
      this.$nextTick(() => {
        // 可以添加一个成功提示
        console.log('注册成功，请登录')
      })
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
}

.form-tabs {
  display: flex;
  margin-bottom: 1.5rem;
}

.form-tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.3s;
}

.form-tabs button.active {
  background: #667eea;
  color: white;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background: #5a6fd8;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #ffebee;
  color: #c62828;
  border-radius: 5px;
  text-align: center;
}
</style>
