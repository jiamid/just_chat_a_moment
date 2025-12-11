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
      lastPinchDistance: 0,
      basePinchDistance: 0, // 基准捏合距离（首次检测时记录）
      spreadAmount: 0, // 扩散程度 0-1, 0为字符串模式，1为完全散开
      targetSpreadAmount: 0 // 目标扩散程度
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

      // 保存当前粒子位置数组（初始为字符串排列）
      this.currentParticlePositions = [...particles]

      // 初始使用字符串位置（默认状态）
      const geometry = markRaw(new THREE.BufferGeometry())
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(particles, 3))
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(this.particleColors, 3))

      // 创建粒子材质（使用 markRaw 避免 Vue 响应式代理）
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

      // 重置状态（默认是字符串模式，扩散程度为0）
      this.spreadAmount = 0
      this.targetSpreadAmount = 0
      this.isScattered = false
    },

    // 动画循环
    animate () {
      if (!this.renderer || !this.scene || !this.camera) {
        console.warn('Three.js 组件未初始化，跳过渲染')
        return
      }

      this.animationId = requestAnimationFrame(() => this.animate())

      // 平滑过渡扩散程度
      this.spreadAmount += (this.targetSpreadAmount - this.spreadAmount) * 0.15

      // 实时更新粒子位置和颜色
      if (this.particleSystem && this.originalParticles && this.scatteredParticles &&
          this.currentParticlePositions && this.originalParticles.length > 0 &&
          this.originalColors && this.scatteredColors && this.particleColors) {
        const geometry = this.particleSystem.geometry
        const positions = geometry.attributes.position.array
        const colors = geometry.attributes.color.array
        const particleCount = positions.length / 3

        for (let i = 0; i < particleCount; i++) {
          const i3 = i * 3

          // 在字符串位置和散开位置之间插值
          // spreadAmount = 0: 完全字符串模式
          // spreadAmount = 1: 完全散开模式
          const stringX = this.originalParticles[i3]
          const stringY = this.originalParticles[i3 + 1]
          const stringZ = this.originalParticles[i3 + 2]

          const scatteredX = this.scatteredParticles[i3]
          const scatteredY = this.scatteredParticles[i3 + 1]
          const scatteredZ = this.scatteredParticles[i3 + 2]

          // 计算目标位置（根据扩散程度插值）
          const targetX = stringX + (scatteredX - stringX) * this.spreadAmount
          const targetY = stringY + (scatteredY - stringY) * this.spreadAmount
          const targetZ = stringZ + (scatteredZ - stringZ) * this.spreadAmount

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

          // 在原始颜色（黑色）和散开颜色（彩色）之间插值
          const originalR = this.originalColors[i3]
          const originalG = this.originalColors[i3 + 1]
          const originalB = this.originalColors[i3 + 2]

          const scatteredR = this.scatteredColors[i3]
          const scatteredG = this.scatteredColors[i3 + 1]
          const scatteredB = this.scatteredColors[i3 + 2]

          const targetR = originalR + (scatteredR - originalR) * this.spreadAmount
          const targetG = originalG + (scatteredG - originalG) * this.spreadAmount
          const targetB = originalB + (scatteredB - originalB) * this.spreadAmount

          // 平滑过渡到目标颜色
          colors[i3] = colors[i3] + (targetR - colors[i3]) * 0.15
          colors[i3 + 1] = colors[i3 + 1] + (targetG - colors[i3 + 1]) * 0.15
          colors[i3 + 2] = colors[i3 + 2] + (targetB - colors[i3 + 2]) * 0.15
        }

        geometry.attributes.position.needsUpdate = true
        geometry.attributes.color.needsUpdate = true
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
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
        )

        this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
            delegate: 'GPU' // 使用 GPU 加速
          },
          numHands: 2, // 检测最多 2 只手
          runningMode: 'VIDEO', // 视频模式
          minHandDetectionConfidence: 0.5,
          minHandPresenceConfidence: 0.5,
          minTrackingConfidence: 0.5
        })

        // 启动摄像头
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 }
        })
        this.video.srcObject = stream
        this.video.play()

        // 等待视频就绪
        await new Promise((resolve) => {
          this.video.onloadedmetadata = () => {
            resolve()
          }
        })

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
        // 使用新的 Tasks API 处理视频帧
        const startTimeMs = performance.now()
        const result = this.handLandmarker.detectForVideo(this.video, startTimeMs)
        this.handleHandResults(result)
      }

      requestAnimationFrame(() => this.processVideo())
    },

    // 处理手势识别结果
    handleHandResults (result) {
      // 新的 API 返回的格式是 { landmarks: [...], worldLandmarks: [...], handednesses: [...] }
      if (!result || !result.landmarks || result.landmarks.length < 2) {
        // 如果没有检测到双手，重置为字符串模式（spreadAmount = 0）
        if (this.lastPinchDistance > 0) {
          this.targetSpreadAmount = 0
          this.lastPinchDistance = 0
          this.basePinchDistance = 0
        }
        return
      }

      const hand1 = result.landmarks[0]
      const hand2 = result.landmarks[1]

      // 食指指尖的索引是 8
      const index1 = hand1[8]
      const index2 = hand2[8]

      // 计算三维距离
      const distance = Math.sqrt(
        Math.pow(index1.x - index2.x, 2) +
        Math.pow(index1.y - index2.y, 2) +
        Math.pow(index1.z - index2.z, 2)
      )

      // 首次检测到双手时，记录基准距离（作为"合拢"的参考）
      if (this.lastPinchDistance === 0 || this.basePinchDistance === 0) {
        this.basePinchDistance = distance
        this.lastPinchDistance = distance
        // 首次检测时，根据距离设置初始扩散程度
        // 如果距离很小，认为是合拢状态（spreadAmount = 0）
        // 如果距离较大，认为是张开状态（spreadAmount 根据距离计算）
        const minDistance = 0.05 // 最小距离阈值（合拢）
        const maxDistance = 0.3 // 最大距离阈值（完全张开）
        if (distance < minDistance) {
          this.targetSpreadAmount = 0
        } else if (distance > maxDistance) {
          this.targetSpreadAmount = 1
        } else {
          // 在最小和最大之间线性映射
          this.targetSpreadAmount = (distance - minDistance) / (maxDistance - minDistance)
        }
        return
      }

      // 根据双手距离变化控制扩散程度
      // 距离越大（双手张开），扩散越大（spreadAmount 接近1）
      // 距离越小（双手捏合），扩散越小（spreadAmount 接近0）
      const minDistance = 0.05 // 最小距离阈值（合拢）
      const maxDistance = 0.3 // 最大距离阈值（完全张开）

      // 将距离映射到 0-1 范围
      if (distance < minDistance) {
        this.targetSpreadAmount = 0
      } else if (distance > maxDistance) {
        this.targetSpreadAmount = 1
      } else {
        // 在最小和最大之间线性映射
        this.targetSpreadAmount = (distance - minDistance) / (maxDistance - minDistance)
      }

      this.lastPinchDistance = distance
    },

    // 处理点击事件（摄像头不可用时切换模式）
    handleClick (event) {
      console.log('点击事件触发, mediaPipeInitialized:', this.mediaPipeInitialized)

      // 如果摄像头已初始化，手势控制优先，不响应点击
      if (this.mediaPipeInitialized) {
        console.log('摄像头已初始化，忽略点击')
        return
      }

      // 切换模式：在字符串模式（spreadAmount = 0）和散开模式（spreadAmount = 1）之间切换
      this.isScattered = !this.isScattered
      this.targetSpreadAmount = this.isScattered ? 1 : 0
      console.log('点击切换模式:', this.isScattered ? '散开' : '字符串', 'targetSpreadAmount:', this.targetSpreadAmount)
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
