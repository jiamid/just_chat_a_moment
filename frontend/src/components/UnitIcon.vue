<script setup>
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  unitType: {
    type: String,
    required: true,
    validator: (value) => ['miner', 'engineer', 'heavy_tank', 'assault_tank'].includes(value)
  },
  team: {
    type: String,
    default: 'red',
    validator: (value) => ['red', 'blue'].includes(value)
  },
  size: {
    type: Number,
    default: 32
  }
})

const canvasRef = ref(null)

function draw () {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const size = props.size || 32

  // 清空画布
  ctx.clearRect(0, 0, size, size)

  ctx.imageSmoothingEnabled = false

  const x = size / 2
  const y = size / 2

  const isRed = (props.team || 'red') === 'red'
  const mainColor = isRed ? '#e74c3c' : '#3498db'
  const darkColor = isRed ? '#c0392b' : '#2980b9'
  const lightColor = isRed ? '#ff6b6b' : '#5dade2'

  // 根据单位类型绘制
  if (props.unitType === 'miner') {
    drawPixelMiner(ctx, x, y, mainColor, darkColor, lightColor, isRed, size)
  } else if (props.unitType === 'engineer') {
    drawPixelEngineer(ctx, x, y, mainColor, darkColor, lightColor, isRed, size)
  } else if (props.unitType === 'heavy_tank') {
    drawPixelHeavyTank(ctx, x, y, mainColor, darkColor, lightColor, size)
  } else if (props.unitType === 'assault_tank') {
    drawPixelAssaultTank(ctx, x, y, mainColor, darkColor, lightColor, size)
  }
}

onMounted(() => {
  draw()
})

watch(() => [props.unitType, props.team, props.size], () => {
  draw()
})

function drawPixelMiner (ctx, x, y, main, dark, light, isRed, size) {
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
}

function drawPixelEngineer (ctx, x, y, main, dark, light, isRed, size) {
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
}

function drawPixelHeavyTank (ctx, x, y, main, dark, light, size) {
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

  // 炮塔基座
  ctx.fillStyle = dark
  ctx.fillRect(-6 * scale, -4 * scale, 12 * scale, 7 * scale)
  ctx.fillStyle = main
  ctx.fillRect(-5 * scale, -3 * scale, 10 * scale, 5 * scale)

  // 炮管
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
}

function drawPixelAssaultTank (ctx, x, y, main, dark, light, size) {
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

  // 炮塔基座
  ctx.fillStyle = dark
  ctx.fillRect(-4 * scale, -3 * scale, 8 * scale, 5 * scale)
  ctx.fillStyle = main
  ctx.fillRect(-3 * scale, -2 * scale, 6 * scale, 3 * scale)

  // 炮管
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
}
</script>

<template>
  <canvas
    ref="canvasRef"
    :width="props.size || 32"
    :height="props.size || 32"
    class="unit-icon"
  ></canvas>
</template>

<style scoped>
.unit-icon {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}
</style>
