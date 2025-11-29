export default {
  data () {
    return {
      // 画图功能相关状态
      showDrawingPanel: false,
      currentDrawer: null, // 当前画画人的用户名
      drawerStartTime: null, // 画画人开始时间（毫秒时间戳）
      drawingRequests: [], // 申请画画列表
      drawerTimer: null, // 倒计时定时器
      drawerTimeRemaining: 600, // 剩余时间（秒），默认10分钟
      canvas: null, // 画布元素
      ctx: null, // 画布上下文
      isDrawingActive: false, // 是否正在绘制（鼠标/触摸按下状态）
      lastX: 0,
      lastY: 0,
      drawingColor: '#000000',
      drawingLineWidth: 3,
      drawingThrottleTimer: null, // 节流定时器
      isEraser: false // 是否使用橡皮擦
    }
  },

  methods: {
    // 画图功能相关方法
    toggleDrawingPanel () {
      this.showDrawingPanel = !this.showDrawingPanel
      if (this.showDrawingPanel) {
        this.$nextTick(() => {
          this.initCanvas()
          // 监听窗口大小变化，重新初始化画布
          window.addEventListener('resize', this.handleResize)
        })
      } else {
        window.removeEventListener('resize', this.handleResize)
      }
    },

    handleResize () {
      if (this.showDrawingPanel) {
        this.$nextTick(() => {
          this.initCanvas()
        })
      }
    },

    initCanvas () {
      // 根据设备类型选择canvas引用
      if (this.isMobile) {
        this.canvas = this.$refs.drawingCanvasMobile
      } else {
        this.canvas = this.$refs.drawingCanvas
      }
      if (!this.canvas) return
      this.ctx = this.canvas.getContext('2d')
      if (!this.ctx) return

      // 使用固定的画布逻辑尺寸，确保所有设备使用相同的逻辑尺寸
      // 标准尺寸：800x600 (4:3 比例)
      const CANVAS_WIDTH = 800
      const CANVAS_HEIGHT = 600
      const dpr = window.devicePixelRatio || 1

      // 设置canvas的实际像素尺寸（考虑设备像素比，用于高DPI屏幕）
      this.canvas.width = CANVAS_WIDTH * dpr
      this.canvas.height = CANVAS_HEIGHT * dpr

      // 获取drawing-container的尺寸，计算合适的显示尺寸
      // PC端：drawing-container -> canvas-wrapper -> canvas
      // 移动端：drawing-container -> canvas
      let container = this.canvas.parentElement

      // PC端：需要找到drawing-container（canvas-wrapper的父元素）
      if (container && container.classList.contains('canvas-wrapper')) {
        container = container.parentElement
      }

      // 确保找到了drawing-container
      if (!container || !container.classList.contains('drawing-container')) {
        // 如果找不到容器，使用默认尺寸
        this.canvas.style.width = CANVAS_WIDTH + 'px'
        this.canvas.style.height = CANVAS_HEIGHT + 'px'
        return
      }

      // 使用固定的显示尺寸，确保所有设备看到的画布显示尺寸一致
      // 这样可以保证所有设备看到的画布区域完全一致，不会出现边缘被裁剪的情况
      // 固定显示宽度：800px（与逻辑尺寸一致），高度根据4:3比例自动计算
      const FIXED_DISPLAY_WIDTH = 800
      const FIXED_DISPLAY_HEIGHT = 600

      // 检查容器尺寸，如果容器太小，则按比例缩小，但保持固定的宽高比
      this.$nextTick(() => {
        const containerRect = container.getBoundingClientRect()
        let containerWidth = containerRect.width
        let containerHeight = containerRect.height

        // PC端：canvas-wrapper有5px的padding，需要减去
        if (!this.isMobile) {
          containerWidth = containerWidth - 10 // 减去左右padding
          containerHeight = containerHeight - 10 // 减去上下padding
        }

        // 如果容器尺寸有效，检查是否需要缩放
        if (containerWidth > 0 && containerHeight > 0) {
          // 计算缩放比例，确保画布完整显示在容器内（使用contain策略）
          const scaleX = containerWidth / FIXED_DISPLAY_WIDTH
          const scaleY = containerHeight / FIXED_DISPLAY_HEIGHT
          // 选择较小的缩放比例，确保画布完整显示在容器内
          // 但不放大（最大为1），这样所有设备看到的画布显示尺寸一致（800x600或更小）
          const scale = Math.min(scaleX, scaleY, 1)

          // 设置canvas的CSS显示尺寸（固定比例，但适应小屏幕）
          const displayWidth = FIXED_DISPLAY_WIDTH * scale
          const displayHeight = FIXED_DISPLAY_HEIGHT * scale

          this.canvas.style.width = displayWidth + 'px'
          this.canvas.style.height = displayHeight + 'px'
        } else {
          // 如果容器尺寸无效，使用固定尺寸
          this.canvas.style.width = FIXED_DISPLAY_WIDTH + 'px'
          this.canvas.style.height = FIXED_DISPLAY_HEIGHT + 'px'
        }
      })

      // 重置变换矩阵，然后缩放上下文以匹配设备像素比
      this.ctx.setTransform(1, 0, 0, 1, 0, 0) // 重置变换
      this.ctx.scale(dpr, dpr)

      // 设置画布样式
      this.updateDrawingStyle()
    },

    startDrawing (e) {
      if (this.currentDrawer !== this.username || !this.ctx || !this.canvas) return
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

    draw (e) {
      if (!this.isDrawingActive || !this.ctx || !this.canvas) return
      e.preventDefault() // 防止默认行为

      // 更新绘制样式（可能在绘制过程中切换了橡皮擦）
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
      const currentX = (clientX - canvasRect.left) * scaleX
      const currentY = (clientY - canvasRect.top) * scaleY

      // 保存当前的合成模式
      const savedCompositeOperation = this.ctx.globalCompositeOperation

      // 根据是否使用橡皮擦设置合成模式
      if (this.isEraser) {
        this.ctx.globalCompositeOperation = 'destination-out'
      } else {
        this.ctx.globalCompositeOperation = 'source-over'
        this.ctx.strokeStyle = this.drawingColor
      }

      this.ctx.beginPath()
      this.ctx.moveTo(this.lastX, this.lastY)
      this.ctx.lineTo(currentX, currentY)
      this.ctx.stroke()

      // 恢复合成模式（虽然通常不需要，但为了安全）
      this.ctx.globalCompositeOperation = savedCompositeOperation

      this.lastX = currentX
      this.lastY = currentY

      // 节流发送画图数据（每50ms发送一次）
      if (this.drawingThrottleTimer) {
        clearTimeout(this.drawingThrottleTimer)
      }
      this.drawingThrottleTimer = setTimeout(() => {
        this.sendDrawingData()
      }, 50)
    },

    stopDrawing () {
      if (!this.isDrawingActive) return
      this.isDrawingActive = false
      // 发送最后一次画图数据
      if (this.drawingThrottleTimer) {
        clearTimeout(this.drawingThrottleTimer)
      }
      this.sendDrawingData()
    },

    sendDrawingData () {
      if (!this.canvas || !this.isConnected || !this.ChatMessage || this.currentDrawer !== this.username) return
      const imageData = this.canvas.toDataURL('image/png')
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: imageData,
          timestamp: Date.now(),
          type: 6 // DRAWING
        })
        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send drawing data:', err)
      }
    },

    handleDrawingData (imageData) {
      // 如果画布未初始化，先初始化
      if (!this.canvas || !this.ctx) {
        if (this.showDrawingPanel) {
          this.$nextTick(() => {
            this.initCanvas()
            // 延迟一下再加载图片，确保画布已初始化
            setTimeout(() => {
              this.loadImageToCanvas(imageData)
            }, 100)
          })
        }
        return
      }
      this.loadImageToCanvas(imageData)
    },

    loadImageToCanvas (imageData) {
      if (!this.canvas || !this.ctx || !imageData) return
      const img = new Image()
      img.onload = () => {
        // 确保画布已初始化
        if (!this.ctx) return
        // 使用固定的画布尺寸（800x600）
        const CANVAS_WIDTH = 800
        const CANVAS_HEIGHT = 600

        // 确保合成模式为正常模式，避免橡皮擦模式影响图片加载
        this.ctx.globalCompositeOperation = 'source-over'

        // 清空画布（使用固定尺寸，因为ctx已经scale了）
        this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

        // 绘制图片（使用固定尺寸，因为ctx已经scale了）
        this.ctx.drawImage(img, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
      }
      img.onerror = () => {
        console.error('Failed to load drawing image')
      }
      img.src = imageData
    },

    clearCanvas () {
      if (!this.ctx || !this.canvas) return
      // 使用固定的画布尺寸（800x600）
      const CANVAS_WIDTH = 800
      const CANVAS_HEIGHT = 600
      // 确保合成模式为正常模式
      this.ctx.globalCompositeOperation = 'source-over'
      // 使用固定尺寸清空画布，因为ctx已经scale了
      this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
    },

    requestDrawing () {
      if (!this.isConnected || !this.ChatMessage) return
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: 7 // DRAWING_REQUEST
        })
        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
      } catch (err) {
        console.error('Failed to send drawing request:', err)
      }
    },

    clearDrawing () {
      if (!this.isConnected || !this.ChatMessage || this.currentDrawer !== this.username) return
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: '',
          timestamp: Date.now(),
          type: 8 // DRAWING_CLEAR
        })
        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
        this.clearCanvas()
      } catch (err) {
        console.error('Failed to send clear drawing:', err)
      }
    },

    exitDrawing () {
      if (!this.isConnected || !this.ChatMessage || this.currentDrawer !== this.username) {
        console.log('exitDrawing: 条件检查失败', {
          isConnected: this.isConnected,
          hasChatMessage: !!this.ChatMessage,
          currentDrawer: this.currentDrawer,
          username: this.username
        })
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
        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
        console.log('exitDrawing: 已发送退出画画消息')
      } catch (err) {
        console.error('Failed to send exit drawing:', err)
      }
    },

    updateDrawingStyle () {
      if (!this.ctx) return
      // 设置基本绘制样式
      this.ctx.lineWidth = this.drawingLineWidth
      this.ctx.lineCap = 'round'
      this.ctx.lineJoin = 'round'
      // 注意：不在这里设置 globalCompositeOperation，而是在绘制时临时设置
      // 这样可以避免影响其他操作（如加载图片）
    },

    changeDrawingColor (color) {
      this.drawingColor = color
      this.isEraser = false // 选择颜色时关闭橡皮擦
      this.updateDrawingStyle()
    },

    changeDrawingLineWidth (width) {
      this.drawingLineWidth = width
      if (this.ctx) {
        this.ctx.lineWidth = width
      }
    },

    toggleEraser () {
      this.isEraser = !this.isEraser
      this.updateDrawingStyle()
    },

    approveDrawingRequest (requester) {
      if (!this.isConnected || !this.ChatMessage || this.currentDrawer !== this.username) return
      try {
        const message = this.ChatMessage.create({
          user: this.username,
          room_id: this.roomId,
          content: requester, // content包含被同意的用户名
          timestamp: Date.now(),
          type: 11 // DRAWING_REQUEST_APPROVE
        })
        const buffer = this.ChatMessage.encode(message).finish()
        this.ws.send(buffer)
        // 从申请列表中移除
        this.drawingRequests = this.drawingRequests.filter(u => u !== requester)
        // 隐藏聊天消息中的同意按钮（通过移除isDrawingRequest标记）
        const requestMessages = this.messages.filter(m => m.isDrawingRequest && m.user === requester)
        requestMessages.forEach(m => {
          m.isDrawingRequest = false
        })
      } catch (err) {
        console.error('Failed to send approve drawing request:', err)
      }
    },

    startDrawerTimer () {
      this.stopDrawerTimer() // 先停止之前的定时器
      this.drawerTimer = setInterval(() => {
        if (this.drawerTimeRemaining > 0) {
          this.drawerTimeRemaining--
        } else {
          this.stopDrawerTimer()
        }
      }, 1000)
    },

    stopDrawerTimer () {
      if (this.drawerTimer) {
        clearInterval(this.drawerTimer)
        this.drawerTimer = null
      }
    },

    formatDrawerTime (seconds) {
      const minutes = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  },

  beforeUnmount () {
    // 停止画画倒计时
    this.stopDrawerTimer()

    // 清理窗口大小变化监听器（画图相关）
    window.removeEventListener('resize', this.handleResize)

    // 清理画图节流定时器
    if (this.drawingThrottleTimer) {
      clearTimeout(this.drawingThrottleTimer)
    }
  }
}
