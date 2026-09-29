<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  abierta: Boolean,
  pago: Object,
  cargando: Boolean,
})
const emit = defineEmits(['cerrar', 'confirmar'])

const observacion = ref('')

watch(
  () => props.abierta,
  (a) => {
    if (a) observacion.value = ''
  },
)

function onKey(e) {
  if (e.key === 'Escape' && props.abierta) emit('cerrar')
}
window.addEventListener('keydown', onKey)
onUnmounted(() => window.removeEventListener('keydown', onKey))

function confirmar() {
  if (!observacion.value.trim()) return
  emit('confirmar', observacion.value.trim())
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    leave-to-class="opacity-0"
  >
    <div
      v-if="abierta"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
      @click.self="emit('cerrar')"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <div class="mb-3 flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-2xl">🚫</div>
          <div>
            <h3 class="text-lg font-bold text-slate-800">Anular pago</h3>
            <p v-if="pago" class="text-sm text-slate-500">
              {{ pago.metodo_pago }} · Bs {{ Number(pago.monto).toFixed(2) }}
            </p>
          </div>
        </div>

        <p class="mb-3 text-sm text-slate-500">
          El pago <strong>no se elimina</strong>: quedará registrado como <em>Anulado</em> con
          su justificación, como manda la buena contabilidad 🧾
        </p>

        <label class="mb-1 block text-xs font-semibold text-slate-500">Justificación *</label>
        <textarea
          v-model="observacion"
          rows="3"
          placeholder="Ej: error de digitación, se registró dos veces..."
          class="w-full resize-none rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
        />

        <div class="mt-4 flex justify-end gap-3">
          <button
            @click="emit('cerrar')"
            class="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            @click="confirmar"
            :disabled="cargando || !observacion.trim()"
            class="rounded-xl bg-rose-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-rose-500 active:scale-95 disabled:opacity-40"
          >
            {{ cargando ? 'Anulando...' : 'Anular pago' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>