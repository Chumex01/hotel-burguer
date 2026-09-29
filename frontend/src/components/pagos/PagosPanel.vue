<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import AnularPagoModal from './AnularPagoModal.vue'

const toast = useToastStore()

const pagos = ref([])
const cargando = ref(true)
const filtro = ref('Todos')

const aAnular = ref(null)
const aReembolsar = ref(null)
const procesando = ref(false)

const ESTADOS = ['Pagado', 'Pendiente', 'Anulado', 'Reembolsado']

const estilosPago = {
  Pagado: 'bg-emerald-100 text-emerald-700',
  Pendiente: 'bg-amber-100 text-amber-700',
  Anulado: 'bg-rose-100 text-rose-500',
  Reembolsado: 'bg-sky-100 text-sky-700',
}

const METODOS = { Efectivo: '💵', Transferencia: '🏦', Tarjeta: '💳', QR: '📱' }
const emojiMetodo = (m) => METODOS[m] || '💰'

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`
const formatoFechaHora = (f) =>
  new Date(f).toLocaleString('es-BO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })

const filtrados = computed(() =>
  filtro.value === 'Todos'
    ? pagos.value
    : pagos.value.filter((p) => p.estado === filtro.value),
)

const conteo = (estado) =>
  estado === 'Todos'
    ? pagos.value.length
    : pagos.value.filter((p) => p.estado === estado).length

// Montos por estado — lo que quiere ver contabilidad
const stats = computed(() => {
  const suma = (estado) =>
    pagos.value
      .filter((p) => p.estado === estado)
      .reduce((a, p) => a + Number(p.monto), 0)
  return {
    cobrado: suma('Pagado'),
    pendiente: suma('Pendiente'),
    anulado: suma('Anulado'),
    reembolsado: suma('Reembolsado'),
  }
})

const hoy = new Date().toDateString()
const cobradoHoy = computed(() =>
  pagos.value
    .filter((p) => p.estado === 'Pagado' && new Date(p.fecha_pago).toDateString() === hoy)
    .reduce((a, p) => a + Number(p.monto), 0),
)

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/pago/')
    // Más recientes primero
    pagos.value = [...data].sort((a, b) => new Date(b.fecha_pago) - new Date(a.fecha_pago))
  } catch {
    toast.show('Error al cargar los pagos', 'error')
  } finally {
    cargando.value = false
  }
}

async function anular(observacion) {
  procesando.value = true
  try {
    await api.patch(`/pago/${aAnular.value.id_pago}/anular`, null, { params: { observacion } })
    toast.show('Pago anulado', 'info')
    aAnular.value = null
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al anular', 'error')
    aAnular.value = null
  } finally {
    procesando.value = false
  }
}

async function reembolsar() {
  procesando.value = true
  try {
    await api.patch(`/pago/${aReembolsar.value.id_pago}/reembolsar`)
    toast.show('Pago reembolsado', 'info')
    aReembolsar.value = null
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al reembolsar', 'error')
    aReembolsar.value = null
  } finally {
    procesando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <!-- Stats contables -->
    <div class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Cobrado hoy</p>
        <p class="mt-1 text-2xl font-black text-emerald-600">{{ formatoPrecio(cobradoHoy) }}</p>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Total cobrado</p>
        <p class="mt-1 text-2xl font-black text-slate-800">{{ formatoPrecio(stats.cobrado) }}</p>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Anulado</p>
        <p class="mt-1 text-2xl font-black text-rose-500">{{ formatoPrecio(stats.anulado) }}</p>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Reembolsado</p>
        <p class="mt-1 text-2xl font-black text-sky-600">{{ formatoPrecio(stats.reembolsado) }}</p>
      </div>
    </div>

    <!-- Tabla -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="flex flex-wrap items-center gap-2 border-b border-slate-100 p-4">
        <button
          v-for="e in ['Todos', ...ESTADOS]"
          :key="e"
          @click="filtro = e"
          class="rounded-full px-4 py-1.5 text-xs font-semibold transition"
          :class="filtro === e ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
        >
          {{ e }} ({{ conteo(e) }})
        </button>
      </div>

      <div class="overflow-x-auto p-2">
        <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando pagos...</div>

        <table v-else class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs uppercase tracking-wide text-slate-400">
              <th class="px-4 py-3">Pago</th>
              <th class="px-4 py-3">Reserva</th>
              <th class="px-4 py-3">Método</th>
              <th class="px-4 py-3">Fecha</th>
              <th class="px-4 py-3">Estado</th>
              <th class="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in filtrados"
              :key="p.id_pago"
              class="group border-t border-slate-50 transition hover:bg-slate-50/80"
              :class="{ 'opacity-50': p.estado === 'Anulado' }"
            >
              <td class="px-4 py-3.5">
                <p class="font-black text-slate-800" :class="{ 'line-through': p.estado === 'Anulado' }">
                  {{ formatoPrecio(p.monto) }}
                </p>
                <p v-if="p.observacion" class="max-w-48 truncate text-xs text-slate-400">📝 {{ p.observacion }}</p>
              </td>
              <td class="px-4 py-3.5 font-semibold text-slate-600">#{{ p.id_reserva }}</td>
              <td class="px-4 py-3.5 text-slate-600">{{ emojiMetodo(p.metodo_pago) }} {{ p.metodo_pago }}</td>
              <td class="px-4 py-3.5 text-slate-500">{{ formatoFechaHora(p.fecha_pago) }}</td>
              <td class="px-4 py-3.5">
                <span class="rounded-full px-3 py-1 text-xs font-bold" :class="estilosPago[p.estado]">
                  {{ p.estado }}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <div class="flex justify-end gap-1 opacity-0 transition group-hover:opacity-100">
                  <button
                    v-if="p.estado === 'Pagado'"
                    @click="aAnular = p"
                    title="Anular"
                    class="rounded-lg px-2 py-1.5 text-xs transition hover:bg-rose-50"
                  >🚫</button>
                  <button
                    v-if="p.estado === 'Pagado'"
                    @click="aReembolsar = p"
                    title="Reembolsar"
                    class="rounded-lg px-2 py-1.5 text-xs transition hover:bg-sky-50"
                  >↩️</button>
                </div>
              </td>
            </tr>

            <tr v-if="!filtrados.length">
              <td colspan="6" class="px-4 py-12 text-center text-slate-400">
                💳 No hay pagos con ese filtro
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AnularPagoModal
      :abierta="!!aAnular"
      :pago="aAnular"
      :cargando="procesando"
      @cerrar="aAnular = null"
      @confirmar="anular"
    />

    <ConfirmDialog
      :abierta="!!aReembolsar"
      :cargando="procesando"
      titulo="¿Reembolsar este pago?"
      :mensaje="aReembolsar ? `Se marcará como Reembolsado: ${aReembolsar.metodo_pago} · Bs ${Number(aReembolsar.monto).toFixed(2)}` : ''"
      textoConfirmar="Sí, reembolsar"
      @cancelar="aReembolsar = null"
      @confirmar="reembolsar"
    />
  </div>
</template>