import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api, { getToken, setToken } from '@/services/api'
import { authMe, type UserMe } from '@/services/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(getToken())
  const user = ref<UserMe | null>(null)

  const isLoggedIn = computed(() => Boolean(token.value))

  async function bootstrap() {
    if (!getToken()) {
      token.value = null
      user.value = null
      return
    }
    token.value = getToken()
    try {
      user.value = await authMe()
    } catch {
      setToken(null)
      token.value = null
      user.value = null
    }
  }

  async function login(phone: string, password: string) {
    const { data } = await api.post<{ access_token: string }>('/auth/login', { phone, password })
    setToken(data.access_token)
    token.value = data.access_token
    user.value = await authMe()
  }

  async function register(payload: { phone: string; nickname: string; password: string }) {
    const { data } = await api.post<{ access_token: string }>('/auth/register', payload)
    setToken(data.access_token)
    token.value = data.access_token
    user.value = await authMe()
  }

  function logout() {
    setToken(null)
    token.value = null
    user.value = null
    localStorage.removeItem('wheretogo_chat_session_id')
  }

  return { token, user, isLoggedIn, bootstrap, login, register, logout }
})
