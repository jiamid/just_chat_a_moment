import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:roomId',
    name: 'ChatRoom',
    component: Chat,
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

  // 如果已登录但访问首页，重定向到聊天页
  if (to.name === 'Home' && token) {
    next('/chat')
    return
  }

  // 验证房间号参数
  if (to.name === 'ChatRoom' && to.params.roomId) {
    const roomId = parseInt(to.params.roomId)
    // 检查房间号是否为有效数字且大于0
    if (isNaN(roomId) || roomId <= 0) {
      next('/chat')
      return
    }
  }

  next()
})

export default router
