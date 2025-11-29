<template>
  <canvas
    ref="canvas"
    class="game-canvas"
  ></canvas>
</template>

<script>
export default {
  name: 'LiveWarCanvas',
  props: {
    gameState: {
      type: Object,
      required: false
    }
  },
  data () {
    return {
      canvas: null,
      ctx: null,
      animationId: null,
      animationFrame: 0,
      TILE_SIZE: 16
    }
  },
  mounted () {
    this.initCanvas()
    this.startRendering()
  },
  beforeUnmount () {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
    }
  },
  watch: {
    gameState: {
      deep: true,
      handler () {
        // 状态变化后下一帧会自动重新渲染
      }
    }
  },
  methods: {
    initCanvas () {
      this.canvas = this.$refs.canvas
      if (!this.canvas) return

      const dpr = window.devicePixelRatio || 1
      const mapWidth = (this.gameState && this.gameState.room && this.gameState.room.width) || 60
      const mapHeight = (this.gameState && this.gameState.room && this.gameState.room.height) || 40

      // 计算画布的逻辑尺寸（保持固定比例 60:40 = 3:2）
      const logicalWidth = mapWidth * this.TILE_SIZE
      const logicalHeight = mapHeight * this.TILE_SIZE

      // 设置画布的实际像素尺寸（考虑设备像素比，用于高DPI显示）
      this.canvas.width = logicalWidth * dpr
      this.canvas.height = logicalHeight * dpr

      // 设置画布的显示尺寸（保持固定比例，CSS aspect-ratio会确保不变形）
      this.canvas.style.width = logicalWidth + 'px'
      this.canvas.style.height = logicalHeight + 'px'

      this.ctx = this.canvas.getContext('2d')
      if (this.ctx) {
        this.ctx.setTransform(1, 0, 0, 1, 0, 0)
        this.ctx.scale(dpr, dpr)
        this.ctx.imageSmoothingEnabled = false
      }
    },

    startRendering () {
      const render = () => {
        try {
          this.draw()
          this.animationFrame++
          this.animationId = requestAnimationFrame(render)
        } catch (e) {
          console.error('LiveWarCanvas render error', e)
        }
      }
      render()
    },

    draw () {
      if (!this.canvas || !this.ctx) {
        this.initCanvas()
        if (!this.canvas || !this.ctx) return
      }

      const ctx = this.ctx
      const state = this.gameState

      const mapWidth = (state && state.room && state.room.width) || 60
      const mapHeight = (state && state.room && state.room.height) || 40
      const width = mapWidth * this.TILE_SIZE
      const height = mapHeight * this.TILE_SIZE

      // 背景
      ctx.fillStyle = '#1e1e1e'
      ctx.fillRect(0, 0, width, height)

      if (!state || !state.room) {
        ctx.fillStyle = '#4ec9b0'
        ctx.font = '14px system-ui, -apple-system, BlinkMacSystemFont, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('LOADING...', width / 2, height / 2)
        return
      }

      // 网格背景（Screeps 风格）
      this.drawGrid(ctx, mapWidth, mapHeight)

      // 基地
      if (state.room.redBase) {
        this.drawBase(ctx, state.room.redBase, 'red')
      }
      if (state.room.blueBase) {
        this.drawBase(ctx, state.room.blueBase, 'blue')
      }

      // 矿场
      if (state.room.mineFields) {
        state.room.mineFields.forEach(m => {
          this.drawMine(ctx, m)
        })
      }

      // 单位
      if (state.room.units) {
        state.room.units.forEach(u => {
          if (!u.isDead) {
            this.drawUnit(ctx, u)
          }
        })
      }

      // 攻击特效（子弹）
      if (state.room.bulletEffects || state.room.bullet_effects) {
        const bullets = state.room.bulletEffects || state.room.bullet_effects || []
        bullets.forEach(bullet => {
          this.drawBulletEffect(ctx, bullet)
        })
      }

      // 回血特效
      if (state.room.healEffects || state.room.heal_effects) {
        const heals = state.room.healEffects || state.room.heal_effects || []
        heals.forEach(heal => {
          this.drawHealEffect(ctx, heal)
        })
      }

      // 能量掉落（小光点）
      if (state.room.energyDrops || state.room.energy_drops) {
        const drops = state.room.energyDrops || state.room.energy_drops || []
        drops.forEach(drop => {
          this.drawEnergyDrop(ctx, drop)
        })
      }
    },

    drawGrid (ctx, mapWidth, mapHeight) {
      ctx.fillStyle = '#252526'
      for (let x = 0; x < mapWidth; x++) {
        for (let y = 0; y < mapHeight; y++) {
          if ((x + y) % 2 === 0) {
            ctx.fillRect(
              x * this.TILE_SIZE,
              y * this.TILE_SIZE,
              this.TILE_SIZE,
              this.TILE_SIZE
            )
          }
        }
      }
    },

    drawBase (ctx, base, team) {
      const centerX = base.x * this.TILE_SIZE
      const centerY = base.y * this.TILE_SIZE
      const size = this.TILE_SIZE * 3
      const halfSize = size / 2

      const colors = team === 'red'
        ? { main: '#c0392b', light: '#e74c3c', dark: '#8b0000' }
        : { main: '#2980b9', light: '#3498db', dark: '#1a5276' }

      // 底座
      ctx.fillStyle = colors.dark
      ctx.fillRect(centerX - halfSize - this.TILE_SIZE / 2, centerY + this.TILE_SIZE / 2, size + this.TILE_SIZE, this.TILE_SIZE)

      // 主体
      ctx.fillStyle = colors.main
      ctx.fillRect(centerX - halfSize - 4, centerY - halfSize - this.TILE_SIZE / 2, size + 8, size)

      // 顶部
      ctx.fillStyle = colors.light
      ctx.fillRect(centerX - halfSize + 4, centerY - halfSize - this.TILE_SIZE * 1.5, size - 8, this.TILE_SIZE)

      // 高光
      ctx.fillStyle = '#fff'
      ctx.globalAlpha = 0.3
      ctx.fillRect(centerX - 4, centerY - halfSize - this.TILE_SIZE / 2, 8, size - this.TILE_SIZE)
      ctx.globalAlpha = 1

      // 血条
      const barY = centerY + halfSize + 4
      ctx.fillStyle = '#000'
      ctx.fillRect(centerX - halfSize - 4, barY, size + 8, 8)

      const hpPercent = base.hp && base.hp_max ? base.hp / base.hp_max : 1
      ctx.fillStyle = hpPercent > 0.5 ? '#4f4' : hpPercent > 0.25 ? '#ff0' : '#f44'
      ctx.fillRect(centerX - halfSize - 2, barY + 2, (size + 4) * hpPercent, 4)

      // 显示血量值（基地下方）
      const hp = base.hp || 0
      const hpMax = base.hp_max || 1000
      const textY = centerY + halfSize + 20
      ctx.fillStyle = '#fff'
      ctx.strokeStyle = '#000'
      ctx.lineWidth = 2
      ctx.font = 'bold 10px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.strokeText(`${hp}/${hpMax}`, centerX, textY)
      ctx.fillText(`${hp}/${hpMax}`, centerX, textY)
    },

    drawMine (ctx, mine) {
      const x = Math.floor(mine.x) * this.TILE_SIZE
      const y = Math.floor(mine.y) * this.TILE_SIZE
      const size = this.TILE_SIZE * 2

      const energyPercent = mine.energy && mine.energyMax ? mine.energy / mine.energyMax : 0

      // 矿场底座
      ctx.fillStyle = '#4a3a00'
      ctx.fillRect(x - 4, y + size - 8, size + 8, 12)

      if (energyPercent > 0) {
        // 金色矿石堆
        ctx.fillStyle = '#ffd700'
        ctx.fillRect(x, y, size, size - 8)

        // 高光
        ctx.fillStyle = '#ffec8b'
        ctx.fillRect(x + 4, y + 4, 8, 8)
        ctx.fillRect(x + size - 12, y + 8, 4, 4)
      } else {
        // 已采空
        ctx.fillStyle = '#333'
        ctx.fillRect(x, y, size, size - 8)
      }

      // 显示余额（矿场下方）
      const energy = mine.energy || 0
      const textY = y + size + 16
      ctx.fillStyle = '#fff'
      ctx.strokeStyle = '#000'
      ctx.lineWidth = 2
      ctx.font = 'bold 10px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.strokeText(`${energy}`, x + size / 2, textY)
      ctx.fillText(`${energy}`, x + size / 2, textY)
    },

    drawUnit (ctx, unit) {
      const x = unit.x * this.TILE_SIZE
      const y = unit.y * this.TILE_SIZE
      const isRed = unit.team === 'red'
      const mainColor = isRed ? '#e74c3c' : '#3498db'
      const darkColor = isRed ? '#c0392b' : '#2980b9'
      const lightColor = isRed ? '#ff6b6b' : '#5dade2'
      const size = this.TILE_SIZE

      // 计算方向角度（8个方向）
      let angle = 0 // 默认向右（红方）或向左（蓝方）
      if (unit.targetX !== undefined && unit.targetY !== undefined && unit.targetX !== null && unit.targetY !== null) {
        const dx = unit.targetX - unit.x
        const dy = unit.targetY - unit.y
        if (Math.abs(dx) > 0.01 || Math.abs(dy) > 0.01) {
          // 计算角度（弧度）
          const rad = Math.atan2(dy, dx)
          // 转换为8个方向（0, 45, 90, 135, 180, 225, 270, 315度）
          const degrees = (rad * 180 / Math.PI + 360) % 360
          // 四舍五入到最近的45度
          angle = Math.round(degrees / 45) * 45
          // 转换为弧度
          angle = angle * Math.PI / 180
        }
      } else {
        // 没有目标，使用默认方向：红方向右(0°)，蓝方向左(180°)
        angle = isRed ? 0 : Math.PI
      }

      // 根据单位类型绘制像素风格图标
      if (unit.type === 'miner') {
        this.drawPixelMiner(ctx, x, y, mainColor, darkColor, lightColor, isRed, size)
      } else if (unit.type === 'engineer') {
        this.drawPixelEngineer(ctx, x, y, mainColor, darkColor, lightColor, isRed, size)
      } else if (unit.type === 'heavy_tank') {
        this.drawPixelHeavyTank(ctx, x, y, mainColor, darkColor, lightColor, size, angle, isRed)
      } else if (unit.type === 'assault_tank') {
        this.drawPixelAssaultTank(ctx, x, y, mainColor, darkColor, lightColor, size, angle, isRed)
      } else {
        // 默认：简单方块
        ctx.fillStyle = mainColor
        ctx.fillRect(x - 4, y - 4, 8, 8)
      }

      // 血条
      const hpPercent = unit.hp && unit.hp_max ? unit.hp / unit.hp_max : 1
      ctx.fillStyle = '#000'
      ctx.fillRect(x - 6, y - 10, 12, 4)
      ctx.fillStyle = hpPercent > 0.5 ? '#2ecc71' : hpPercent > 0.25 ? '#f1c40f' : '#e74c3c'
      ctx.fillRect(x - 6, y - 10, 12 * hpPercent, 4)

      // 矿工携带能量时显示额外UI（小金点效果）
      // 兼容两种字段名：carryingEnergy (camelCase) 和 carrying_energy (snake_case)
      const carryingEnergy = unit.carryingEnergy || unit.carrying_energy || 0
      if (unit.type === 'miner' && carryingEnergy > 0) {
        const energy = carryingEnergy

        // 在单位上方显示能量图标和数值
        const energyY = y - 18
        ctx.fillStyle = '#ffd700'
        ctx.font = 'bold 10px monospace'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.strokeStyle = '#000'
        ctx.lineWidth = 2
        ctx.strokeText(`⚡${energy}`, x, energyY)
        ctx.fillText(`⚡${energy}`, x, energyY)

        // 小金点效果：在单位周围显示多个小金点
        const time = Date.now() / 1000
        const pulse = Math.sin(time * 4) * 0.3 + 0.7 // 脉冲效果

        ctx.save()
        ctx.globalAlpha = pulse

        // 在单位周围绘制3-5个小金点
        const dotCount = Math.min(5, Math.max(3, Math.floor(energy / 10)))
        for (let i = 0; i < dotCount; i++) {
          const angle = (i / dotCount) * Math.PI * 2 + time * 0.5 // 旋转效果
          const radius = size / 2 + 4
          const dotX = x + Math.cos(angle) * radius
          const dotY = y + Math.sin(angle) * radius

          // 绘制小金点
          ctx.fillStyle = '#ffd700'
          ctx.beginPath()
          ctx.arc(dotX, dotY, 2, 0, Math.PI * 2)
          ctx.fill()

          // 外圈光晕
          ctx.fillStyle = '#ffeb3b'
          ctx.globalAlpha = pulse * 0.5
          ctx.beginPath()
          ctx.arc(dotX, dotY, 3, 0, Math.PI * 2)
          ctx.fill()
        }

        ctx.restore()

        // 能量光环效果
        ctx.strokeStyle = '#ffd700'
        ctx.lineWidth = 1
        ctx.globalAlpha = pulse * 0.5
        ctx.beginPath()
        ctx.arc(x, y, size / 2 + 2, 0, Math.PI * 2)
        ctx.stroke()
        ctx.globalAlpha = 1
      }

      // 工程师治疗时显示光环特效
      if (unit.type === 'engineer') {
        const state = this.gameState
        let isHealing = false

        // 方法1：检查healEffects中是否有工程师位置的特效
        if (state && state.room) {
          const heals = state.room.healEffects || state.room.heal_effects || []
          const unitX = unit.x
          const unitY = unit.y
          const threshold = 0.5 // 0.5格内的误差范围

          for (const heal of heals) {
            const healX = heal.x
            const healY = heal.y
            if (healX === undefined || healY === undefined) continue
            const dist = Math.sqrt((unitX - healX) ** 2 + (unitY - healY) ** 2)
            if (dist < threshold && heal.team === unit.team) {
              isHealing = true
              break
            }
          }
        }

        // 方法2：如果方法1没找到，检查周围3格内是否有受伤的友方单位
        if (!isHealing && state && state.room && state.room.units) {
          const healRange = 3 // 3格
          const unitX = unit.x
          const unitY = unit.y

          for (const ally of state.room.units) {
            if (ally.isDead || ally.team !== unit.team || ally.id === unit.id) {
              continue
            }
            if (ally.hp < ally.hpMax) {
              const dist = Math.sqrt((unitX - ally.x) ** 2 + (unitY - ally.y) ** 2)
              if (dist <= healRange) {
                isHealing = true
                break
              }
            }
          }
        }

        // 如果正在治疗，显示治疗光环
        if (isHealing) {
          const healColor = isRed ? '#2ecc71' : '#3498db'
          const time = Date.now() / 1000
          const pulse = Math.sin(time * 3) * 0.3 + 0.7 // 脉冲效果
          const healRange = 3 * this.TILE_SIZE // 3格转换为像素

          ctx.save()
          ctx.globalAlpha = pulse * 0.6
          ctx.strokeStyle = healColor
          ctx.lineWidth = 2

          // 外圈光环（3格范围）
          ctx.beginPath()
          ctx.arc(x, y, healRange, 0, Math.PI * 2)
          ctx.stroke()

          // 内圈光环（更亮）
          ctx.globalAlpha = pulse * 0.8
          ctx.lineWidth = 1.5
          ctx.beginPath()
          ctx.arc(x, y, healRange * 0.7, 0, Math.PI * 2)
          ctx.stroke()

          // 中心光点
          ctx.globalAlpha = pulse
          ctx.fillStyle = healColor
          ctx.beginPath()
          ctx.arc(x, y, 4, 0, Math.PI * 2)
          ctx.fill()

          ctx.restore()
        }
      }
    },

    drawPixelMiner (ctx, x, y, main, dark, light, isRed, size) {
      const scale = size / 16
      const uniformColor = isRed ? '#8b2500' : '#1a5276'
      const uniformLight = isRed ? '#cd5c5c' : '#5dade2'

      // 腿
      ctx.fillStyle = dark
      ctx.fillRect(x - 3 * scale, y + 2 * scale, 2 * scale, 4 * scale)
      ctx.fillRect(x + 1 * scale, y + 2 * scale, 2 * scale, 4 * scale)

      // 身体
      ctx.fillStyle = uniformColor
      ctx.fillRect(x - 4 * scale, y - 3 * scale, 8 * scale, 6 * scale)

      // 工装高光
      ctx.fillStyle = uniformLight
      ctx.fillRect(x - 3 * scale, y - 2 * scale, 2 * scale, 4 * scale)

      // 背包
      ctx.fillStyle = '#5c4a1f'
      ctx.fillRect(x - 6 * scale, y - 2 * scale, 3 * scale, 5 * scale)

      // 头
      ctx.fillStyle = '#ffcc99'
      ctx.fillRect(x - 2 * scale, y - 7 * scale, 4 * scale, 4 * scale)

      // 安全帽
      ctx.fillStyle = main
      ctx.fillRect(x - 3 * scale, y - 9 * scale, 6 * scale, 3 * scale)
      ctx.fillStyle = light
      ctx.fillRect(x - 4 * scale, y - 7 * scale, 8 * scale, 1 * scale)

      // 帽灯
      ctx.fillStyle = '#ffd700'
      ctx.fillRect(x - 1 * scale, y - 9 * scale, 2 * scale, 2 * scale)

      // 镐子
      ctx.fillStyle = '#8b4513'
      ctx.fillRect(x + 4 * scale, y - 8 * scale, 2 * scale, 10 * scale)
      ctx.fillStyle = '#708090'
      ctx.fillRect(x + 2 * scale, y - 10 * scale, 6 * scale, 3 * scale)
      ctx.fillRect(x + 6 * scale, y - 8 * scale, 2 * scale, 2 * scale)
    },

    drawPixelEngineer (ctx, x, y, main, dark, light, isRed, size) {
      const scale = size / 16
      const uniformColor = isRed ? '#a93226' : '#2471a3'
      const uniformLight = isRed ? '#ec7063' : '#85c1e9'

      // 腿
      ctx.fillStyle = dark
      ctx.fillRect(x - 3 * scale, y + 2 * scale, 2 * scale, 4 * scale)
      ctx.fillRect(x + 1 * scale, y + 2 * scale, 2 * scale, 4 * scale)

      // 身体
      ctx.fillStyle = uniformColor
      ctx.fillRect(x - 5 * scale, y - 4 * scale, 10 * scale, 7 * scale)

      // 工程服高光
      ctx.fillStyle = uniformLight
      ctx.fillRect(x - 4 * scale, y - 3 * scale, 3 * scale, 5 * scale)

      // 医疗包
      ctx.fillStyle = main
      ctx.fillRect(x - 7 * scale, y - 3 * scale, 4 * scale, 5 * scale)
      ctx.fillStyle = '#fff'
      ctx.fillRect(x - 6 * scale, y - 1 * scale, 2 * scale, 1 * scale)
      ctx.fillRect(x - 5 * scale, y - 2 * scale, 1 * scale, 3 * scale)

      // 头
      ctx.fillStyle = '#ffcc99'
      ctx.fillRect(x - 2 * scale, y - 8 * scale, 4 * scale, 4 * scale)

      // 护目镜
      ctx.fillStyle = light
      ctx.fillRect(x - 3 * scale, y - 6 * scale, 6 * scale, 2 * scale)
      ctx.fillStyle = '#333'
      ctx.fillRect(x - 1 * scale, y - 6 * scale, 1 * scale, 2 * scale)

      // 安全帽
      ctx.fillStyle = main
      ctx.fillRect(x - 3 * scale, y - 10 * scale, 6 * scale, 3 * scale)
      ctx.fillStyle = light
      ctx.fillRect(x - 2 * scale, y - 9 * scale, 4 * scale, 1 * scale)

      // 扳手
      ctx.fillStyle = '#bdc3c7'
      ctx.fillRect(x + 5 * scale, y - 6 * scale, 3 * scale, 8 * scale)
      ctx.fillRect(x + 4 * scale, y - 6 * scale, 5 * scale, 2 * scale)
      ctx.fillRect(x + 4 * scale, y + 0 * scale, 5 * scale, 2 * scale)
    },

    drawPixelHeavyTank (ctx, x, y, main, dark, light, size, angle, isRed) {
      const scale = size / 16

      // 履带
      ctx.fillStyle = '#1a1a1a'
      ctx.fillRect(x - 10 * scale, y + 2 * scale, 20 * scale, 6 * scale)
      ctx.fillStyle = '#333'
      for (let i = 0; i < 5; i++) {
        ctx.fillRect(x - 9 * scale + i * 4 * scale, y + 3 * scale, 2 * scale, 4 * scale)
      }

      // 车身
      ctx.fillStyle = dark
      ctx.fillRect(x - 9 * scale, y - 4 * scale, 18 * scale, 7 * scale)

      // 装甲板
      ctx.fillStyle = main
      ctx.fillRect(x - 8 * scale, y - 3 * scale, 16 * scale, 5 * scale)

      // 装甲纹理
      ctx.fillStyle = light
      ctx.fillRect(x - 7 * scale, y - 2 * scale, 2 * scale, 3 * scale)
      ctx.fillRect(x + 5 * scale, y - 2 * scale, 2 * scale, 3 * scale)

      // 炮塔
      ctx.save()
      ctx.translate(x, y - 6 * scale)

      // 旋转炮塔（根据方向）
      ctx.rotate(angle)

      // 炮塔基座
      ctx.fillStyle = dark
      ctx.fillRect(-6 * scale, -4 * scale, 12 * scale, 7 * scale)
      ctx.fillStyle = main
      ctx.fillRect(-5 * scale, -3 * scale, 10 * scale, 5 * scale)

      // 炮管（向右，旋转后会指向正确方向）
      ctx.fillStyle = '#444'
      ctx.fillRect(5 * scale, -2 * scale, 12 * scale, 4 * scale)
      ctx.fillStyle = '#555'
      ctx.fillRect(5 * scale, -1 * scale, 12 * scale, 2 * scale)

      ctx.restore()

      // 盾牌标志
      ctx.fillStyle = light
      ctx.fillRect(x - 2 * scale, y - 2 * scale, 4 * scale, 3 * scale)
      ctx.fillStyle = '#fff'
      ctx.fillRect(x - 1 * scale, y - 1 * scale, 2 * scale, 1 * scale)
    },

    drawPixelAssaultTank (ctx, x, y, main, dark, light, size, angle, isRed) {
      const scale = size / 16

      // 履带
      ctx.fillStyle = '#1a1a1a'
      ctx.fillRect(x - 7 * scale, y + 2 * scale, 14 * scale, 4 * scale)
      ctx.fillStyle = '#333'
      for (let i = 0; i < 4; i++) {
        ctx.fillRect(x - 6 * scale + i * 4 * scale, y + 3 * scale, 2 * scale, 2 * scale)
      }

      // 车身
      ctx.fillStyle = dark
      ctx.fillRect(x - 6 * scale, y - 2 * scale, 12 * scale, 5 * scale)

      // 车身高光
      ctx.fillStyle = main
      ctx.fillRect(x - 5 * scale, y - 1 * scale, 10 * scale, 3 * scale)

      // 炮塔
      ctx.save()
      ctx.translate(x, y - 3 * scale)

      // 旋转炮塔（根据方向）
      ctx.rotate(angle)

      // 炮塔基座
      ctx.fillStyle = dark
      ctx.fillRect(-4 * scale, -3 * scale, 8 * scale, 5 * scale)
      ctx.fillStyle = main
      ctx.fillRect(-3 * scale, -2 * scale, 6 * scale, 3 * scale)

      // 炮管（向右，旋转后会指向正确方向）
      ctx.fillStyle = '#444'
      ctx.fillRect(3 * scale, -1 * scale, 14 * scale, 2 * scale)
      ctx.fillStyle = '#555'
      ctx.fillRect(14 * scale, -1 * scale, 3 * scale, 2 * scale)

      ctx.restore()

      // 闪电标志
      ctx.fillStyle = light
      ctx.fillRect(x - 1 * scale, y - 1 * scale, 1 * scale, 1 * scale)
      ctx.fillRect(x - 2 * scale, y * scale, 2 * scale, 1 * scale)
      ctx.fillRect(x - 1 * scale, y + 1 * scale, 2 * scale, 1 * scale)
      ctx.fillRect(x * scale, y + 2 * scale, 1 * scale, 1 * scale)
    },

    drawBulletEffect (ctx, bullet) {
      const currentTime = Date.now() / 1000
      const createdTime = bullet.created_time || bullet.createdTime || currentTime
      const elapsed = currentTime - createdTime
      const lifetime = bullet.lifetime || 0.3

      if (elapsed > lifetime || elapsed < 0) {
        return // 特效已过期或未开始
      }

      const progress = elapsed / lifetime
      const fromX = (bullet.from_x || bullet.fromX || 0) * this.TILE_SIZE
      const fromY = (bullet.from_y || bullet.fromY || 0) * this.TILE_SIZE
      const toX = (bullet.to_x || bullet.toX || 0) * this.TILE_SIZE
      const toY = (bullet.to_y || bullet.toY || 0) * this.TILE_SIZE

      // 计算当前位置（根据进度插值）
      const currentX = fromX + (toX - fromX) * progress
      const currentY = fromY + (toY - fromY) * progress

      const isRed = bullet.team === 'red'
      const color = isRed ? '#ff6b6b' : '#5dade2'
      const glowColor = isRed ? '#ff4757' : '#4fc1ff'

      // 绘制子弹（带发光效果）
      ctx.save()
      ctx.globalAlpha = 1 - progress * 0.5 // 逐渐变透明

      // 外发光
      ctx.shadowBlur = 4
      ctx.shadowColor = glowColor
      ctx.fillStyle = color
      ctx.fillRect(currentX - 2, currentY - 2, 4, 4)

      // 核心
      ctx.shadowBlur = 0
      ctx.fillStyle = '#fff'
      ctx.fillRect(currentX - 1, currentY - 1, 2, 2)

      ctx.restore()
    },

    drawHealEffect (ctx, heal) {
      const currentTime = Date.now() / 1000
      const createdTime = heal.created_time || heal.createdTime || currentTime
      const elapsed = currentTime - createdTime
      const lifetime = heal.lifetime || 0.5

      if (elapsed > lifetime || elapsed < 0) {
        return // 特效已过期或未开始
      }

      const progress = elapsed / lifetime
      const x = heal.x * this.TILE_SIZE
      const y = heal.y * this.TILE_SIZE

      const isRed = heal.team === 'red'
      const color = isRed ? '#2ecc71' : '#3498db'

      ctx.save()
      ctx.globalAlpha = 1 - progress // 逐渐变透明

      // 绘制十字治疗符号
      const size = 8 * (1 - progress * 0.5) // 逐渐缩小

      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.beginPath()
      // 横线
      ctx.moveTo(x - size, y)
      ctx.lineTo(x + size, y)
      // 竖线
      ctx.moveTo(x, y - size)
      ctx.lineTo(x, y + size)
      ctx.stroke()

      // 外发光
      ctx.shadowBlur = 6
      ctx.shadowColor = color
      ctx.stroke()
      ctx.shadowBlur = 0

      // 中心点
      ctx.fillStyle = color
      ctx.fillRect(x - 2, y - 2, 4, 4)

      ctx.restore()
    },

    drawEnergyDrop (ctx, drop) {
      // 能量掉落显示为金色小光点，带脉冲效果
      const x = drop.x * this.TILE_SIZE
      const y = drop.y * this.TILE_SIZE
      const energy = drop.energy || 10

      // 使用时间创建脉冲效果
      const time = Date.now() / 1000
      const pulse = Math.sin(time * 3) * 0.3 + 0.7 // 0.4 到 1.0 之间脉冲

      ctx.save()

      // 外发光效果
      ctx.shadowBlur = 8
      ctx.shadowColor = '#ffd700'
      ctx.globalAlpha = pulse * 0.8

      // 绘制光点（金色）
      const radius = 3 + pulse * 1 // 半径在 3-4 之间变化
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
      gradient.addColorStop(0, '#ffeb3b') // 中心亮黄色
      gradient.addColorStop(0.5, '#ffd700') // 中间金色
      gradient.addColorStop(1, '#ffa500') // 边缘橙色

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      ctx.fill()

      // 内层高光
      ctx.globalAlpha = pulse
      ctx.fillStyle = '#fff'
      ctx.beginPath()
      ctx.arc(x, y, radius * 0.4, 0, Math.PI * 2)
      ctx.fill()

      // 重置阴影和透明度
      ctx.shadowBlur = 0
      ctx.globalAlpha = 1

      // 显示能量值（可选，如果能量较大则显示）
      if (energy > 20) {
        ctx.fillStyle = '#fff'
        ctx.strokeStyle = '#000'
        ctx.lineWidth = 2
        ctx.font = 'bold 8px monospace'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.strokeText(`${energy}`, x, y + radius + 2)
        ctx.fillText(`${energy}`, x, y + radius + 2)
      }

      ctx.restore()
    }
  }
}
</script>

<style scoped>
.game-canvas {
  display: block;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  border: 1px solid #3e3e42;
  background: #1e1e1e;
  /* 保持固定宽高比，避免形变 */
  /* 地图比例：60x40 = 3:2 */
  aspect-ratio: 3 / 2;
  /* 确保画布在容器中保持比例，不拉伸 */
  width: 100%;
  max-width: 100%;
  max-height: 100%;
  /* aspect-ratio 会自动计算高度，确保比例不变 */
}
</style>
