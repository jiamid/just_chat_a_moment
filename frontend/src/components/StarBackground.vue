<template>
  <canvas ref="starCanvas" class="star-canvas"></canvas>
</template>

<script>
export default {
  name: 'StarBackground',
  data () {
    return {
      canvas: null,
      ctx: null,
      stars: [],
      angle: 0,
      animationId: null,
      width: 0,
      height: 0
    }
  },
  mounted () {
    this.initCanvas()
    this.initStars()
    this.startAnimation()
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
      this.canvas = this.$refs.starCanvas
      this.ctx = this.canvas.getContext('2d')
      this.width = this.canvas.width = window.innerWidth
      this.height = this.canvas.height = window.innerHeight
    },
    initStars () {
      this.stars = []
      for (let i = 0; i < 200; i++) {
        this.stars.push({
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          r: Math.random() * 1.5,
          d: Math.random() * 0.5
        })
      }
    },
    handleResize () {
      this.width = this.canvas.width = window.innerWidth
      this.height = this.canvas.height = window.innerHeight
      // 重新初始化星星位置以适应新尺寸
      this.initStars()
    },
    draw () {
      this.ctx.clearRect(0, 0, this.width, this.height)
      this.ctx.fillStyle = 'white'
      this.ctx.beginPath()
      for (let i = 0; i < this.stars.length; i++) {
        const s = this.stars[i]
        this.ctx.moveTo(s.x, s.y)
        this.ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2, true)
      }
      this.ctx.fill()
      this.update()
      this.animationId = requestAnimationFrame(() => this.draw())
    },
    update () {
      this.angle += 0.01
      for (let i = 0; i < this.stars.length; i++) {
        const s = this.stars[i]
        s.y += Math.sin(this.angle) * 0.2
        s.x += Math.cos(this.angle) * 0.2
        if (s.x < 0) s.x = this.width
        if (s.x > this.width) s.x = 0
        if (s.y < 0) s.y = this.height
        if (s.y > this.height) s.y = 0
      }
    },
    startAnimation () {
      this.draw()
    }
  }
}
</script>

<style scoped>
.star-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #0a0a2a;
  z-index: -1;
  display: block;
}
</style>
