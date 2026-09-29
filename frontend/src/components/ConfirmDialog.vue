<script setup>
import { onUnmounted } from 'vue'

defineProps({
  abierta: Boolean,
  titulo: { type: String, default: '¿Estás seguro?' },
  mensaje: { type: String, default: '' },
  textoConfirmar: { type: String, default: 'Eliminar' },
  cargando: Boolean,
})
const emit = defineEmits(['cancelar', 'confirmar'])

function onKey(e) {
  if (e.key === 'Escape') emit('cancelar')
}
window.addEventListener('keydown', onKey)
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    leave-active-class="transition duration-150 ease-in"
    leave-to-class="opacity-0"
  >
    <div
      v-if="abierta"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
      @click.self="emit('cancelar')"
    >
      <div class="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
        <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-2xl">
          🗑️
        </div>
        <h3 class="text-lg font-bold text-slate-800">{{ titulo }}</h3>
        <p class="mt-1 text-sm text-slate-500">{{ mensaje }}</p>
        <div class="mt-5 flex justify-end gap-3">
          <button
            @click="emit('cancelar')"
            class="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            @click="emit('confirmar')"
            :disabled="cargando"
            class="rounded-xl bg-rose-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-rose-500 active:scale-95 disabled:opacity-60"
          >
            {{ cargando ? 'Eliminando...' : textoConfirmar }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>