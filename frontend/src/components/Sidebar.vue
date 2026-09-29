<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const modulos = [
  { name: 'dashboard', label: 'Dashboard', to: '/', icon: '...' },        // el que ya tienes
  { name: 'habitaciones', label: 'Habitaciones', to: '/habitaciones', icon: 'M3.375 19.5h17.25m-17.25 0a1.125...' }, // el icono que estaba en proximamente
  { name: 'personal', label: 'Personal', to: '/personal', icon: '...' }, // el que ya tienes
  { name: 'huespedes', label: 'Huéspedes', to: '/huespedes', icon: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z' },
  { name: 'reservas', label: 'Reservas', to: '/reservas', icon: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5' },
  { name: 'servicios', label: 'Servicios', to: '/servicios', icon: 'M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z M6 6h.008v.008H6V6z' },
  { name: 'pagos', label: 'Pagos', to: '/pagos', icon: 'M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z' },
]


const iniciales = (nombre = '') =>
  nombre.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()

async function cerrarSesion() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="flex h-screen w-64 flex-col bg-slate-900 text-slate-300">
    <!-- Logo -->
    <div class="flex items-center gap-3 px-6 py-6">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 text-xl shadow-lg shadow-amber-500/30">
        🏨
      </div>
      <div>
        <p class="text-lg font-bold text-white leading-tight">HotelSys</p>
        <p class="text-[11px] text-slate-500">Panel Administrativo</p>
      </div>
    </div>

    <!-- Navegación -->
    <nav class="flex-1 space-y-1 overflow-y-auto px-3">
      <p class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">Menú</p>

      <RouterLink
        v-for="m in modulos"
        :key="m.name"
        :to="m.to"
        class="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200"
        :class="$route.name === m.name
          ? 'bg-amber-500/10 text-amber-400 shadow-inner'
          : 'hover:bg-slate-800 hover:text-white'"
      >
        <svg class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" :d="m.icon" />
        </svg>
        {{ m.label }}
        <span
          v-if="$route.name === m.name"
          class="ml-auto h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"
        />
      </RouterLink>

      <p class="px-3 pt-5 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-600">Próximamente</p>
        <span
          v-for="p in proximamente"
          :key="p.label"
          class="flex cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-600"
          title="Módulo en desarrollo"
        >
        <svg class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" :d="p.icon" />
        </svg>
        {{ p.label }}
      </span>
    </nav>

    <!-- Usuario -->
    <div class="border-t border-slate-800 p-4">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-indigo-600 text-sm font-bold text-white">
          {{ iniciales(auth.user?.nombre) }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold text-white">{{ auth.user?.nombre }}</p>
          <p class="truncate text-xs text-amber-400">{{ auth.user?.rol_nombre }}</p>
        </div>
        <button
          @click="cerrarSesion"
          title="Cerrar sesión"
          class="rounded-lg p-2 text-slate-400 transition hover:bg-rose-500/10 hover:text-rose-400"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>