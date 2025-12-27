<template>
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
    <div class="drawing-container" :ref="isMobile ? 'drawingContainerMobile' : 'drawingContainer'">
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
</template>

<script>
import drawingMixin from '@/mixins/drawingMixin'

// 创建一个自定义的 mixin，排除与 props 冲突的属性
const drawingPanelMixin = {
  data () {
    // 获取原始 mixin 的 data
    const originalData = drawingMixin.data ? drawingMixin.data() : {}
    // 移除与 props 冲突的属性（currentDrawer 和 drawerTimeRemaining 通过 props 传入）
    const { currentDrawer, drawerTimeRemaining, showDrawingPanel, ...restData } = originalData
    // 只保留不冲突的属性
    return {
      ...restData,
      showDrawingPanel: true // 在这个组件中总是 true
    }
  },
  methods: drawingMixin.methods || {}
}
// 如果有 beforeUnmount 钩子，添加到 mixin 中
if (drawingMixin.beforeUnmount) {
  drawingPanelMixin.beforeUnmount = drawingMixin.beforeUnmount
}

export default {
  name: 'DrawingPanel',
  mixins: [drawingPanelMixin],
  props: {
    currentDrawer: {
      type: String,
      default: null
    },
    username: {
      type: String,
      required: true
    },
    isConnected: {
      type: Boolean,
      default: false
    },
    isMobile: {
      type: Boolean,
      default: false
    },
    drawerTimeRemaining: {
      type: Number,
      default: 600
    },
    roomId: {
      type: Number,
      required: true
    },
    ChatMessage: {
      type: Object,
      default: null
    },
    WsEnvelope: {
      type: Object,
      default: null
    },
    ws: {
      type: WebSocket,
      default: null
    }
  },
  methods: {
    // 重写 exitDrawing 方法，确保可以正确访问 props
    exitDrawing () {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope || !this.ws || this.currentDrawer !== this.username) {
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: 10 // DRAWING_STOP
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send exit drawing:', err)
      }
    },
    // 重写 requestDrawing 方法
    requestDrawing () {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope || !this.ws) {
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: 7 // DRAWING_REQUEST
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send drawing request:', err)
      }
    },
    // 重写 clearDrawing 方法
    clearDrawing () {
      if (!this.isConnected || !this.ChatMessage || !this.WsEnvelope || !this.ws || this.currentDrawer !== this.username) {
        return
      }
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: 8 // DRAWING_CLEAR
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
        this.clearCanvas()
      } catch (err) {
        console.error('Failed to send clear drawing:', err)
      }
    },
    // 重写 sendDrawingData 方法
    sendDrawingData () {
      if (!this.canvas || !this.isConnected || !this.ChatMessage || !this.WsEnvelope || !this.ws || this.currentDrawer !== this.username) {
        return
      }
      const imageData = this.canvas.toDataURL('image/png')
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: imageData,
          timestamp: Date.now(),
          type: 6 // DRAWING
        })
        const envelope = this.WsEnvelope.create({ chat: message })
        const buffer = this.WsEnvelope.encode(envelope).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send drawing data:', err)
      }
    },
    // 重写 startDrawing 方法，确保使用正确的 props
    startDrawing (e) {
      if (this.currentDrawer !== this.username || !this.ctx || !this.canvas) {
        return
      }
      // 更新绘制样式（确保使用正确的工具）
      this.updateDrawingStyle()
      // 获取canvas的实际位置（考虑canvas-wrapper的偏移）
      const canvasRect = this.canvas.getBoundingClientRect()
      const clientX = e.touches ? e.touches[0].clientX : e.clientX
      const clientY = e.touches ? e.touches[0].clientY : e.clientY

      // 画布逻辑尺寸（ctx已经scale了dpr，所以使用逻辑尺寸）
      const CANVAS_WIDTH = 800
      const CANVAS_HEIGHT = 600

      // 将显示坐标转换为画布逻辑坐标
      const scaleX = CANVAS_WIDTH / canvasRect.width
      const scaleY = CANVAS_HEIGHT / canvasRect.height
      this.lastX = (clientX - canvasRect.left) * scaleX
      this.lastY = (clientY - canvasRect.top) * scaleY
      this.isDrawingActive = true
    },
    // 重写 stopDrawing 方法，确保调用正确的 sendDrawingData
    stopDrawing () {
      if (!this.isDrawingActive) return
      this.isDrawingActive = false
      // 发送最后一次画图数据
      if (this.drawingThrottleTimer) {
        clearTimeout(this.drawingThrottleTimer)
      }
      this.sendDrawingData()
    }
  },
  watch: {
    currentDrawer (newDrawer) {
      // 如果当前用户成为画画人，初始化画布
      if (newDrawer === this.username) {
        this.$nextTick(() => {
          this.initCanvas()
          window.addEventListener('resize', this.handleResize)
        })
      } else {
        // 如果不再是画画人，清理画布
        window.removeEventListener('resize', this.handleResize)
      }
    }
  },
  mounted () {
    // 如果当前用户是画画人，初始化画布
    if (this.currentDrawer === this.username) {
      this.$nextTick(() => {
        this.initCanvas()
        window.addEventListener('resize', this.handleResize)
      })
    }
  },
  beforeUnmount () {
    // 清理窗口大小变化监听器
    window.removeEventListener('resize', this.handleResize)

    // 清理画图节流定时器
    if (this.drawingThrottleTimer) {
      clearTimeout(this.drawingThrottleTimer)
    }
  }
}
</script>

<style scoped>
.drawing-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.drawing-header {
  padding: 1rem 1.5rem; /* 与chat-header的padding保持一致 */
  background: transparent;
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
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
  color: #2C3E50;
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
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  color: white;
  border: 3px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.request-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5B9BD5 0%, #4A90E2 100%);
  transform: translateY(-2px);
  box-shadow:
    0 6px 12px rgba(74, 144, 226, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.clear-btn {
  background: linear-gradient(135deg, #95A5A6 0%, #7F8C8D 100%);
  color: white;
  border: 3px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow:
    0 4px 8px rgba(149, 165, 166, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.clear-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #AAB7B8 0%, #95A5A6 100%);
  transform: translateY(-2px);
  box-shadow:
    0 6px 12px rgba(149, 165, 166, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.stop-btn {
  background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
  color: white;
  border: 3px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow:
    0 4px 8px rgba(231, 76, 60, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.stop-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #EC7063 0%, #E74C3C 100%);
  transform: translateY(-2px);
  box-shadow:
    0 6px 12px rgba(231, 76, 60, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.approve-btn {
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
}

.approve-btn:hover:not(:disabled) {
  background: #000000;
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
  background: #000000;
  color: white;
  border: var(--px-border, 3px) solid #000000;
  border-radius: var(--px-border-radius, 15px);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.approve-btn-inline:hover:not(:disabled) {
  background: #000000;
}

.approve-btn-inline:active:not(:disabled) {
  background: #000000;
}

.approve-btn-inline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #666666;
}

.drawing-tools {
  padding: 0.75rem 1rem;
  background: transparent;
  border-bottom: 1px solid rgba(200, 200, 200, 0.3);
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
  color: #2C3E50;
  font-size: 0.9rem;
  font-weight: 500;
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
  background: rgba(255, 255, 255, 0.9);
  color: #2C3E50;
  border: 3px solid rgba(200, 200, 200, 0.6);
  border-radius: 16px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgba(255, 255, 255, 0.8);
}

.width-btn:hover {
  border-color: #4A90E2;
  box-shadow:
    0 2px 4px rgba(74, 144, 226, 0.2),
    inset 0 2px 4px rgba(0, 0, 0, 0.05),
    0 1px 0 rgba(255, 255, 255, 0.8);
}

.width-btn.active {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  border-color: rgba(255, 255, 255, 0.8);
  color: white;
  box-shadow:
    0 4px 8px rgba(74, 144, 226, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
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

/* 移动端响应式样式 */
@media (max-width: 768px) {
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
