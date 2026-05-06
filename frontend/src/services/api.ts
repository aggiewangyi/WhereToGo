import axios from 'axios'

const TOKEN_KEY = 'wheretogo_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

function agentHeaders(): Record<string, string> {
  const key = (import.meta.env.VITE_AGENT_API_KEY as string | undefined)?.trim()
  if (!key) return {}
  return { 'X-Agent-API-Key': key }
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const t = getToken()
  if (t) config.headers.Authorization = `Bearer ${t}`
  Object.assign(config.headers, agentHeaders())
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      setToken(null)
      localStorage.removeItem('wheretogo_chat_session_id')
      const path = window.location.pathname
      if (path !== '/login' && path !== '/register') {
        const q = new URLSearchParams({ redirect: path + (window.location.search || '') })
        window.location.assign(`/login?${q.toString()}`)
      }
    }
    return Promise.reject(err)
  },
)

export default api
export { agentHeaders }
