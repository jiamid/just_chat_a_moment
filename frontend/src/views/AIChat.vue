<template>
  <div class="ai-chat-container">
    <ClashBackground />

    <div class="content-wrapper">
      <!-- 顶部：标题 + 返回按钮 -->
      <div class="top-bar">
        <div class="title-group">
          <h1 class="title">麦当劳优惠券 AI 助手</h1>
          <p class="subtitle">
            连接麦当劳官方 MCP 服务，智能查询活动日历、优惠券，并帮你一键领券。
          </p>
        </div>
        <button class="back-btn" @click="$router.push('/')">
          ← 返回大厅
        </button>
      </div>

      <!-- MCP Token 设置 -->
      <div class="token-panel">
        <h2 class="panel-title">MCP Token 设置</h2>
        <p class="panel-desc">
          请填写你在
          <a
            href="https://github.com/M-China/mcd-mcp-server"
            target="_blank"
            rel="noopener noreferrer"
          >mcd-mcp-server</a>
          申请到的 MCP Token。Token 会安全存储在服务端（按账号绑定），用于后续 AI 领券与查询。
        </p>
        <div class="token-row">
          <input
            v-model="mcpToken"
            :type="showToken ? 'text' : 'password'"
            class="token-input"
            placeholder="请输入你的 McDonald's MCP Token"
          />
          <button class="token-action-btn" type="button" @click="toggleShowToken">
            {{ showToken ? '隐藏' : '显示' }}
          </button>
          <button class="token-action-btn primary" type="button" @click="saveToken">
            保存
          </button>
        </div>
        <div v-if="tokenSavedTip" class="token-tip">
          {{ tokenSavedTip }}
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="chat-layout">
        <div class="chat-window" ref="chatWindow">
          <!-- 顶部系统提示条（错误等），样式参考 Chat.vue 的 system-notification -->
          <div v-if="error" class="system-notification">
            {{ error }}
          </div>
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['chat-message', msg.role]"
          >
            <div class="avatar">
              <span v-if="msg.role === 'assistant'">🍟</span>
              <span v-else>🧑</span>
            </div>
            <div class="bubble">
              <div class="bubble-role">
                {{ msg.role === 'assistant' ? '麦麦助手' : (username || '你') }}
              </div>
              <div class="bubble-content">
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>

        <form class="input-bar" @submit.prevent="handleSend">
          <input
            v-model="userInput"
            class="message-input"
            type="text"
            :placeholder="inputPlaceholder"
            :disabled="loading"
            @keyup.enter.exact.prevent="handleSend"
          />
          <button
            type="button"
            class="send-btn"
            :disabled="loading || !userInput.trim()"
            @click="handleSend"
          >
            {{ loading ? '思考中...' : '发送' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import ClashBackground from '@/components/ClashBackground.vue'
import { api } from '@/utils/request.js'

export default {
  name: 'AIChat',
  components: {
    ClashBackground
  },
  data () {
    return {
      username: localStorage.getItem('username') || '',
      mcpToken: '',
      showToken: false,
      tokenSavedTip: '',
      userInput: '',
      loading: false,
      error: '',
      messages: [
        {
          role: 'assistant',
          content:
            '你好，我是麦当劳优惠券 AI 助手 🍟。我可以帮你查询麦麦日历、查看和领取优惠券。先在上方填好 MCP Token，然后问我：“帮我看看今天有什么优惠？” 或 “帮我一键领券”。'
        }
      ]
    }
  },
  computed: {
    inputPlaceholder () {
      if (!this.mcpToken) {
        return '请先填写并保存 MCP Token（服务端会校验），再开始聊天'
      }
      return '例如：帮我看看今天有什么优惠券 / 帮我一键领券'
    }
  },
  async mounted () {
    // 进入页面时，从服务端拉取一次已保存的 Token（如果有）
    try {
      const resp = await api.mcd.getToken()
      this.mcpToken = resp.data?.token || ''
      if (this.mcpToken) {
        // 同步一份到本地，便于下次打开时占位
        localStorage.setItem('mcd_mcp_token', this.mcpToken)
      } else {
        const localToken = localStorage.getItem('mcd_mcp_token') || ''
        if (localToken) {
          this.mcpToken = localToken
        }
      }
    } catch (err) {
      console.error('获取 MCP Token 失败:', err)
    }
  },
  methods: {
    toggleShowToken () {
      this.showToken = !this.showToken
    },
    async saveToken () {
      if (!this.mcpToken) {
        this.showError('请先输入 MCP Token')
        return
      }
      this.loading = true
      this.error = ''
      try {
        const resp = await api.mcd.saveToken({ token: this.mcpToken })
        this.mcpToken = resp.data?.token || this.mcpToken
        localStorage.setItem('mcd_mcp_token', this.mcpToken || '')
        this.tokenSavedTip = '已保存到服务器，登录后可随时使用。'
        setTimeout(() => {
          this.tokenSavedTip = ''
        }, 2000)
      } catch (err) {
        this.showError(err.message || '保存 MCP Token 失败，请稍后重试')
      } finally {
        this.loading = false
      }
    },
    showError (message) {
      this.error = message || ''
      if (this.error) {
        setTimeout(() => {
          this.error = ''
        }, 3000)
      }
    },
    appendMessage (role, content) {
      this.messages.push({ role, content })
      this.$nextTick(() => {
        const el = this.$refs.chatWindow
        if (el) {
          el.scrollTop = el.scrollHeight
        }
      })
    },
    async handleSend () {
      if (!this.userInput.trim() || this.loading) return
      if (!this.mcpToken) {
        this.showError('请先填写并保存 MCP Token 后再开始聊天')
        return
      }

      const content = this.userInput.trim()
      this.appendMessage('user', content)
      this.userInput = ''
      this.loading = true
      this.error = ''

      try {
        const resp = await api.mcd.chat({
          message: content
        })
        const answer = resp.data?.answer || '麦麦助手没有返回内容，请稍后重试。'
        this.appendMessage('assistant', answer)
      } catch (err) {
        this.showError(err.message || '请求失败，请检查网络、Token 或联系管理员。')
        this.appendMessage('assistant', '连接麦当劳 MCP 服务失败，请检查 Token 或稍后重试。')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.ai-chat-container {
  position: relative;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.content-wrapper {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem 1.5rem;
  box-sizing: border-box;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.title-group {
  max-width: 70%;
}

.title {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 900;
  color: #fff8dc;
  text-shadow:
    2px 2px 0 rgba(184, 134, 11, 0.9),
    -1px -1px 0 rgba(255, 255, 255, 1);
}

.subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: #ecf0f1;
  opacity: 0.9;
}

.back-btn {
  border: 3px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(135deg, #ffffffaa, #ffffffff);
  border-radius: 999px;
  padding: 0.5rem 1.2rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.token-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.9));
  border-radius: 24px;
  border: 4px solid rgba(255, 255, 255, 0.9);
  padding: 1.25rem 1.5rem;
  box-shadow:
    0 10px 20px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.panel-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: #2c3e50;
}

.panel-desc {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.panel-desc a {
  color: #e74c3c;
  font-weight: 600;
}

.token-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}

.token-input {
  flex: 1;
  min-width: 220px;
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  border: 3px solid rgba(200, 200, 200, 0.7);
  font-size: 0.95rem;
  box-sizing: border-box;
}

.token-action-btn {
  padding: 0.65rem 0.9rem;
  border-radius: 12px;
  border: 3px solid rgba(200, 200, 200, 0.7);
  background: rgba(245, 245, 245, 0.9);
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
}

.token-action-btn.primary {
  border-color: rgba(255, 165, 0, 0.9);
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #2c3e50;
}

.token-tip {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #27ae60;
}

.chat-layout {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-window {
  flex: 1;
  min-height: 0;
  padding: 1rem 1.25rem;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 4px solid rgba(255, 255, 255, 0.9);
  overflow-y: auto;
  box-shadow:
    0 10px 20px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.system-notification {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  min-height: 30px;
  margin-bottom: 0.5rem;
  padding: 8px 16px;
  background: #000000;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: 15px;
  border: 3px solid #000000;
  box-sizing: border-box;
}

.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #ffe082;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.chat-message.user .avatar {
  background: #4a90e2;
  color: #fff;
}

.bubble {
  max-width: 80%;
  background: #ffffff;
  border-radius: 16px;
  padding: 0.6rem 0.75rem;
  border: 2px solid rgba(0, 0, 0, 0.05);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.chat-message.user .bubble {
  background: #e3f2fd;
}

.bubble-role {
  font-size: 0.75rem;
  font-weight: 700;
  color: #7f8c8d;
  margin-bottom: 0.15rem;
}

.bubble-content {
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.message-input {
  flex: 1;
  min-width: 0;
  padding: 0.75rem 1rem;
  border-radius: 16px;
  border: 4px solid rgb(255, 255, 255);
  font-size: 1rem;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #2c3e50;
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
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
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
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5b9bd5 0%, #4a90e2 100%);
  transform: translateY(-2px);
}

.send-btn:disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #cccccc 0%, #999999 100%);
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 1.25rem 1rem;
    gap: 1rem;
  }

  .top-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .title-group {
    max-width: 100%;
  }

  .title {
    font-size: 1.4rem;
  }

  .chat-window {
    padding: 0.75rem;
  }
}
</style>
