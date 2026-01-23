import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ChatRoom from '../views/ChatRoom.vue'
import DrawingRoom from '../views/DrawingRoom.vue'
import LiveWarRoom from '../views/LiveWarRoom.vue'
import AIChat from '../views/AIChat.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/room/chat/:roomId',
    name: 'ChatRoom',
    component: ChatRoom,
    meta: { requiresAuth: true }
  },
  {
    path: '/room/drawing/:roomId',
    name: 'DrawingRoom',
    component: DrawingRoom,
    meta: { requiresAuth: true }
  },
  {
    path: '/room/live_war/:roomId',
    name: 'LiveWarRoom',
    component: LiveWarRoom,
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-chat',
    name: 'AIChat',
    component: AIChat,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next('/')
    return
  }

  // 允许已登录用户访问主页（不再自动跳转）

  // 验证房间号参数
  if ((to.name === 'ChatRoom' || to.name === 'DrawingRoom' || to.name === 'LiveWarRoom') && to.params.roomId) {
    const roomId = parseInt(to.params.roomId)
    // 检查房间号是否为有效数字且大于0
    if (isNaN(roomId) || roomId <= 0) {
      next('/')
      return
    }
  }

  next()
})

export default router
