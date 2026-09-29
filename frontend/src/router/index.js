import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'personal', name: 'personal', component: () => import('@/views/PersonalView.vue') },
      { path: 'habitaciones', name: 'habitaciones', component: () => import('@/views/HabitacionesView.vue') },
      { path: 'huespedes', name: 'huespedes', component: () => import('@/views/HuespedesView.vue') },
      { path: 'reservas', name: 'reservas', component: () => import('@/views/ReservasView.vue') },
      { path: 'servicios', name: 'servicios', component: () => import('@/views/ServiciosView.vue') },
      { path: 'pagos', name: 'pagos', component: () => import('@/views/PagosView.vue') },
      // Próximos módulos: /habitaciones, /reservas, /servicios, /pagos
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    return auth.isAuthenticated ? { name: 'dashboard' } : true
  }
  return auth.isAuthenticated ? true : { name: 'login' }
})

export default router