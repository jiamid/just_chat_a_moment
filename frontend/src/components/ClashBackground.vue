<template>
  <canvas ref="gridCanvas" class="grid-canvas"></canvas>
</template>

<script>
export default {
  name: 'ClashBackground',
  data () {
    return {
      canvas: null,
      ctx: null,
      animationId: null,
      width: 0,
      height: 0,
      tileSize: 80, // 方块大小
      gap: 4 // 方块之间的间隙
    }
  },
  mounted () {
    this.initCanvas()
    this.draw()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount () {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
    }
    window.removeEventListener('resize', this.handleResize)
  },
  methods: {
    initCanvas () {
      this.canvas = this.$refs.gridCanvas
      this.ctx = this.canvas.getContext('2d')
      // 启用抗锯齿
      this.ctx.imageSmoothingEnabled = true
      this.ctx.imageSmoothingQuality = 'high'
      this.width = this.canvas.width = window.innerWidth
      this.height = this.canvas.height = window.innerHeight
    },
    handleResize () {
      this.width = this.canvas.width = window.innerWidth
      this.height = this.canvas.height = window.innerHeight
      // 重新启用抗锯齿
      this.ctx.imageSmoothingEnabled = true
      this.ctx.imageSmoothingQuality = 'high'
      this.draw()
    },
    draw () {
      // 清除画布
      this.ctx.clearRect(0, 0, this.width, this.height)

      // 绘制渐变背景（深蓝到蓝）
      const gradient = this.ctx.createLinearGradient(0, 0, 0, this.height)
      gradient.addColorStop(0, '#3C7DBB') // 深蓝 r:0.235, g:0.489, b:0.733
      gradient.addColorStop(1, '#082B56') // 蓝 r:0.030, g:0.170, b:0.336
      this.ctx.fillStyle = gradient
      this.ctx.fillRect(0, 0, this.width, this.height)

      // 计算中心点
      const centerX = this.width / 2
      const centerY = this.height / 2

      // 计算需要绘制的方块数量（考虑旋转45度后需要覆盖整个屏幕）
      const diagonal = Math.sqrt(this.width * this.width + this.height * this.height)
      const tileWithGap = this.tileSize + this.gap
      const cols = Math.ceil(diagonal / tileWithGap) + 2
      const rows = Math.ceil(diagonal / tileWithGap) + 2

      // 保存上下文
      this.ctx.save()

      // 移动到中心点并旋转45度
      this.ctx.translate(centerX, centerY)
      this.ctx.rotate(Math.PI / 4) // 45度

      // 定义颜色（浅蓝系列用于方格）
      const ultraLightBlue = '#44AEE4' // 浅浅蓝 r:0.267, g:0.682, b:0.896
      const lightBlue = '#3686BD' // 浅蓝（调深）原 r:0.248, g:0.618, b:0.870

      // 绘制方块网格
      const startX = -(cols * tileWithGap) / 2
      const startY = -(rows * tileWithGap) / 2

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = startX + col * tileWithGap
          const y = startY + row * tileWithGap

          // 根据行列索引决定颜色（棋盘格效果，使用超浅蓝和浅蓝）
          const isLight = (row + col) % 2 === 0
          const baseColor = isLight ? ultraLightBlue : lightBlue

          // 绘制带浮雕效果的圆角矩形
          this.drawRoundedRectWithRelief(x, y, this.tileSize, this.tileSize, 8, baseColor)
        }
      }

      // 恢复上下文
      this.ctx.restore()
    },
    drawRoundedRect (x, y, width, height, radius) {
      this.ctx.beginPath()
      // 使用 arc 绘制更平滑的圆角
      // 左上角
      this.ctx.moveTo(x + radius, y)
      // 上边
      this.ctx.lineTo(x + width - radius, y)
      // 右上角
      this.ctx.arc(x + width - radius, y + radius, radius, -Math.PI / 2, 0, false)
      // 右边
      this.ctx.lineTo(x + width, y + height - radius)
      // 右下角
      this.ctx.arc(x + width - radius, y + height - radius, radius, 0, Math.PI / 2, false)
      // 下边
      this.ctx.lineTo(x + radius, y + height)
      // 左下角
      this.ctx.arc(x + radius, y + height - radius, radius, Math.PI / 2, Math.PI, false)
      // 左边
      this.ctx.lineTo(x, y + radius)
      // 左上角
      this.ctx.arc(x + radius, y + radius, radius, Math.PI, -Math.PI / 2, false)
      this.ctx.closePath()
      this.ctx.fill()
    },
    // 将十六进制颜色转换为RGB
    hexToRgb (hex) {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result
        ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
          }
        : null
    },
    // 将RGB转换为十六进制
    rgbToHex (r, g, b) {
      return '#' + [r, g, b].map(x => {
        const hex = Math.round(x).toString(16)
        return hex.length === 1 ? '0' + hex : hex
      }).join('')
    },
    // 绘制带浮雕效果的圆角矩形
    drawRoundedRectWithRelief (x, y, width, height, radius, baseColor) {
      // 保存上下文
      this.ctx.save()

      // 绘制阴影
      this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)'
      this.ctx.shadowBlur = 8
      this.ctx.shadowOffsetX = 2
      this.ctx.shadowOffsetY = 2

      // 创建渐变（从左上亮到右下暗，模拟光照）
      const gradient = this.ctx.createLinearGradient(x, y, x + width, y + height)

      // 将基础颜色转换为RGB以便调整亮度
      const rgb = this.hexToRgb(baseColor)
      if (rgb) {
        // 左上角更亮（高光）
        const lightR = Math.min(255, rgb.r + 30)
        const lightG = Math.min(255, rgb.g + 30)
        const lightB = Math.min(255, rgb.b + 30)
        const lightColor = this.rgbToHex(lightR, lightG, lightB)

        // 右下角更暗（阴影）
        const darkR = Math.max(0, rgb.r - 40)
        const darkG = Math.max(0, rgb.g - 40)
        const darkB = Math.max(0, rgb.b - 40)
        const darkColor = this.rgbToHex(darkR, darkG, darkB)

        gradient.addColorStop(0, lightColor)
        gradient.addColorStop(0.5, baseColor)
        gradient.addColorStop(1, darkColor)
      } else {
        gradient.addColorStop(0, baseColor)
        gradient.addColorStop(1, baseColor)
      }

      // 绘制圆角矩形
      this.ctx.beginPath()
      this.ctx.moveTo(x + radius, y)
      this.ctx.lineTo(x + width - radius, y)
      this.ctx.arc(x + width - radius, y + radius, radius, -Math.PI / 2, 0, false)
      this.ctx.lineTo(x + width, y + height - radius)
      this.ctx.arc(x + width - radius, y + height - radius, radius, 0, Math.PI / 2, false)
      this.ctx.lineTo(x + radius, y + height)
      this.ctx.arc(x + radius, y + height - radius, radius, Math.PI / 2, Math.PI, false)
      this.ctx.lineTo(x, y + radius)
      this.ctx.arc(x + radius, y + radius, radius, Math.PI, -Math.PI / 2, false)
      this.ctx.closePath()

      this.ctx.fillStyle = gradient
      this.ctx.fill()

      // 清除阴影
      this.ctx.shadowColor = 'transparent'
      this.ctx.shadowBlur = 0
      this.ctx.shadowOffsetX = 0
      this.ctx.shadowOffsetY = 0

      // 添加高光边框（左上角）
      this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
      this.ctx.lineWidth = 1
      this.ctx.beginPath()
      this.ctx.moveTo(x + radius, y)
      this.ctx.lineTo(x + width - radius, y)
      this.ctx.arc(x + width - radius, y + radius, radius, -Math.PI / 2, 0, false)
      this.ctx.stroke()

      // 恢复上下文
      this.ctx.restore()
    }
  }
}
</script>

<style scoped>
.grid-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  display: block;
}
</style>
