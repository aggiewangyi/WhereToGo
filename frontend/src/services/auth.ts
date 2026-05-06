import api from './api'

export type UserMe = {
  id: number
  phone: string
  nickname: string
  avatar: string | null
  is_verified: boolean
  created_at: string
}

export async function authMe(): Promise<UserMe> {
  const { data } = await api.get<UserMe>('/auth/me')
  return data
}
