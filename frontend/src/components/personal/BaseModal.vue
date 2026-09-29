<script setup>
import { watch, onUnmounted } from 'vue'

const props = defineProps({
  titulo: String,
  abierta: Boolean,   // ⬅️ el v-if vive AQUÍ adentro
})
const emit = defineEmits(['cerrar'])

// Cerrar con tecla Escape ✨
function onKey(e) {
  if (e.key === 'Escape' && props.abierta) emit('cerrar')
}
window.addEventListener('keydown', onKey)
onUnmounted(() => window.removeEventListener('keydown', onKey))

// Bloquear el scroll del fondo mientras está abierto ✨
watch(
  () => props.abierta,
  (abierto) => {
    document.body.style.overflow = abierto ? 'hidden' : ''
  },
)
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
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
      @click.self="emit('cerrar')"
    >
      <div class="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h3 class="text-lg font-bold text-slate-800">{{ titulo }}</h3>
          <button
            @click="emit('cerrar')"
            class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            ✕
          </button>
        </div>
        <div class="max-h-[70vh] overflow-y-auto p-6">
          <slot />
        </div>
      </div>
    </div>
  </Transition>
</template>