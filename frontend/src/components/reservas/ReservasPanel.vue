<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ReservaFormModal from './ReservaFormModal.vue'
import DetalleReservaModal from './DetalleReservaModal.vue'

const toast = useToastStore()

const reservas = ref([])
const habitaciones = ref([])
const tipos = ref([])
const huespedes = ref([])
const cargando = ref(true)
const filtroEstado = ref('Todas')
const busqueda = ref('')

const modalCrear = ref(false)
const editando = ref(null)        // reserva a editar
const detalleId = ref(null)       // reserva a ver en detalle
const aCancelar = ref(null)
const procesando = ref(false)

const ESTADOS = ['Pendiente', 'Confirmada', 'Check-in', 'Check-out', 'Cancelada']
const ESTADOS_ACTIVOS = ['Pendiente', 'Confirmada', 'Check-in']

const estilosEstado = {
  Pendiente: 'bg-amber-100 text-amber-700 ring-amber-200',
  Confirmada: 'bg-sky-100 text-sky-700 ring-sky-200',
  'Check-in': 'bg-violet-100 text-violet-700 ring-violet-200',
  'Check-out': 'bg-slate-100 text-slate-600 ring-slate-200',
  Cancelada: 'bg-rose-100 text-rose-700 ring-rose-200',
}

// --- Lookups locales (el listado trae solo IDs) ---
const huespedDe = (id) => huespedes.value.find((h) => h.id_huesped === id)
const habitacionDe = (id) => habitaciones.value.find((h) => h.id_habitacion === id)
const tipoDe = (id) => tipos.value.find((t) => t.id_tipo === id)

const nochesDe = (r) =>
  Math.max(
    Math.round(
      (new Date(r.fecha_salida) - new Date(r.fecha_entrada)) / 86400000,
    ),
    1,
  )

const esHoy = (fecha) => new Date(fecha).toDateString() === new Date().toDateString()

const formatoFecha = (f) =>
  new Date(f).toLocaleDateString('es-BO', { day: '2-digit', month: 'short' })

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

// --- Stats del día ---
const stats = computed(() => ({
  lleganHoy: reservas.value.filter(
    (r) => esHoy(r.fecha_entrada) && ['Pendiente', 'Confirmada'].includes(r.estado),
  ).length,
  enCurso: reservas.value.filter((r) => r.estado === 'Check-in').length,
  salenHoy: reservas.value.filter((r) => esHoy(r.fecha_salida) && r.estado === 'Check-in').length,
  activas: reservas.value.filter((r) => ESTADOS_ACTIVOS.includes(r.estado)).length,
}))

const filtradas = computed(() => {
  let lista = reservas.value
  if (filtroEstado.value !== 'Todas') {
    lista = lista.filter((r) => r.estado === filtroEstado.value)
  }
  const q = busqueda.value.toLowerCase().trim()
  if (q) {
    lista = lista.filter((r) => {
      const h = huespedDe(r.id_huesped)
      const hab = habitacionDe(r.id_habitacion)
      return (
        `${h?.nombre} ${h?.apellido}`.toLowerCase().includes(q) ||
        String(h?.ci || '').includes(q) ||
        String(hab?.numero || '').includes(q) ||
        String(r.id_reserva).includes(q)
      )
    })
  }
  return lista
})

const conteo = (estado) =>
  estado === 'Todas'
    ? reservas.value.length
    : reservas.value.filter((r) => r.estado === estado).length

// --- Carga ---
async function cargar() {
  cargando.value = true
  try {
    const [resR, resH, resT, resHu] = await Promise.all([
      api.get('/reserva/'),
      api.get('/habitacion/'),
      api.get('/tipo-habitacion/'),
      api.get('/huesped/'),
    ])
    reservas.value = resR.data
    habitaciones.value = resH.data
    tipos.value = resT.data
    huespedes.value = resHu.data
  } catch {
    toast.show('Error al cargar las reservas', 'error')
  } finally {
    cargando.value = false
  }
}

// --- Acciones ---
async function accion(reserva, endpoint, mensaje) {
  procesando.value = true
  try {
    await api.patch(`/reserva/${reserva.id_reserva}/${endpoint}`)
    toast.show(mensaje)
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error en la operación', 'error')
  } finally {
    procesando.value = false
  }
}

const confirmar = (r) => accion(r, 'check-in', `Check-in registrado: habitación ${habitacionDe(r.id_habitacion)?.numero} ocupada`)
// check-in usa el mismo endpoint; confirmar explícito:
async function confirmarReserva(r) {
  procesando.value = true
  try {
    await api.put(`/reserva/${r.id_reserva}`, { estado: 'Confirmada' })
    toast.show(`Reserva #${r.id_reserva} confirmada`)
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al confirmar', 'error')
  } finally {
    procesando.value = false
  }
}

async function cancelar() {
  await accion(aCancelar.value, 'cancelar', `Reserva #${aCancelar.value.id_reserva} cancelada`)
  aCancelar.value = null
}

function reservaEditada() {
  editando.value = null
  cargar()
}

onMounted(cargar)
</script>

<template>
  <div>
    <!-- Stats del día -->
    <div class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Llegan hoy</p>
            <p class="mt-1 text-3xl font-black text-sky-600">{{ stats.lleganHoy }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-2xl">🛬</div>
        </div>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">En curso</p>
            <p class="mt-1 text-3xl font-black text-violet-600">{{ stats.enCurso }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-2xl">🔑</div>
        </div>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Salen hoy</p>
            <p class="mt-1 text-3xl font-black text-amber-600">{{ stats.salenHoy }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-2xl">🛫</div>
        </div>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Reservas activas</p>
            <p class="mt-1 text-3xl font-black text-emerald-600">{{ stats.activas }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-2xl">📅</div>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="mb-5 flex flex-wrap items-center gap-2 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <button
        v-for="e in ['Todas', ...ESTADOS]"
        :key="e"
        @click="filtroEstado = e"
        class="rounded-full px-4 py-1.5 text-xs font-semibold transition"
        :class="filtroEstado === e
          ? 'bg-slate-900 text-white'
          : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
      >
        {{ e }} ({{ conteo(e) }})
      </button>

      <div class="ml-auto flex items-center gap-2">
        <div class="relative">
          <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
          <input
            v-model="busqueda"
            placeholder="Buscar huésped, CI, habitación..."
            class="w-64 rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
          />
        </div>
        <button
          @click="modalCrear = true"
          class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
        >
          <span class="text-lg leading-none">＋</span> Nueva Reserva
        </button>
      </div>
    </div>

    <!-- Tabla -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="overflow-x-auto p-2">
        <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando reservas...</div>

        <table v-else class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs uppercase tracking-wide text-slate-400">
              <th class="px-4 py-3">Reserva</th>
              <th class="px-4 py-3">Huésped</th>
              <th class="px-4 py-3">Estadía</th>
              <th class="px-4 py-3">Personas</th>
              <th class="px-4 py-3">Estado</th>
              <th class="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in filtradas"
              :key="r.id_reserva"
              class="group border-t border-slate-50 transition hover:bg-slate-50/80"
            >
              <td class="px-4 py-3.5">
                <p class="font-bold text-slate-800">#{{ r.id_reserva }}</p>
                <p class="text-xs text-slate-400">{{ habitacionDe(r.id_habitacion)?.numero || '—' }}</p>
              </td>

              <td class="px-4 py-3.5">
                <p class="font-semibold text-slate-800">
                  {{ huespedDe(r.id_huesped)?.nombre }} {{ huespedDe(r.id_huesped)?.apellido }}
                </p>
                <p class="font-mono text-xs text-slate-400">CI {{ huespedDe(r.id_huesped)?.ci }}</p>
              </td>

              <td class="px-4 py-3.5">
                <div class="flex items-center gap-1.5">
                  <span class="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                    {{ formatoFecha(r.fecha_entrada) }}
                  </span>
                  <span class="text-slate-300">→</span>
                  <span class="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                    {{ formatoFecha(r.fecha_salida) }}
                  </span>
                  <span class="ml-1 text-xs text-slate-400">{{ nochesDe(r) }}n</span>
                </div>
                <p v-if="esHoy(r.fecha_entrada) && ['Pendiente','Confirmada'].includes(r.estado)"
                   class="mt-1 text-xs font-bold text-sky-600 animate-pulse">🛬 ¡Llega hoy!</p>
                <p v-if="esHoy(r.fecha_salida) && r.estado === 'Check-in'"
                   class="mt-1 text-xs font-bold text-amber-600 animate-pulse">🛫 Sale hoy</p>
              </td>

              <td class="px-4 py-3.5 text-slate-600">👤 {{ r.cantidad_personas }}</td>

              <td class="px-4 py-3.5">
                <span
                  class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1"
                  :class="estilosEstado[r.estado]"
                >
                  {{ r.estado }}
                </span>
              </td>

              <td class="px-4 py-3.5">
                <div class="flex justify-end gap-1">
                  <!-- Confirmar -->
                  <button
                    v-if="r.estado === 'Pendiente'"
                    @click="confirmarReserva(r)"
                    :disabled="procesando"
                    title="Confirmar"
                    class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-emerald-600 transition hover:bg-emerald-50"
                  >
                    ✅ Confirmar
                  </button>
                  <!-- Check-in -->
                  <button
                    v-if="['Pendiente', 'Confirmada'].includes(r.estado)"
                    @click="confirmar(r)"
                    :disabled="procesando"
                    title="Registrar check-in"
                    class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-violet-600 transition hover:bg-violet-50"
                  >
                    🔑 Check-in
                  </button>
                  <!-- Check-out -->
                  <button
                    v-if="r.estado === 'Check-in'"
                    @click="accion(r, 'check-out', `Check-out completado. Habitación a limpieza`)"
                    :disabled="procesando"
                    title="Registrar check-out"
                    class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-sky-600 transition hover:bg-sky-50"
                  >
                    🚪 Check-out
                  </button>
                  <!-- Cancelar -->
                  <button
                    v-if="['Pendiente', 'Confirmada', 'Check-in'].includes(r.estado)"
                    @click="aCancelar = r"
                    title="Cancelar reserva"
                    class="rounded-lg px-2 py-1.5 text-xs transition hover:bg-rose-50"
                  >
                    🚫
                  </button>
                  <!-- Editar -->
                  <button
                    v-if="['Pendiente', 'Confirmada'].includes(r.estado)"
                    @click="editando = r"
                    title="Editar"
                    class="rounded-lg px-2 py-1.5 text-xs transition hover:bg-slate-100"
                  >
                    ✏️
                  </button>
                  <!-- Detalle -->
                  <button
                    @click="detalleId = r.id_reserva"
                    title="Ver cuenta"
                    class="rounded-lg px-2 py-1.5 text-xs transition hover:bg-slate-100"
                  >
                    📄
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="!filtradas.length">
              <td colspan="6" class="px-4 py-12 text-center text-slate-400">
                📅 No hay reservas con esos filtros
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal crear/editar -->
    <ReservaFormModal
      :abierta="modalCrear || !!editando"
      :reserva="editando"
      :habitaciones="habitaciones"
      :tipos="tipos"
      :huespedes="huespedes"
      :reservas="reservas"
      @cerrar="modalCrear = false; editando = null"
      @guardado="reservaEditada"
    />

    <!-- Detalle / cuenta -->
    <DetalleReservaModal
      :abierta="!!detalleId"
      :id-reserva="detalleId"
      @cerrar="detalleId = null"
    />

    <!-- Confirmar cancelación -->
    <ConfirmDialog
      :abierta="!!aCancelar"
      :cargando="procesando"
      :titulo="`¿Cancelar reserva #${aCancelar?.id_reserva}?`"
      mensaje="Si el huésped ya hizo check-in, la habitación quedará liberada para limpieza."
      textoConfirmar="Sí, cancelar"
      @cancelar="aCancelar = null"
      @confirmar="cancelar"
    />
  </div>
</template>