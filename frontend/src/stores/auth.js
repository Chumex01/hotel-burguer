import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('hotel_token'))
  const user = ref(JSON.parse(localStorage.getItem('hotel_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  // El backend usa OAuth2PasswordRequestForm → form-urlencoded
  async function login(username, password) {
    const body = new URLSearchParams({ username, password })
    const { data } = await api.post('/auth/login', body)

    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('hotel_token', data.access_token)
    localStorage.setItem('hotel_user', JSON.stringify(data.user))
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // si el token ya expiró, igual cerramos sesión local
    }
    token.value = null
    user.value = null
    localStorage.removeItem('hotel_token')
    localStorage.removeItem('hotel_user')
  }

  return { token, user, isAuthenticated, login, logout }
})