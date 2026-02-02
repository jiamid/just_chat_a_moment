<template>
  <div class="gobang-board-container">
    <canvas
      ref="canvas"
      class="gobang-canvas"
      :width="canvasSize"
      :height="canvasSize"
      @click="handleClick"
    ></canvas>
    <div class="gobang-info">
      <span class="role">
        你的身份：
        <span v-if="role === 'black'">黑子</span>
        <span v-else-if="role === 'white'">白子</span>
        <span v-else-if="role === 'waiting_player'">玩家</span>
        <span v-else>观战者</span>
      </span>
      <!-- 对局开始后才显示“轮到谁”，未开始时不展示 -->
      <template v-if="started">
        <span class="separator">｜</span>
        <span class="status">
          <span v-if="finished">
            对局结束：
            <span v-if="winner === 'black'">黑子获胜</span>
            <span v-else-if="winner === 'white'">白子获胜</span>
            <span v-else>平局</span>
          </span>
          <span v-else>
            轮到
            <span v-if="currentTurn === 1">黑子</span>
            <span v-else-if="currentTurn === 2">白子</span>
          </span>
        </span>
      </template>
      <!-- started === false 时，只展示“你的身份”一段 -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'GobangBoard',
  props: {
    board: {
      type: Array,
      required: true
    },
    role: {
      type: String,
      default: 'spectator' // 'black' | 'white' | 'spectator'
    },
    started: {
      type: Boolean,
      default: false
    },
    currentTurn: {
      type: Number,
      default: 1 // 1=黑, 2=白
    },
    finished: {
      type: Boolean,
      default: false
    },
    winner: {
      type: String,
      default: '' // 'black' | 'white' | ''
    },
    boardSize: {
      type: Number,
      default: 15
    },
    canvasSize: {
      type: Number,
      default: 480
    }
  },
  emits: ['cell-click'],
  mounted () {
    this.drawBoard()
  },
  watch: {
    board: {
      handler () {
        this.$nextTick(() => {
          this.drawBoard()
        })
      },
      deep: true
    },
    currentTurn () {
      this.$nextTick(() => {
        this.drawBoard()
      })
    },
    finished () {
      this.$nextTick(() => {
        this.drawBoard()
      })
    }
  },
  methods: {
    getCtx () {
      const canvas = this.$refs.canvas
      if (!canvas) return null
      const ctx = canvas.getContext('2d')
      return ctx
    },
    drawBoard () {
      const ctx = this.getCtx()
      if (!ctx) return

      const size = this.canvasSize
      const n = this.boardSize
      const padding = size * 0.06
      const gridSize = (size - padding * 2) / (n - 1)

      // 清空画布
      ctx.clearRect(0, 0, size, size)

      // 背景
      const gradient = ctx.createLinearGradient(0, 0, size, size)
      gradient.addColorStop(0, '#F5DEB3')
      gradient.addColorStop(1, '#D2B48C')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, size, size)

      // 外边框
      ctx.strokeStyle = '#8B4513'
      ctx.lineWidth = 4
      ctx.strokeRect(padding - 4, padding - 4, (n - 1) * gridSize + 8, (n - 1) * gridSize + 8)

      // 画网格
      ctx.strokeStyle = '#8B4513'
      ctx.lineWidth = 1
      ctx.beginPath()
      for (let i = 0; i < n; i++) {
        const pos = padding + i * gridSize
        // 横线
        ctx.moveTo(padding, pos)
        ctx.lineTo(padding + (n - 1) * gridSize, pos)
        // 竖线
        ctx.moveTo(pos, padding)
        ctx.lineTo(pos, padding + (n - 1) * gridSize)
      }
      ctx.stroke()

      // 星位（根据15x15标准棋盘）
      if (n === 15) {
        const starCoords = [
          [3, 3],
          [3, 7],
          [3, 11],
          [7, 3],
          [7, 7],
          [7, 11],
          [11, 3],
          [11, 7],
          [11, 11]
        ]
        ctx.fillStyle = '#8B4513'
        for (const [gx, gy] of starCoords) {
          const x = padding + gx * gridSize
          const y = padding + gy * gridSize
          ctx.beginPath()
          ctx.arc(x, y, gridSize * 0.1, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // 画棋子
      const radius = gridSize * 0.45
      for (let y = 0; y < n; y++) {
        for (let x = 0; x < n; x++) {
          const v = this.board[y] && this.board[y][x]
          if (!v) continue

          const cx = padding + x * gridSize
          const cy = padding + y * gridSize

          ctx.beginPath()
          ctx.arc(cx, cy, radius, 0, Math.PI * 2)

          if (v === 1) {
            // 黑子
            const g = ctx.createRadialGradient(
              cx - radius * 0.3,
              cy - radius * 0.3,
              radius * 0.2,
              cx,
              cy,
              radius
            )
            g.addColorStop(0, '#555555')
            g.addColorStop(1, '#000000')
            ctx.fillStyle = g
          } else if (v === 2) {
            // 白子
            const g = ctx.createRadialGradient(
              cx - radius * 0.3,
              cy - radius * 0.3,
              radius * 0.2,
              cx,
              cy,
              radius
            )
            g.addColorStop(0, '#FFFFFF')
            g.addColorStop(1, '#CCCCCC')
            ctx.fillStyle = g
          } else {
            continue
          }

          ctx.fill()
          ctx.strokeStyle = 'rgba(0,0,0,0.3)'
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }

      // 如果已经结束，高亮赢家文字区域由父组件处理即可，这里只做棋盘绘制
    },
    handleClick (event) {
      const canvas = this.$refs.canvas
      if (!canvas) return

      const rect = canvas.getBoundingClientRect()
      // 处理画布缩放（CSS 缩放与实际像素不一致时，需要按比例换算）
      const scaleX = canvas.width / rect.width
      const scaleY = canvas.height / rect.height
      const x = (event.clientX - rect.left) * scaleX
      const y = (event.clientY - rect.top) * scaleY

      const size = this.canvasSize
      const n = this.boardSize
      const padding = size * 0.06
      const gridSize = (size - padding * 2) / (n - 1)

      // 超出棋盘区域则忽略
      if (
        x < padding - gridSize * 0.5 ||
        x > padding + (n - 1) * gridSize + gridSize * 0.5 ||
        y < padding - gridSize * 0.5 ||
        y > padding + (n - 1) * gridSize + gridSize * 0.5
      ) {
        return
      }

      // 映射到最近的交叉点
      const gx = Math.round((x - padding) / gridSize)
      const gy = Math.round((y - padding) / gridSize)

      if (gx < 0 || gx >= n || gy < 0 || gy >= n) return

      this.$emit('cell-click', { x: gx, y: gy })
    }
  }
}
</script>

<style scoped>
.gobang-board-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  gap: 0.5rem;
}

.gobang-canvas {
  max-width: 100%;
  height: auto;
  border-radius: 16px;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.15),
    0 4px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  background: #f5deb3;
}

.gobang-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  font-size: 0.9rem;
  color: #2c3e50;
}

.gobang-info .role {
  font-weight: 600;
}

.gobang-info .separator {
  color: #999;
}

.gobang-info .status {
  color: #555;
}
</style>
