<script setup>
import { ref } from 'vue'
import HabitacionesPanel from '@/components/habitaciones/HabitacionesPanel.vue'
import TiposPanel from '@/components/habitaciones/TiposPanel.vue'

const tab = ref('habitaciones')
const tabs = [
  { id: 'habitaciones', label: 'Habitaciones', icono: '🛏️' },
  { id: 'tipos', label: 'Tipos y Precios', icono: '🏷️' },
]
</script>

<template>
  <div>
    <div class="mb-6 inline-flex rounded-2xl bg-white p-1.5 shadow-sm ring-1 ring-slate-200">
      <button
        v-for="t in tabs"
        :key="t.id"
        @click="tab = t.id"
        class="flex items-center gap-2 rounded-xl px-6 py-2.5 text-sm font-semibold transition-all duration-200"
        :class="tab === t.id ? 'bg-slate-900 text-white shadow-md' : 'text-slate-500 hover:text-slate-800'"
      >
        <span>{{ t.icono }}</span> {{ t.label }}
      </button>
    </div>

    <Transition mode="out-in"
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0 translate-y-2"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <HabitacionesPanel v-if="tab === 'habitaciones'" key="hab" />
      <TiposPanel v-else key="tipos" />
    </Transition>
  </div>
</template>