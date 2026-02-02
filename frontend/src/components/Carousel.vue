<template>
  <div class="carousel-wrapper">
    <!-- 卡片轮播图 - 圆形循环 -->
    <div class="carousel-container">
      <div
        v-for="(card, index) in cards"
        :key="index"
        :class="['carousel-card', { active: index === currentCardIndex }]"
        :style="getCardStyle(index)"
        @click="goToCard(index)"
      >
        <div class="card-content">
          <h3 class="card-title">{{ card.title }}</h3>
          <p class="card-description">{{ card.description }}</p>
          <BattleButton v-if="card.showButton" text="Enter" @click.stop="handleEnterClick(index)" />
        </div>
      </div>
      <!-- 左右切换按钮 -->
      <button class="carousel-btn carousel-btn-prev" @click="prevCard">‹</button>
      <button class="carousel-btn carousel-btn-next" @click="nextCard">›</button>
    </div>
    <!-- 指示器 -->
    <div class="carousel-indicators">
      <span
        v-for="(card, index) in cards"
        :key="index"
        :class="['indicator', { active: index === currentCardIndex }]"
        @click="goToCard(index)"
      ></span>
    </div>
  </div>
</template>

<script>
import BattleButton from '@/components/BattleButton.vue'

export default {
  name: 'Carousel',
  components: {
    BattleButton
  },
  props: {
    cards: {
      type: Array,
      default: () => []
    }
  },
  emits: ['enter'],
  data () {
    return {
      currentCardIndex: 0,
      currentCardIndexFloat: 0
    }
  },
  methods: {
    nextCard () {
      const total = this.cards.length || 1
      this.currentCardIndexFloat = (this.currentCardIndexFloat + 1 + total) % total
      this.currentCardIndex = Math.round(this.currentCardIndexFloat) % total
    },

    prevCard () {
      const total = this.cards.length || 1
      this.currentCardIndexFloat = (this.currentCardIndexFloat - 1 + total) % total
      this.currentCardIndex = Math.round(this.currentCardIndexFloat) % total
    },

    goToCard (index) {
      const total = this.cards.length || 1
      const safeIndex = ((index % total) + total) % total
      this.currentCardIndexFloat = safeIndex
      this.currentCardIndex = safeIndex
    },

    handleEnterClick (index) {
      this.$emit('enter', { card: this.cards[index], index })
    },

    getCardStyle (index) {
      const total = this.cards.length
      const angleStep = 360 / total
      const offset = index - this.currentCardIndex
      const angle = offset * angleStep

      const isMobile = window.innerWidth <= 768
      const radius = isMobile ? 180 : 300

      const radian = (angle * Math.PI) / 180
      const x = Math.sin(radian) * radius
      const z = Math.cos(radian) * radius

      const normalizedZ = (z + radius) / (2 * radius)
      const scale = 0.5 + normalizedZ * 0.25
      const opacity = normalizedZ > 0.3 ? 1 : Math.max(0.4, normalizedZ * 1.5)
      const zIndex = Math.round(normalizedZ * total * 2)

      return {
        transform: `translateX(${x}px) translateZ(${z}px) scale(${scale})`,
        opacity,
        zIndex
      }
    }
  }
}
</script>

<style scoped>
.carousel-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
  flex: 1;
  min-height: 0;
}

.carousel-container {
  position: relative;
  width: 100%;
  max-width: 1200px;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  margin: 0 auto;
  perspective: 1000px;
  transform-style: preserve-3d;
  padding: 1rem 0;
  box-sizing: border-box;
}

.carousel-card {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 330px;
  height: 440px;
  margin-left: -165px;
  margin-top: -220px;
  cursor: pointer;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
  max-width: calc(100% - 2rem);
  max-height: calc(100% - 2rem);
  box-sizing: border-box;
  aspect-ratio: 3 / 4;
}

.card-content {
  width: 100%;
  height: 100%;
  max-height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  padding: 2rem;
  box-sizing: border-box;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
}

.card-title {
  font-size: 1.4rem;
  font-weight: 900;
  color: #2C3E50;
  margin: 0 0 1rem 0;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.carousel-card.active .card-title {
  font-size: 1.6rem;
}

.card-description {
  font-size: 1rem;
  color: #7F8C8D;
  text-align: center;
  line-height: 1.6;
  margin: 0;
  white-space: pre-line;
}

.carousel-card.active .card-description {
  font-size: 1.1rem;
}

.card-content .battle-btn {
  position: absolute;
  bottom: 1em;
  left: 1em;
  right: 1em;
  width: calc(100% - 2em);
}

.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  border: 4px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  font-size: 2rem;
  font-weight: 900;
  color: #2C3E50;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  line-height: 1;
}

.carousel-btn:hover {
  transform: translateY(-50%) scale(1.1);
  box-shadow:
    0 6px 12px rgba(0, 0, 0, 0.2),
    0 3px 6px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.carousel-btn:active {
  transform: translateY(-50%) scale(1.05);
}

.carousel-btn-prev {
  left: 1rem;
}

.carousel-btn-next {
  right: 1rem;
}

.carousel-indicators {
  position: relative;
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
  padding: 0.5rem 0;
}

.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  border: 2px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.indicator.active {
  background: rgba(255, 255, 255, 1);
  width: 30px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.indicator:hover {
  background: rgba(255, 255, 255, 0.8);
}

@media (max-width: 768px) {
  .carousel-container {
    height: 100%;
    max-width: 100%;
    padding: 0.5rem 0;
    box-sizing: border-box;
    perspective: 800px;
  }

  .carousel-card {
    width: 270px;
    height: 360px;
    margin-left: -135px;
    margin-top: -180px;
    max-width: calc(100% - 2rem);
    max-height: calc(100% - 2rem);
    box-sizing: border-box;
    aspect-ratio: 3 / 4;
  }

  .card-content {
    padding: 1.5rem;
  }

  .card-title {
    font-size: 1.2rem;
  }

  .carousel-card.active .card-title {
    font-size: 1.35rem;
  }

  .card-description {
    font-size: 0.9rem;
  }

  .carousel-btn {
    width: 40px;
    height: 40px;
    font-size: 1.5rem;
  }

  .carousel-btn-prev {
    left: 0.5rem;
  }

  .carousel-btn-next {
    right: 0.5rem;
  }
}
</style>
