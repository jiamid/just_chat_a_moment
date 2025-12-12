<template>
  <div class="content-section" ref="contentSection" @click="handleClick">
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as THREE from 'three'
import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'

export default {
  name: 'ParticleText',
  props: {
    text: {
      type: String,
      required: true
    }
  },
  data () {
    return {
      // Three.js 相关
      scene: null,
      camera: null,
      renderer: null,
      particleSystem: null,
      particles: null,
      originalParticles: null, // 保存原始粒子位置（字符串排列）
      scatteredParticles: null, // 保存均匀散开的粒子位置
      currentParticlePositions: null, // 当前粒子位置数组（用于实时更新）
      particleColors: null, // 粒子颜色数组（每个粒子的 RGB 值）
      originalColors: null, // 原始颜色（字符串模式：黑色）
      scatteredColors: null, // 散开时的随机彩色
      animationId: null,
      // MediaPipe 相关
      handLandmarker: null,
      video: null,
      mediaPipeInitialized: false,
      // 交互状态
      isScattered: false, // 是否为散开模式（点击切换时使用）
      // 手势控制
      currentGesture: 'rock', // 当前手势：'rock'(石头), 'paper'(布), 'tree'(树)
      gestureMode: 'rock', // 手势模式
      // 动画相关
      animationTime: 0, // 动画时间（用于自旋）
      rotationX: 0, // X轴旋转角度
      rotationY: 0, // Y轴旋转角度
      rotationDirection: 1, // 旋转方向：1为正向，-1为反向
      // 手势位置跟踪（用于检测水平移动）
      lastHandX: null, // 上一帧手的位置X坐标
      handPositionHistory: [], // 手的位置历史（用于平滑检测）
      // 粒子位置
      globeParticles: null, // 地球仪模式粒子位置（球面分布）
      treeParticles: null, // 树模式粒子位置
      globeColors: null, // 地球仪颜色
      treeColors: null, // 树颜色
      // 花瓣飘落
      petals: [], // 花瓣数组
      petalSystem: null // 花瓣粒子系统
    }
  },
  watch: {
    text: {
      handler (newVal) {
        // 当文字变化时，重新创建粒子文字
        if (this.particleSystem) {
          this.createParticleText(newVal)
        }
      },
      immediate: false
    }
  },
  async mounted () {
    // 初始化 Three.js 粒子化文字（延迟确保 DOM 已渲染）
    setTimeout(async () => {
      try {
        await this.initParticleText()
      } catch (err) {
        console.error('Three.js 初始化失败:', err)
      }
    }, 200)
    // 自动初始化 MediaPipe 手势识别
    setTimeout(async () => {
      try {
        await this.initMediaPipe()
        // initMediaPipe 成功时会设置 mediaPipeInitialized = true
      } catch (err) {
        console.warn('MediaPipe 初始化失败（不影响粒子显示）:', err)
        // 失败时不设置 mediaPipeInitialized，保持为 false，允许点击切换
      }
    }, 500)
  },
  beforeUnmount () {
    // 清理 Three.js
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
    }
    if (this.renderer) {
      this.renderer.dispose()
    }
    if (this.particleSystem) {
      this.scene.remove(this.particleSystem)
      this.particleSystem.geometry.dispose()
      this.particleSystem.material.dispose()
    }
    window.removeEventListener('resize', this.handleParticleResize)
    // 清理 MediaPipe
    if (this.handLandmarker) {
      this.handLandmarker.close()
      this.handLandmarker = null
    }
    if (this.video && this.video.srcObject) {
      this.video.srcObject.getTracks().forEach(track => track.stop())
    }
    if (this.video && this.video.parentNode) {
      this.video.parentNode.removeChild(this.video)
    }
  },
  methods: {
    // 初始化 Three.js 粒子化文字
    async initParticleText () {
      await this.$nextTick()
      // 等待容器渲染完成
      await new Promise(resolve => setTimeout(resolve, 100))

      const container = this.$refs.contentSection
      const canvas = this.$refs.particleCanvas
      if (!container || !canvas) {
        console.error('容器或画布未找到')
        return
      }

      const width = container.clientWidth
      const height = container.clientHeight

      if (width === 0 || height === 0) {
        console.error('容器尺寸为0:', { width, height })
        // 如果尺寸为0，使用默认尺寸
        const defaultWidth = 800
        const defaultHeight = 600
        this.initWithSize(defaultWidth, defaultHeight, container, canvas)
        return
      }

      this.initWithSize(width, height, container, canvas)
    },

    // 使用指定尺寸初始化
    initWithSize (width, height, container, canvas) {
      console.log('初始化 Three.js，尺寸:', { width, height })

      // 创建场景（使用 markRaw 避免 Vue 响应式代理）
      this.scene = markRaw(new THREE.Scene())
      this.scene.background = new THREE.Color(0xffffff)

      // 创建相机（使用 markRaw 避免 Vue 响应式代理）
      const aspect = width / height || 1
      this.camera = markRaw(new THREE.PerspectiveCamera(75, aspect, 0.1, 1000))
      this.camera.position.z = 400

      // 创建渲染器（使用 markRaw 避免 Vue 响应式代理）
      this.renderer = markRaw(new THREE.WebGLRenderer({ canvas, antialias: true }))
      this.renderer.setSize(width, height)
      this.renderer.setPixelRatio(window.devicePixelRatio)

      // 创建粒子文字
      this.createParticleText(this.text)

      // 开始动画
      this.animate()

      // 监听窗口大小变化
      window.addEventListener('resize', this.handleParticleResize)
    },

    // 创建粒子化文字
    createParticleText (text) {
      // 清除旧的粒子系统
      if (this.particleSystem) {
        this.scene.remove(this.particleSystem)
        this.particleSystem.geometry.dispose()
        this.particleSystem.material.dispose()
      }

      // 使用 Canvas 2D 渲染文字获取像素数据
      const canvas2d = document.createElement('canvas')
      const ctx2d = canvas2d.getContext('2d')
      const fontSize = 450 // 增大字体
      canvas2d.width = 1800 // 增大画布宽度以容纳更大的字体
      canvas2d.height = 900 // 增大画布高度以容纳更大的字体

      ctx2d.fillStyle = '#000000'
      ctx2d.font = `bold ${fontSize}px Arial`
      ctx2d.textAlign = 'center'
      ctx2d.textBaseline = 'middle'
      ctx2d.fillText(text, canvas2d.width / 2, canvas2d.height / 2)

      // 获取像素数据
      const imageData = ctx2d.getImageData(0, 0, canvas2d.width, canvas2d.height)
      const data = imageData.data
      const particles = []

      // 采样像素创建粒子
      const step = 8 // 采样步长，控制粒子密度（增大以减少粒子数量，提升性能）
      for (let y = 0; y < canvas2d.height; y += step) {
        for (let x = 0; x < canvas2d.width; x += step) {
          const index = (y * canvas2d.width + x) * 4
          const alpha = data[index + 3]
          if (alpha > 128) {
            particles.push(
              (x - canvas2d.width / 2) * 0.3,
              -(y - canvas2d.height / 2) * 0.3,
              0
            )
          }
        }
      }

      // 保存原始粒子位置（字符串模式的目标位置）
      this.originalParticles = [...particles]

      // 创建均匀散开的粒子位置（用于散开模式）
      const scatteredParticles = []
      const particleCount = particles.length / 3
      const sphereRadius = 300 // 散开球体半径（增大以覆盖整个画面）

      // 初始化颜色数组
      const originalColors = [] // 原始颜色（字符串模式：黑色）
      const scatteredColors = [] // 散开模式：随机彩色

      for (let i = 0; i < particleCount; i++) {
        // 在球体内随机分布
        const theta = Math.random() * Math.PI * 2 // 水平角
        const phi = Math.acos(Math.random() * 2 - 1) // 垂直角
        const r = sphereRadius * Math.cbrt(Math.random()) // 在球体内均匀分布

        scatteredParticles.push(
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.sin(phi) * Math.sin(theta),
          r * Math.cos(phi)
        )

        // 原始颜色：黑色 (0, 0, 0)
        originalColors.push(0, 0, 0)

        // 散开颜色：随机彩色 (0-1 的 RGB 值)
        scatteredColors.push(
          Math.random(), // R
          Math.random(), // G
          Math.random() // B
        )
      }

      this.scatteredParticles = scatteredParticles
      this.originalColors = originalColors
      this.scatteredColors = scatteredColors
      this.particleColors = [...originalColors] // 初始为黑色

      // 创建地球仪粒子位置（球面均匀分布）
      const globeParticles = []
      const globeColors = []
      const globeRadius = 250 // 地球仪半径

      for (let i = 0; i < particleCount; i++) {
        // 在球面上均匀分布（使用斐波那契螺旋）
        const y = 1 - (i / (particleCount - 1)) * 2 // -1 到 1
        const radius = Math.sqrt(1 - y * y)
        const theta = Math.PI * (3 - Math.sqrt(5)) * i // 黄金角度
        const x = Math.cos(theta) * radius
        const z = Math.sin(theta) * radius

        globeParticles.push(
          x * globeRadius,
          y * globeRadius,
          z * globeRadius
        )

        // 地球仪颜色：根据位置生成渐变色彩（类似地球）
        const lat = Math.asin(y)
        const lon = theta
        // 模拟地球颜色：蓝色海洋 + 绿色陆地
        const isLand = Math.sin(lat * 3) * Math.cos(lon * 2) > 0.2
        if (isLand) {
          // 绿色陆地
          globeColors.push(0.2, 0.6, 0.3)
        } else {
          // 蓝色海洋
          globeColors.push(0.1, 0.3, 0.7)
        }
      }
      this.globeParticles = globeParticles
      this.globeColors = globeColors

      // 创建3D圣诞树模型（参考GitHub实现，更美观）
      const treeParticles = []
      const treeColors = []

      // 计算屏幕尺寸，使树占据至少半个屏幕
      const screenHeight = 300 // 目标树高度（半个屏幕）
      const screenWidth = 400 // 目标树宽度（半个屏幕）

      // 树的总高度和宽度
      const totalTreeHeight = screenHeight
      const totalTreeWidth = screenWidth

      // 树干参数（圣诞树树干较短）
      const trunkHeight = totalTreeHeight * 0.12 // 树干占12%高度
      const trunkBaseWidth = totalTreeWidth * 0.05 // 树干底部宽度
      const trunkTopWidth = totalTreeWidth * 0.03 // 树干顶部宽度

      // 圣诞树冠参数（参考实现：更饱满的圆锥形）
      const crownHeight = totalTreeHeight * 0.88 // 树冠占88%高度
      const crownBaseRadius = totalTreeWidth * 0.48 // 树冠底部半径（更宽）
      const crownTopRadius = totalTreeWidth * 0.02 // 树冠顶部半径（更尖）

      // 分配粒子：2% 树干，73% 树冠叶子，15% 装饰品，8% 星星（立体五角星）
      const trunkParticleCount = Math.floor(particleCount * 0.02)
      const decorationParticleCount = Math.floor(particleCount * 0.15)
      const starParticleCount = Math.floor(particleCount * 0.08)
      const crownParticleCount = particleCount - trunkParticleCount - decorationParticleCount - starParticleCount

      // 生成树干粒子（圆柱形）
      for (let i = 0; i < trunkParticleCount; i++) {
        const heightRatio = i / trunkParticleCount // 0 到 1
        const height = heightRatio * trunkHeight
        const radius = trunkBaseWidth * (1 - heightRatio) + trunkTopWidth * heightRatio

        // 在圆周上均匀分布
        const angle = (i * 137.5) % (Math.PI * 2) // 黄金角度螺旋
        const radialPos = Math.sqrt(Math.random()) * radius // 均匀分布在圆内

        const x = Math.cos(angle) * radialPos
        const y = -totalTreeHeight / 2 + height // 从底部开始
        const z = Math.sin(angle) * radialPos

        treeParticles.push(x, y, z)

        // 树干颜色：深棕色（参考实现）
        const r = 0.35 + Math.random() * 0.15
        const g = 0.15 + Math.random() * 0.1
        const b = 0.08 + Math.random() * 0.05
        treeColors.push(r, g, b)
      }

      // 生成圣诞树冠粒子（圆锥形，深绿色，更饱满）
      // 参考实现：使用更深的绿色渐变，从EMERALD_DEEP到EMERALD_LIGHT
      // EMERALD_DEEP: #003808, EMERALD_MID: #005410, EMERALD_LIGHT: #006018
      const layers = Math.max(10, Math.floor(crownParticleCount / 50)) // 至少10层，更细腻
      const particlesPerLayer = Math.floor(crownParticleCount / layers)
      let generatedCrownCount = 0

      for (let layer = 0; layer < layers && generatedCrownCount < crownParticleCount; layer++) {
        const layerProgress = layer / (layers - 1) // 0 到 1
        const height = trunkHeight + layerProgress * crownHeight
        const heightRatio = layerProgress

        // 计算该层的半径范围
        const radiusFactor = 1 - heightRatio
        const outerRadius = crownBaseRadius * radiusFactor + crownTopRadius * heightRatio
        const innerRadius = outerRadius * 0.25 // 内部也有粒子，使树更饱满

        for (let i = 0; i < particlesPerLayer && generatedCrownCount < crownParticleCount; i++) {
          // 在圆形截面上均匀分布（从内到外都有）
          const angle = (generatedCrownCount * 137.5) % (Math.PI * 2) // 黄金角度螺旋
          const radialRatio = Math.random() // 0 到 1
          const radialPos = innerRadius + (outerRadius - innerRadius) * Math.sqrt(radialRatio) // 均匀分布在圆环内

          const x = Math.cos(angle) * radialPos
          const y = -totalTreeHeight / 2 + height + (Math.random() - 0.5) * (crownHeight / layers * 0.3) // 在层内稍微随机
          const z = Math.sin(angle) * radialPos

          treeParticles.push(x, y, z)

          // 圣诞树颜色：参考实现的深绿色渐变
          // EMERALD_DEEP (#003808): rgb(0, 56, 8) / 255
          // EMERALD_MID (#005410): rgb(0, 84, 16) / 255
          // EMERALD_LIGHT (#006018): rgb(0, 96, 24) / 255
          let r, g, b
          if (heightRatio < 0.33) {
            // 底部：EMERALD_DEEP
            const t = heightRatio / 0.33
            r = (0 + t * 0) / 255
            g = (56 + t * 28) / 255
            b = (8 + t * 8) / 255
          } else if (heightRatio < 0.66) {
            // 中部：EMERALD_MID
            const t = (heightRatio - 0.33) / 0.33
            r = 0 / 255
            g = (84 + t * 12) / 255
            b = (16 + t * 8) / 255
          } else {
            // 顶部：EMERALD_LIGHT
            r = 0 / 255
            g = (96 + Math.random() * 20) / 255 // 顶部稍微亮一些
            b = (24 + Math.random() * 10) / 255
          }

          // 添加一些随机变化，使树更自然
          r += (Math.random() - 0.5) * 0.02
          g += (Math.random() - 0.5) * 0.05
          b += (Math.random() - 0.5) * 0.02

          treeColors.push(Math.max(0, Math.min(1, r)), Math.max(0, Math.min(1, g)), Math.max(0, Math.min(1, b)))

          generatedCrownCount++
        }
      }

      // 如果还有剩余粒子，继续生成
      while (generatedCrownCount < crownParticleCount) {
        const heightRatio = Math.random()
        const height = trunkHeight + heightRatio * crownHeight
        const radiusFactor = 1 - heightRatio
        const outerRadius = crownBaseRadius * radiusFactor + crownTopRadius * heightRatio
        const innerRadius = outerRadius * 0.25
        const angle = Math.random() * Math.PI * 2
        const radialPos = innerRadius + (outerRadius - innerRadius) * Math.sqrt(Math.random())

        const x = Math.cos(angle) * radialPos
        const y = -totalTreeHeight / 2 + height
        const z = Math.sin(angle) * radialPos

        treeParticles.push(x, y, z)

        // 使用相同的深绿色渐变
        let r, g, b
        if (heightRatio < 0.33) {
          const t = heightRatio / 0.33
          r = (0 + t * 0) / 255
          g = (56 + t * 28) / 255
          b = (8 + t * 8) / 255
        } else if (heightRatio < 0.66) {
          const t = (heightRatio - 0.33) / 0.33
          r = 0 / 255
          g = (84 + t * 12) / 255
          b = (16 + t * 8) / 255
        } else {
          r = 0 / 255
          g = (96 + Math.random() * 20) / 255
          b = (24 + Math.random() * 10) / 255
        }

        r += (Math.random() - 0.5) * 0.02
        g += (Math.random() - 0.5) * 0.05
        b += (Math.random() - 0.5) * 0.02

        treeColors.push(Math.max(0, Math.min(1, r)), Math.max(0, Math.min(1, g)), Math.max(0, Math.min(1, b)))

        generatedCrownCount++
      }

      // 生成装饰品粒子（彩球、星星等）
      // 参考实现：使用更丰富的颜色，包括ROYAL_BLUE, RED, DEEP_PINK, PINK, PURPLE, ORANGE等
      for (let i = 0; i < decorationParticleCount; i++) {
        const heightRatio = Math.random() * 0.85 + 0.12 // 从树干上方开始
        const height = trunkHeight + heightRatio * crownHeight

        // 装饰品在树冠表面附近
        const radiusFactor = 1 - heightRatio * 0.9
        const radius = (crownBaseRadius * radiusFactor + crownTopRadius * heightRatio) * (0.75 + Math.random() * 0.25)

        const angle = Math.random() * Math.PI * 2
        const radialPos = radius * (0.7 + Math.random() * 0.3) // 在表面附近

        const x = Math.cos(angle) * radialPos
        const y = -totalTreeHeight / 2 + height
        const z = Math.sin(angle) * radialPos

        treeParticles.push(x, y, z)

        // 装饰品颜色：参考实现的丰富颜色方案
        // GOLD (#FFD700), ROYAL_BLUE (#8a97ff), RED (#e31441), DEEP_PINK (#ffabd9)
        // PINK (#ff52a6), PURPLE (#DA70D6), ORANGE (#ff7b00), LIGHT_PINK (#FFB6C1)
        const decorationType = Math.random()
        let r, g, b

        if (decorationType < 0.15) {
          // 金色装饰 GOLD (#FFD700) - 15%
          r = 1.0
          g = 0.84 + Math.random() * 0.1
          b = 0.0
        } else if (decorationType < 0.28) {
          // 皇家蓝 ROYAL_BLUE (#8a97ff) - 13%
          r = (138 + Math.random() * 10) / 255
          g = (151 + Math.random() * 10) / 255
          b = (255 + Math.random() * 0) / 255
        } else if (decorationType < 0.43) {
          // 红色 RED (#e31441) - 15%
          r = (227 + Math.random() * 10) / 255
          g = (20 + Math.random() * 10) / 255
          b = (65 + Math.random() * 10) / 255
        } else if (decorationType < 0.58) {
          // 深粉色 DEEP_PINK (#ffabd9) - 15%
          r = (255 + Math.random() * 0) / 255
          g = (171 + Math.random() * 20) / 255
          b = (217 + Math.random() * 20) / 255
        } else if (decorationType < 0.70) {
          // 粉色 PINK (#ff52a6) - 12%
          r = (255 + Math.random() * 0) / 255
          g = (82 + Math.random() * 20) / 255
          b = (166 + Math.random() * 20) / 255
        } else if (decorationType < 0.82) {
          // 紫色 PURPLE (#DA70D6) - 12%
          r = (218 + Math.random() * 10) / 255
          g = (112 + Math.random() * 10) / 255
          b = (214 + Math.random() * 10) / 255
        } else if (decorationType < 0.92) {
          // 橙色 ORANGE (#ff7b00) - 10%
          r = (255 + Math.random() * 0) / 255
          g = (123 + Math.random() * 20) / 255
          b = (0 + Math.random() * 10) / 255
        } else {
          // 浅粉色 LIGHT_PINK (#FFB6C1) - 8%
          r = (255 + Math.random() * 0) / 255
          g = (182 + Math.random() * 20) / 255
          b = (193 + Math.random() * 20) / 255
        }

        treeColors.push(Math.max(0, Math.min(1, r)), Math.max(0, Math.min(1, g)), Math.max(0, Math.min(1, b)))
      }

      // 在树顶添加立体黄色五角星⭐️（增强立体感，避免像杆子）
      const starHeight = trunkHeight + crownHeight + 8 // 树顶上方
      const starSize = totalTreeWidth * 0.12 // 星星大小（占据树宽度的12%）
      const starCenterY = -totalTreeHeight / 2 + starHeight
      const starThickness = starSize * 0.6 // 增加星星厚度（从0.25增加到0.6，更立体）

      // 五角星参数：外圆半径和内圆半径
      const outerRadius = starSize
      const innerRadius = outerRadius * 0.382 // 五角星内圆半径比例（黄金比例）

      // 生成立体五角星：在Z方向创建多层，增强3D效果
      const starLayers = 7 // 增加层数（从3增加到7），使星星更立体
      const starParticlesPerLayer = Math.floor(starParticleCount / starLayers)
      const remainingStarParticles = starParticleCount % starLayers

      // 五角星的10个顶点（5个外角 + 5个内角）
      // 外角：0°, 72°, 144°, 216°, 288°（从顶部开始，逆时针）
      // 内角：36°, 108°, 180°, 252°, 324°
      const outerAngles = []
      const innerAngles = []
      for (let i = 0; i < 5; i++) {
        outerAngles.push(i * Math.PI * 2 / 5 - Math.PI / 2) // 从顶部开始
        innerAngles.push((i + 0.5) * Math.PI * 2 / 5 - Math.PI / 2)
      }

      for (let layer = 0; layer < starLayers; layer++) {
        const layerParticles = starParticlesPerLayer + (layer < remainingStarParticles ? 1 : 0)
        const layerProgress = layer / (starLayers - 1) // 0 到 1
        // Z方向偏移：从后到前，使用更平滑的分布
        const zOffset = (layerProgress - 0.5) * starThickness

        // 生成五角星轮廓：沿着10条边精确分布
        const edgeParticleRatio = 0.65 // 65%的粒子用于轮廓
        const edgeParticleCount = Math.floor(layerParticles * edgeParticleRatio)
        const particlesPerEdge = Math.floor(edgeParticleCount / 10)
        const remainingEdgeParticles = edgeParticleCount % 10

        for (let edge = 0; edge < 10; edge++) {
          const edgeParticles = particlesPerEdge + (edge < remainingEdgeParticles ? 1 : 0)
          let startAngle, endAngle, startRadius, endRadius

          if (edge % 2 === 0) {
            // 从外角到内角
            const outerIndex = Math.floor(edge / 2)
            const innerIndex = outerIndex
            startAngle = outerAngles[outerIndex]
            endAngle = innerAngles[innerIndex]
            startRadius = outerRadius
            endRadius = innerRadius
          } else {
            // 从内角到外角
            const innerIndex = Math.floor(edge / 2)
            const outerIndex = (innerIndex + 1) % 5
            startAngle = innerAngles[innerIndex]
            endAngle = outerAngles[outerIndex]
            startRadius = innerRadius
            endRadius = outerRadius
          }

          // 沿着这条边均匀分布粒子
          for (let i = 0; i < edgeParticles; i++) {
            const t = i / Math.max(1, edgeParticles - 1) // 0 到 1
            const angle = startAngle + (endAngle - startAngle) * t
            const radius = startRadius + (endRadius - startRadius) * t

            // 在X-Y平面计算位置
            const x = Math.cos(angle) * radius
            const y = starCenterY + (Math.random() - 0.5) * 0.3 // 减少Y方向随机

            // 增强Z方向的3D分布：不仅沿Z轴偏移，还在X-Z和Y-Z平面有分布
            // 让星星在3D空间中更立体，而不是扁平
            const zInPlane = Math.sin(angle) * radius * 0.4 // 在X-Z平面的投影
            const zDepth = zOffset + (Math.random() - 0.5) * starThickness * 0.3 // 在Z方向有随机深度
            const z = zInPlane + zDepth

            treeParticles.push(x, y, z)

            // 星星颜色：GOLD (#FFD700)，根据深度调整亮度
            const depthFactor = 1 - Math.abs(layerProgress - 0.5) * 0.3 // 中心层更亮
            const layerBrightness = 0.85 + depthFactor * 0.15
            const brightness = layerBrightness + Math.random() * 0.05
            const r = brightness
            const g = brightness * 0.843
            const b = 0.0
            treeColors.push(r, g, b)
          }
        }

        // 在五角星中心区域填充粒子（35%的粒子）
        const centerParticleCount = layerParticles - edgeParticleCount
        for (let i = 0; i < centerParticleCount; i++) {
          // 使用极坐标在中心区域均匀分布
          const angle = Math.random() * Math.PI * 2
          const radius = Math.sqrt(Math.random()) * innerRadius * 0.75 // 中心区域

          const x = Math.cos(angle) * radius
          const y = starCenterY + (Math.random() - 0.5) * 0.3

          // 中心区域也在Z方向有更好的分布
          const zInPlane = Math.sin(angle) * radius * 0.4
          const zDepth = zOffset + (Math.random() - 0.5) * starThickness * 0.3
          const z = zInPlane + zDepth

          treeParticles.push(x, y, z)

          // 中心也是GOLD颜色，根据深度调整亮度
          const depthFactor = 1 - Math.abs(layerProgress - 0.5) * 0.3
          const layerBrightness = 0.9 + depthFactor * 0.1
          const brightness = layerBrightness + Math.random() * 0.05
          const r = brightness
          const g = brightness * 0.843
          const b = 0.0
          treeColors.push(r, g, b)
        }
      }

      this.treeParticles = treeParticles
      this.treeColors = treeColors

      // 初始化花瓣数组
      this.petals = []
      this.initPetals()

      // 保存当前粒子位置数组（初始为字符串排列）
      this.currentParticlePositions = [...particles]

      // 初始使用字符串位置（默认状态）
      const geometry = markRaw(new THREE.BufferGeometry())
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(particles, 3))
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(this.particleColors, 3))

      // 创建粒子材质（使用 markRaw 避免 Vue 响应式代理）
      // 注意：AdditiveBlending 会让所有粒子都发光，可能不适合所有模式
      // 所以只在需要时动态调整
      const material = markRaw(new THREE.PointsMaterial({
        vertexColors: true, // 启用顶点颜色
        size: 4,
        transparent: true,
        opacity: 1.0,
        sizeAttenuation: false // 禁用距离衰减，确保粒子大小一致
      }))

      console.log('创建粒子文字:', text, '粒子数量:', particles.length / 3)

      if (particles.length === 0) {
        console.warn('没有生成任何粒子，文字可能为空或字体加载失败')
      }

      // 创建粒子系统（使用 markRaw 避免 Vue 响应式代理）
      this.particleSystem = markRaw(new THREE.Points(geometry, material))
      this.scene.add(this.particleSystem)

      // 重置状态（默认是石头模式，字符显示）
      this.gestureMode = 'rock'
      this.currentGesture = 'rock'
      this.animationTime = 0
      this.rotationX = 0
      this.rotationY = 0
      this.isScattered = false
      // 通知父组件初始手势模式
      this.$emit('gesture-mode-changed', 'rock')
    },

    // 初始化粉色雪花
    initPetals () {
      const snowflakeCount = 300 // 雪花数量（增加到300，让雪花飘得更多）
      for (let i = 0; i < snowflakeCount; i++) {
        // 粉色雪花颜色：浅粉色到深粉色
        const pinkFactor = Math.random() // 0 到 1
        const r = 0.95 + pinkFactor * 0.05 // 0.95 到 1.0
        const g = 0.75 + pinkFactor * 0.2 // 0.75 到 0.95
        const b = 0.85 + pinkFactor * 0.1 // 0.85 到 0.95

        this.petals.push({
          x: (Math.random() - 0.5) * 1000, // 随机起始X位置（范围更大）
          y: 250 + Math.random() * 150, // 从屏幕上方开始
          z: (Math.random() - 0.5) * 1000, // 随机起始Z位置
          vx: (Math.random() - 0.5) * 0.8, // X方向速度（雪花飘动）
          vy: -0.3 - Math.random() * 0.5, // Y方向速度（向下飘落）
          vz: (Math.random() - 0.5) * 0.8, // Z方向速度
          rotation: Math.random() * Math.PI * 2, // 旋转角度
          rotationSpeed: (Math.random() - 0.5) * 0.15, // 旋转速度（雪花旋转）
          size: 2 + Math.random() * 3, // 雪花大小
          color: {
            r,
            g,
            b
          }
        })
      }
    },

    // 更新雪花位置
    updatePetals () {
      if (this.gestureMode !== 'tree') {
        // 如果不是树模式，重置雪花位置
        this.petals.forEach(petal => {
          petal.y = 250 + Math.random() * 150
          petal.x = (Math.random() - 0.5) * 1000
          petal.z = (Math.random() - 0.5) * 1000
        })
        return
      }

      this.petals.forEach(petal => {
        // 更新位置
        petal.x += petal.vx
        petal.y += petal.vy
        petal.z += petal.vz
        petal.rotation += petal.rotationSpeed

        // 添加轻微的横向摆动（雪花飘动效果）
        petal.vx += (Math.random() - 0.5) * 0.03
        petal.vz += (Math.random() - 0.5) * 0.03

        // 如果雪花落到屏幕外，重新从屏幕上方生成
        if (petal.y < -350) {
          petal.y = 250 + Math.random() * 150
          petal.x = (Math.random() - 0.5) * 1000
          petal.z = (Math.random() - 0.5) * 1000
          petal.vx = (Math.random() - 0.5) * 0.8
          petal.vy = -0.3 - Math.random() * 0.5
          petal.vz = (Math.random() - 0.5) * 0.8
        }

        // 限制横向范围（雪花可以飘得更远）
        if (Math.abs(petal.x) > 700) {
          petal.vx *= -0.3
        }
        if (Math.abs(petal.z) > 700) {
          petal.vz *= -0.3
        }
      })
    },

    // 渲染雪花
    renderPetals () {
      if (this.gestureMode !== 'tree' || !this.petals || this.petals.length === 0) {
        return
      }

      // 如果雪花粒子系统不存在，创建它
      if (!this.petalSystem) {
        const petalPositions = []
        const petalColors = []
        const petalSizes = []

        this.petals.forEach(petal => {
          petalPositions.push(petal.x, petal.y, petal.z)
          petalColors.push(petal.color.r, petal.color.g, petal.color.b)
          petalSizes.push(petal.size)
        })

        const petalGeometry = markRaw(new THREE.BufferGeometry())
        petalGeometry.setAttribute('position', new THREE.Float32BufferAttribute(petalPositions, 3))
        petalGeometry.setAttribute('color', new THREE.Float32BufferAttribute(petalColors, 3))
        petalGeometry.setAttribute('size', new THREE.Float32BufferAttribute(petalSizes, 1))

        const petalMaterial = markRaw(new THREE.PointsMaterial({
          vertexColors: true,
          size: 5, // 雪花稍小
          transparent: true,
          opacity: 0.9, // 雪花更明显
          sizeAttenuation: true
        }))

        this.petalSystem = markRaw(new THREE.Points(petalGeometry, petalMaterial))
        this.scene.add(this.petalSystem)
      }

      // 更新雪花位置和颜色
      const positions = this.petalSystem.geometry.attributes.position.array
      const colors = this.petalSystem.geometry.attributes.color.array

      this.petals.forEach((petal, i) => {
        const i3 = i * 3
        positions[i3] = petal.x
        positions[i3 + 1] = petal.y
        positions[i3 + 2] = petal.z

        colors[i3] = petal.color.r
        colors[i3 + 1] = petal.color.g
        colors[i3 + 2] = petal.color.b
      })

      this.petalSystem.geometry.attributes.position.needsUpdate = true
      this.petalSystem.geometry.attributes.color.needsUpdate = true
    },

    // 动画循环
    animate () {
      if (!this.renderer || !this.scene || !this.camera) {
        console.warn('Three.js 组件未初始化，跳过渲染')
        return
      }

      this.animationId = requestAnimationFrame(() => this.animate())

      // 更新动画时间（用于自旋）
      this.animationTime += 0.016 // 约60fps

      // 实时更新粒子位置和颜色
      if (this.particleSystem && this.originalParticles &&
          this.currentParticlePositions && this.originalParticles.length > 0) {
        const geometry = this.particleSystem.geometry
        const positions = geometry.attributes.position.array
        const colors = geometry.attributes.color.array
        const particleCount = positions.length / 3

        // 根据手势模式选择目标位置和颜色
        let targetParticles = this.originalParticles
        let targetColors = this.originalColors
        let shouldRotate = false
        let rotationSpeed = 0

        if (this.gestureMode === 'paper' && this.globeParticles && this.globeColors) {
          // 布手势：地球仪模式
          targetParticles = this.globeParticles
          targetColors = this.globeColors
          shouldRotate = true
          rotationSpeed = 0.5 // 地球仪自旋速度
        } else if (this.gestureMode === 'tree' && this.treeParticles && this.treeColors) {
          // 树手势：3D圣诞树模式
          targetParticles = this.treeParticles
          targetColors = this.treeColors
          shouldRotate = true // 树缓慢旋转（参考实现）
          rotationSpeed = 0.3 // 缓慢旋转速度
        } else {
          // 石头手势：字符模式
          targetParticles = this.originalParticles
          targetColors = this.originalColors
          shouldRotate = false
        }

        // 更新旋转角度（根据手势方向）
        if (shouldRotate) {
          const direction = this.rotationDirection // 1或-1，控制旋转方向
          if (this.gestureMode === 'tree') {
            // 圣诞树只绕Y轴旋转（沿着树干）
            this.rotationY += rotationSpeed * 0.016 * direction
            this.rotationX = 0 // 不绕X轴旋转
          } else {
            // 其他模式可以绕X和Y轴旋转
            this.rotationY += rotationSpeed * 0.016 * direction
            this.rotationX += rotationSpeed * 0.008 * direction // X轴旋转稍慢
          }
        }

        for (let i = 0; i < particleCount; i++) {
          const i3 = i * 3

          // 获取目标位置
          let targetX = targetParticles[i3]
          let targetY = targetParticles[i3 + 1]
          let targetZ = targetParticles[i3 + 2]

          // 应用自旋旋转
          if (shouldRotate) {
            if (this.gestureMode === 'tree') {
              // 圣诞树只绕Y轴旋转（沿着树干）
              const cosY = Math.cos(this.rotationY)
              const sinY = Math.sin(this.rotationY)
              const rotatedX = targetX * cosY - targetZ * sinY
              const rotatedZ = targetX * sinY + targetZ * cosY
              targetX = rotatedX
              targetZ = rotatedZ
              // Y坐标不变
            } else {
              // 其他模式：绕Y轴和X轴旋转
              // 先绕Y轴旋转（水平旋转）
              const cosY = Math.cos(this.rotationY)
              const sinY = Math.sin(this.rotationY)
              const rotatedX = targetX * cosY - targetZ * sinY
              const rotatedZ = targetX * sinY + targetZ * cosY
              const rotatedY = targetY

              // 再绕X轴旋转（垂直旋转），使用Y轴旋转后的坐标
              const cosX = Math.cos(this.rotationX)
              const sinX = Math.sin(this.rotationX)
              targetY = rotatedY * cosX - rotatedZ * sinX
              targetZ = rotatedY * sinX + rotatedZ * cosX
              targetX = rotatedX
            }
          }

          // 平滑过渡到目标位置
          const currentX = this.currentParticlePositions[i3]
          const currentY = this.currentParticlePositions[i3 + 1]
          const currentZ = this.currentParticlePositions[i3 + 2]

          positions[i3] = currentX + (targetX - currentX) * 0.15
          positions[i3 + 1] = currentY + (targetY - currentY) * 0.15
          positions[i3 + 2] = currentZ + (targetZ - currentZ) * 0.15

          // 更新当前位置数组
          this.currentParticlePositions[i3] = positions[i3]
          this.currentParticlePositions[i3 + 1] = positions[i3 + 1]
          this.currentParticlePositions[i3 + 2] = positions[i3 + 2]

          // 平滑过渡到目标颜色
          const targetR = targetColors[i3]
          const targetG = targetColors[i3 + 1]
          const targetB = targetColors[i3 + 2]

          colors[i3] = colors[i3] + (targetR - colors[i3]) * 0.15
          colors[i3 + 1] = colors[i3 + 1] + (targetG - colors[i3 + 1]) * 0.15
          colors[i3 + 2] = colors[i3 + 2] + (targetB - colors[i3 + 2]) * 0.15
        }

        geometry.attributes.position.needsUpdate = true
        geometry.attributes.color.needsUpdate = true
      }

      // 更新和渲染花瓣
      if (this.gestureMode === 'tree') {
        this.updatePetals()
        this.renderPetals()
      } else if (this.petalSystem) {
        // 如果不是树模式，移除花瓣系统
        this.scene.remove(this.petalSystem)
        this.petalSystem.geometry.dispose()
        this.petalSystem.material.dispose()
        this.petalSystem = null
      }

      try {
        this.renderer.render(this.scene, this.camera)
      } catch (err) {
        console.error('渲染错误:', err)
      }
    },

    // 处理窗口大小变化
    handleParticleResize () {
      if (!this.$refs.contentSection || !this.renderer || !this.camera) return
      const container = this.$refs.contentSection
      const width = container.clientWidth
      const height = container.clientHeight

      this.camera.aspect = width / height
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(width, height)
    },

    // 初始化 MediaPipe 手势识别（使用新的 Tasks API）
    async initMediaPipe () {
      try {
        // 检查是否支持摄像头 API
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          console.warn('浏览器不支持摄像头 API，跳过手势识别')
          return
        }

        // 创建视频元素用于摄像头输入
        this.video = document.createElement('video')
        this.video.style.position = 'fixed'
        this.video.style.top = '-9999px'
        this.video.style.width = '1px'
        this.video.style.height = '1px'
        document.body.appendChild(this.video)

        // 初始化手部关键点检测器（使用 npm 包）
        const vision = await FilesetResolver.forVisionTasks(
          'https://cdn.jiamid.com/wasm'
        )

        // 使用 markRaw 避免 Vue 响应式代理导致 MediaPipe 内部状态异常
        this.handLandmarker = markRaw(await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: 'https://cdn.jiamid.com/wasm/hand_landmarker.task',
            delegate: 'GPU' // 使用 GPU 加速
          },
          numHands: 1, // 检测单手
          runningMode: 'VIDEO', // 视频模式
          minHandDetectionConfidence: 0.5,
          minHandPresenceConfidence: 0.5,
          minTrackingConfidence: 0.5
        }))

        // 启动摄像头
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 }
        })
        this.video.srcObject = stream
        this.video.play()

        // 等待视频就绪（确保视频元数据已加载）
        await new Promise((resolve) => {
          if (this.video.readyState >= this.video.HAVE_METADATA) {
            resolve()
          } else {
            this.video.onloadedmetadata = () => {
              resolve()
            }
          }
        })

        // 额外等待视频有足够数据
        await new Promise((resolve) => {
          if (this.video.readyState >= this.video.HAVE_ENOUGH_DATA) {
            resolve()
          } else {
            this.video.oncanplay = () => {
              resolve()
            }
          }
        })

        // 确保 HandLandmarker 已正确初始化
        if (!this.handLandmarker) {
          throw new Error('HandLandmarker 初始化失败')
        }

        // 开始处理视频帧
        this.processVideo()
        console.log('MediaPipe 手势识别已启动')
        this.mediaPipeInitialized = true
      } catch (err) {
        // 静默处理错误，不影响其他功能
        if (err.name === 'NotFoundError' || err.name === 'NotAllowedError' || err.name === 'NotReadableError') {
          // 摄像头相关的错误，静默处理
          console.warn('摄像头不可用，手势识别功能已禁用')
        } else {
          console.warn('MediaPipe 初始化失败:', err.message, err)
        }
        // 清理可能创建的资源
        if (this.video && this.video.srcObject) {
          this.video.srcObject.getTracks().forEach(track => track.stop())
          this.video.srcObject = null
        }
        if (this.video && this.video.parentNode) {
          this.video.parentNode.removeChild(this.video)
          this.video = null
        }
      }
    },

    // 处理视频帧
    processVideo () {
      if (!this.video || !this.handLandmarker) return

      if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
        try {
          // 使用新的 Tasks API 处理视频帧
          const startTimeMs = performance.now()
          const result = this.handLandmarker.detectForVideo(this.video, startTimeMs)
          this.handleHandResults(result)
        } catch (err) {
          // 捕获可能的错误（如 runningMode 未正确设置）
          if (err.message && err.message.includes('runningMode')) {
            console.error('MediaPipe runningMode 错误:', err.message)
            // 停止处理，避免持续报错
            this.mediaPipeInitialized = false
            return
          }
          console.warn('处理视频帧时出错:', err.message)
        }
      }

      requestAnimationFrame(() => this.processVideo())
    },

    // 识别手势类型
    recognizeGesture (landmarks) {
      if (!landmarks || landmarks.length < 21) return 'rock'

      // MediaPipe 手部关键点索引：
      // 0: 手腕, 4: 拇指尖, 8: 食指尖, 12: 中指尖, 16: 无名指尖, 20: 小指尖
      // 3: 拇指关节, 6: 食指关节, 10: 中指关节, 14: 无名指关节, 18: 小指关节
      const thumbTip = landmarks[4]
      const thumbJoint = landmarks[3]
      const indexTip = landmarks[8]
      const indexJoint = landmarks[6]
      const middleTip = landmarks[12]
      const middleJoint = landmarks[10]
      const ringTip = landmarks[16]
      const ringJoint = landmarks[14]
      const pinkyTip = landmarks[20]
      const pinkyJoint = landmarks[18]

      // 计算每个手指是否伸直（指尖到关节的距离）
      const getFingerExtended = (tip, joint) => {
        const tipToJoint = Math.sqrt(
          Math.pow(tip.x - joint.x, 2) +
          Math.pow(tip.y - joint.y, 2) +
          Math.pow(tip.z - joint.z, 2)
        )
        // 如果指尖到关节的距离大于阈值，认为手指是伸直的
        return tipToJoint > 0.08
      }

      const thumbExtended = getFingerExtended(thumbTip, thumbJoint)
      const indexExtended = getFingerExtended(indexTip, indexJoint)
      const middleExtended = getFingerExtended(middleTip, middleJoint)
      const ringExtended = getFingerExtended(ringTip, ringJoint)
      const pinkyExtended = getFingerExtended(pinkyTip, pinkyJoint)

      // 检测树手势：拇指和食指都伸直，且距离适中（形成L形或V形）
      const thumbIndexDistance = Math.sqrt(
        Math.pow(thumbTip.x - indexTip.x, 2) +
        Math.pow(thumbTip.y - indexTip.y, 2) +
        Math.pow(thumbTip.z - indexTip.z, 2)
      )

      // 树手势：拇指和食指都伸直，其他手指弯曲
      if (thumbExtended && indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
        if (thumbIndexDistance > 0.05 && thumbIndexDistance < 0.2) {
          return 'tree'
        }
      }

      // 布手势：所有手指都伸直
      if (thumbExtended && indexExtended && middleExtended && ringExtended && pinkyExtended) {
        return 'paper'
      }

      // 石头手势：所有手指都弯曲（默认）
      return 'rock'
    },

    // 处理手势识别结果
    handleHandResults (result) {
      // 新的 API 返回的格式是 { landmarks: [...], worldLandmarks: [...], handednesses: [...] }
      if (!result || !result.landmarks || result.landmarks.length === 0) {
        // 如果没有检测到手，重置为石头模式（字符模式）
        if (this.gestureMode !== 'rock') {
          this.gestureMode = 'rock'
          this.currentGesture = 'rock'
          // 通知父组件手势模式变化
          this.$emit('gesture-mode-changed', 'rock')
        }
        // 清空手的位置历史
        this.lastHandX = null
        this.handPositionHistory = []
        return
      }

      // 识别手势（单手）
      const hand = result.landmarks[0]
      const gesture = this.recognizeGesture(hand)

      // 更新手势模式
      if (gesture !== this.currentGesture) {
        this.currentGesture = gesture
        this.gestureMode = gesture
        console.log('检测到手势:', gesture)
        // 通知父组件手势模式变化
        this.$emit('gesture-mode-changed', gesture)
      }

      // 在圣诞树和地球仪模式下，检测手的水平移动来改变旋转方向
      if (gesture === 'tree' || gesture === 'paper') {
        const wristX = hand[0].x // 手腕的X坐标（0-1，0在左边，1在右边）

        // 记录手的位置历史（用于平滑检测）
        this.handPositionHistory.push(wristX)
        if (this.handPositionHistory.length > 15) {
          this.handPositionHistory.shift() // 只保留最近15帧
        }

        // 如果有足够的历史数据，检测水平移动趋势
        if (this.handPositionHistory.length >= 10) {
          // 计算最近5帧的平均X位置（当前）
          const recentFrames = this.handPositionHistory.slice(-5)
          const recentAvgX = recentFrames.reduce((a, b) => a + b, 0) / recentFrames.length

          // 计算之前5帧的平均X位置（历史）
          const olderFrames = this.handPositionHistory.slice(-10, -5)
          const olderAvgX = olderFrames.reduce((a, b) => a + b, 0) / olderFrames.length

          // 检测明显的水平移动（阈值：0.03，约3%屏幕宽度）
          const movementThreshold = 0.03
          const movement = recentAvgX - olderAvgX

          if (Math.abs(movement) > movementThreshold) {
            // 向右移动（X增加）：正向旋转
            if (movement > 0) {
              this.rotationDirection = 1
              console.log('检测到向右移动，正向旋转')
            } else {
              // 向左移动（X减少）：反向旋转
              this.rotationDirection = -1
              console.log('检测到向左移动，反向旋转')
            }
          }
        }

        this.lastHandX = wristX
      } else {
        // 其他模式下重置位置跟踪
        this.lastHandX = null
        this.handPositionHistory = []
      }
    },

    // 处理点击事件（摄像头不可用时切换模式）
    handleClick (event) {
      console.log('点击事件触发, mediaPipeInitialized:', this.mediaPipeInitialized)

      // 如果摄像头已初始化，手势控制优先，不响应点击
      if (this.mediaPipeInitialized) {
        console.log('摄像头已初始化，忽略点击')
        return
      }

      // 点击切换模式：rock -> paper -> tree -> rock
      const modes = ['rock', 'paper', 'tree']
      const currentIndex = modes.indexOf(this.gestureMode)
      const nextIndex = (currentIndex + 1) % modes.length
      this.gestureMode = modes[nextIndex]
      this.currentGesture = modes[nextIndex]
      console.log('点击切换模式:', this.gestureMode)
    }
  }
}
</script>

<style scoped>
.content-section {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.particle-canvas {
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none; /* 允许点击事件穿透到父容器 */
}
</style>
