<script setup>
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const estilos = {
  success: 'bg-emerald-600',
  error: 'bg-rose-600',
  info: 'bg-sky-600',
}
const iconos = { success: '✓', error: '✕', info: 'ℹ' }
</script>

<template>
  <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80">
    <TransitionGroup
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-x-8 opacity-0"
      enter-to-class="translate-x-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-for="t in toast.toasts"
        :key="t.id"
        class="flex items-center gap-3 rounded-xl px-4 py-3 text-white shadow-lg shadow-slate-900/20"
        :class="estilos[t.tipo]"
      >
        <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/25 text-sm font-bold">
          {{ iconos[t.tipo] }}
        </span>
        <p class="text-sm leading-snug">{{ t.mensaje }}</p>
      </div>
    </TransitionGroup>
  </div>
</template>