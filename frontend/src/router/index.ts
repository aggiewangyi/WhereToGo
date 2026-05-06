import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/services/api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { guest: true } },
    { path: '/register', name: 'Register', component: () => import('@/pages/Register.vue'), meta: { guest: true } },
    { path: '/', name: 'Agent', component: () => import('@/pages/AgentConsole.vue'), meta: { auth: true } },
  ],
})

router.beforeEach((to) => {
  const t = getToken()
  if (to.meta.auth && !t) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && t) {
    return { path: '/' }
  }
})

export default router
