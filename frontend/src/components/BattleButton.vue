<template>
  <button :class="['battle-btn', { 'battle-btn-small': small }]" @click="$emit('click', $event)">
    <span class="battle-btn-text">{{ text }}</span>
    <span class="battle-btn-glow"></span>
  </button>
</template>

<script>
export default {
  name: 'BattleButton',
  props: {
    text: {
      type: String,
      default: '对战'
    },
    small: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click']
}
</script>

<style scoped>
.battle-btn {
  position: relative;
  padding: 0.875rem 2.5rem;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 900;
  font-size: 1.25rem;
  color: #FFFFFF;
  text-shadow:
    2px 2px 0px rgba(139, 69, 19, 1),
    4px 4px 0px rgba(139, 69, 19, 0.8),
    -1px -1px 0px rgba(255, 255, 255, 0.3);
  letter-spacing: 0.05em;
  /* 3D凸起效果：顶部亮，底部暗，外阴影 */
  box-shadow:
    0 6px 0px rgba(139, 69, 19, 0.8),
    0 4px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.1s ease-out;
  overflow: visible;
}

.battle-btn-text {
  position: relative;
  z-index: 1;
  display: block;
  transition: transform 0.1s ease-out;
}

.battle-btn-glow {
  display: none;
}

/* hover和active：按下效果 */
.battle-btn:hover,
.battle-btn:active {
  transform: translateY(4px);
  /* 按下效果：顶部暗，底部亮，减少外阴影 */
  box-shadow:
    0 2px 0px rgba(139, 69, 19, 0.8),
    0 1px 0px rgba(139, 69, 19, 0.9),
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}

.battle-btn:hover .battle-btn-text,
.battle-btn:active .battle-btn-text {
  transform: translateY(1px);
}

/* 小尺寸变体 */
.battle-btn-small {
  padding: 0.625rem 1.75rem;
  font-size: 1rem;
  border-radius: 6px;
}

.battle-btn-small:hover,
.battle-btn-small:active {
  transform: translateY(3px);
  box-shadow:
    0 1px 0px rgba(139, 69, 19, 0.8),
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 -2px 4px rgba(255, 255, 255, 0.2);
}
</style>
