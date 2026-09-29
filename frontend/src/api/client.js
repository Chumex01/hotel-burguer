import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

// Cada request lleva el token automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hotel_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Si el backend responde 401 (token expirado/revocado) → fuera
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const esLogin = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !esLogin) {
      localStorage.removeItem('hotel_token')
      localStorage.removeItem('hotel_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api