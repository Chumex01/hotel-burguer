<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'

const route = useRoute()

const titulos = {
  dashboard: 'Dashboard',
  personal: 'Gestión de Personal',
  habitaciones: 'Gestión de Habitaciones',
  huespedes: 'Gestión de Huéspedes',
  reservas: 'Gestión de Reservas',
  servicios: 'Servicios y Consumos',
  pagos: 'Caja y Pagos',
}

const titulo = computed(() => titulos[route.name] || 'HotelSys')
const fechaHoy = new Date().toLocaleDateString('es-BO', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
})
</script>

<template>
  <div class="flex min-h-screen bg-slate-100">
    <Sidebar />

    <div class="flex flex-1 flex-col">
      <!-- Topbar -->
      <header class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8">
        <div>
          <h1 class="text-lg font-bold text-slate-800">{{ titulo }}</h1>
        </div>
        <p class="text-sm capitalize text-slate-500">{{ fechaHoy }}</p>
      </header>

      <!-- Contenido -->
      <main class="flex-1 overflow-y-auto p-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>