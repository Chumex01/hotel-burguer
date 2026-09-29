<script setup>
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const hora = new Date().getHours()
const saludo = hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches'
</script>

<template>
  <div>
    <div class="rounded-3xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-8 text-white shadow-xl">
      <p class="text-sm text-amber-400">{{ saludo }} 👋</p>
      <h2 class="mt-1 text-2xl font-bold">{{ auth.user?.nombre }}</h2>
      <p class="mt-2 max-w-lg text-sm text-slate-400">
        Bienvenido al panel de administración. Los módulos de habitaciones, reservas,
        servicios y pagos estarán disponibles pronto.
      </p>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="m in ['Habitaciones 🛏️', 'Reservas 📅', 'Servicios 🍳', 'Pagos 💰']" :key="m"
        class="rounded-2xl border-2 border-dashed border-slate-200 p-6 text-center text-slate-300 transition hover:border-amber-300 hover:text-amber-400"
      >
        <p class="text-3xl">{{ m.split(' ')[1] }}</p>
        <p class="mt-2 text-sm font-semibold">{{ m.split(' ')[0] }}</p>
        <p class="text-xs">Próximamente</p>
      </div>
    </div>
  </div>
</template>