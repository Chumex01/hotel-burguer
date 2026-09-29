<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToastStore()

const ESTADOS_CONSUMO = ['Pendiente', 'Confirmada', 'Check-in']

const reservas = ref([])
const huespedes = ref([])
const habitaciones = ref([])
const servicios = ref([])
const cargando = ref(true)

const reservaSel = ref(null)
const cuenta = ref(null)
const cargandoCuenta = ref(false)

const modalAgregar = ref(false)
const modalEditar = ref(false)
const aAnular = ref(null)
const procesando = ref(false)

const HORA_ENTRADA = '14:00'
const HORA_SALIDA = '12:00'

const formAgregar = ref({ id_servicio: '', cantidad: 1, observacion: '' })
const formEditar = ref({ id_reserva_servicio: null, cantidad: 1, observacion: '' })

// --- Lookups ---
const huespedDe = (id) => huespedes.value.find((h) => h.id_huesped === id)
const habitacionDe = (id) => habitaciones.value.find((h) => h.id_habitacion === id)

const estilosEstado = {
  Pendiente: 'bg-amber-100 text-amber-700',
  Confirmada: 'bg-sky-100 text-sky-700',
  'Check-in': 'bg-violet-100 text-violet-700',
}

const reservasActivas = computed(() =>
  reservas.value.filter((r) => ESTADOS_CONSUMO.includes(r.estado)),
)

const servicioDe = (id) => servicios.value.find((s) => s.id_servicio === id)

const emojis = {
  desayuno: '🥐', almuerzo: '🍛', cena: '🍝', piscina: '🏊', sauna: '🧖',
  recreacion: '🎲', recreación: '🎲', lavanderia: '🧺', lavandería: '🧺',
  traslado: '🚐', masaje: '💆', gimnasio: '🏋️', bar: '🍸',
  habitacion: '🛎️', 'habitación': '🛎️', minibar: '🥤',
}
const emojiDe = (nombre) => {
  const q = (nombre || '').toLowerCase()
  for (const k in emojis) if (q.includes(k)) return emojis[k]
  return '🍽️'
}

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

// Servicios que se pueden agregar: solo activos
const serviciosActivos = computed(() => servicios.value.filter((s) => s.estado === 'Activo'))

// Preview en vivo del modal de agregar
const servicioElegido = computed(() => servicioDe(formAgregar.value.id_servicio))
const subtotalPreview = computed(() =>
  servicioElegido.value
    ? Number(servicioElegido.value.precio) * formAgregar.value.cantidad
    : 0,
)

const editable = computed(() => reservaSel.value && ESTADOS_CONSUMO.includes(reservaSel.value.estado))

// --- Carga ---
async function cargar() {
  cargando.value = true
  try {
    const [resR, resH, resHab, resS] = await Promise.all([
      api.get('/reserva/'),
      api.get('/huesped/'),
      api.get('/habitacion/'),
      api.get('/servicio/'),
    ])
    reservas.value = resR.data
    huespedes.value = resH.data
    habitaciones.value = resHab.data
    servicios.value = resS.data
  } catch {
    toast.show('Error al cargar los datos', 'error')
  } finally {
    cargando.value = false
  }
}

async function seleccionarReserva(id) {
  reservaSel.value = reservas.value.find((r) => r.id_reserva === Number(id)) || null
  cuenta.value = null
  if (reservaSel.value) await cargarCuenta()
}

async function cargarCuenta() {
  cargandoCuenta.value = true
  try {
    const { data } = await api.get('/reserva-servicio/cuenta', {
      params: { id_reserva: reservaSel.value.id_reserva },
    })
    cuenta.value = data
  } catch {
    toast.show('Error al cargar la cuenta', 'error')
  } finally {
    cargandoCuenta.value = false
  }
}

// --- Acciones ---
function abrirAgregar() {
  formAgregar.value = { id_servicio: '', cantidad: 1, observacion: '' }
  modalAgregar.value = true
}

async function agregar() {
  procesando.value = true
  try {
    const { data } = await api.post('/reserva-servicio/', {
      id_reserva: reservaSel.value.id_reserva,
      id_servicio: formAgregar.value.id_servicio,
      cantidad: formAgregar.value.cantidad,
      observacion: formAgregar.value.observacion || null,
    })
    toast.show(`${servicioDe(data.id_servicio)?.nombre} agregado a la cuenta (precio congelado: ${formatoPrecio(data.precio_unitario)})`)
    modalAgregar.value = false
    await cargarCuenta()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al agregar el consumo', 'error')
  } finally {
    procesando.value = false
  }
}

function abrirEditar(linea) {
  formEditar.value = {
    id_reserva_servicio: linea.id_reserva_servicio,
    cantidad: linea.cantidad,
    observacion: linea.observacion || '',
  }
  modalEditar.value = true
}

async function guardarEdicion() {
  procesando.value = true
  try {
    await api.put(`/reserva-servicio/${formEditar.value.id_reserva_servicio}`, {
      cantidad: formEditar.value.cantidad,
      observacion: formEditar.value.observacion || null,
    })
    toast.show('Consumo actualizado')
    modalEditar.value = false
    await cargarCuenta()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al actualizar', 'error')
  } finally {
    procesando.value = false
  }
}

async function anular() {
  procesando.value = true
  try {
    await api.delete(`/reserva-servicio/${aAnular.value.id_reserva_servicio}`)
    toast.show('Consumo anulado')
    aAnular.value = null
    await cargarCuenta()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al anular', 'error')
    aAnular.value = null
  } finally {
    procesando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <!-- Selector de reserva -->
    <div class="mb-5 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
        Selecciona una reserva activa
      </label>
      <select
        @change="seleccionarReserva($event.target.value)"
        class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"
      >
        <option value="" :selected="!reservaSel">— Elegir reserva —</option>
        <option v-for="r in reservasActivas" :key="r.id_reserva" :value="r.id_reserva">
          #{{ r.id_reserva }} · {{ huespedDe(r.id_huesped)?.nombre }} {{ huespedDe(r.id_huesped)?.apellido }}
          · Hab {{ habitacionDe(r.id_habitacion)?.numero }} · {{ r.estado }}
        </option>
      </select>
      <p v-if="!reservasActivas.length && !cargando" class="mt-2 text-xs text-amber-600">
        ⚠️ No hay reservas activas (Pendiente/Confirmada/Check-in). Crea una en el módulo Reservas.
      </p>
    </div>

    <!-- Ticket -->
    <div v-if="reservaSel" class="mx-auto max-w-2xl">
      <!-- Info de la reserva -->
      <div class="rounded-t-2xl bg-slate-900 p-5 text-white">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-lg font-black">Reserva #{{ reservaSel.id_reserva }}</p>
            <p class="text-sm text-slate-300">
              {{ huespedDe(reservaSel.id_huesped)?.nombre }} {{ huespedDe(reservaSel.id_huesped)?.apellido }}
              · Hab {{ habitacionDe(reservaSel.id_habitacion)?.numero }}
              · 👤 {{ reservaSel.cantidad_personas }}
            </p>
          </div>
          <span
            class="rounded-full px-3 py-1 text-xs font-bold"
            :class="estilosEstado[reservaSel.estado]"
          >
            {{ reservaSel.estado }}
          </span>
        </div>
      </div>

      <!-- Líneas -->
      <div class="rounded-b-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <div v-if="cargandoCuenta" class="p-10 text-center text-slate-400">Cargando cuenta...</div>

        <template v-else>
          <div class="divide-y divide-slate-50">
            <div
              v-for="l in cuenta?.detalle || []"
              :key="l.id_reserva_servicio"
              class="group flex items-center gap-3 px-5 py-3.5"
            >
              <span class="text-2xl">{{ emojiDe(servicioDe(l.id_servicio)?.nombre) }}</span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-semibold text-slate-800">
                  {{ servicioDe(l.id_servicio)?.nombre || `Servicio #${l.id_servicio}` }}
                  <span class="font-normal text-slate-400">× {{ l.cantidad }}</span>
                </p>
                <p class="text-xs text-slate-400">
                  {{ formatoPrecio(l.precio_unitario) }} c/u
                  <span v-if="l.observacion"> · 📝 {{ l.observacion }}</span>
                </p>
              </div>
              <p class="font-bold text-slate-800">
                {{ formatoPrecio(Number(l.precio_unitario) * l.cantidad) }}
              </p>
              <div
                v-if="editable"
                class="flex gap-1 opacity-0 transition group-hover:opacity-100"
              >
                <button @click="abrirEditar(l)" title="Editar cantidad" class="rounded-lg p-1.5 transition hover:bg-slate-100">✏️</button>
                <button @click="aAnular = l" title="Anular" class="rounded-lg p-1.5 transition hover:bg-rose-50">🗑️</button>
              </div>
            </div>

            <div v-if="cuenta && !cuenta.detalle.length" class="p-10 text-center text-slate-400">
              🧾 Sin consumos aún — agrega el primero
            </div>
          </div>

          <!-- Total -->
          <div class="flex items-center justify-between border-t-2 border-dashed border-slate-200 px-5 py-4">
            <div>
              <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total servicios</p>
              <p class="text-2xl font-black text-slate-900">
                {{ formatoPrecio(cuenta?.total_servicios) }}
              </p>
            </div>
            <button
              v-if="editable"
              @click="abrirAgregar"
              class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
            >
              <span class="text-lg leading-none">＋</span> Agregar consumo
            </button>
            <span v-else class="rounded-full bg-slate-100 px-4 py-1.5 text-xs font-semibold text-slate-500">
              🔒 Cuenta cerrada ({{ reservaSel.estado }})
            </span>
          </div>
        </template>
      </div>

      <p class="mt-3 text-center text-xs text-slate-400">
        💡 Para el total con pagos incluidos, usa el botón 📄 en el módulo Reservas
      </p>
    </div>

    <div v-else class="rounded-2xl border-2 border-dashed border-slate-200 p-16 text-center text-slate-400">
      🧾 Selecciona una reserva arriba para ver y gestionar su cuenta de servicios
    </div>

    <!-- Modal agregar consumo -->
    <BaseModal :abierta="modalAgregar" titulo="Agregar Consumo" @cerrar="modalAgregar = false">
      <form @submit.prevent="agregar" class="space-y-4">
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Servicio *</label>
          <select
            v-model="formAgregar.id_servicio"
            required
            class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
          >
            <option value="" disabled>Seleccionar...</option>
            <option v-for="s in serviciosActivos" :key="s.id_servicio" :value="s.id_servicio">
              {{ emojiDe(s.nombre) }} {{ s.nombre }} — {{ formatoPrecio(s.precio) }}
            </option>
          </select>
          <p v-if="!serviciosActivos.length" class="mt-1 text-xs text-amber-600">
            ⚠️ No hay servicios activos en el catálogo
          </p>
        </div>

        <!-- Stepper de cantidad -->
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Cantidad *</label>
          <div class="flex items-center gap-3">
            <button
              type="button"
              @click="formAgregar.cantidad = Math.max(1, formAgregar.cantidad - 1)"
              class="h-10 w-10 rounded-xl bg-slate-100 text-lg font-bold text-slate-600 transition hover:bg-slate-200 active:scale-95"
            >
              −
            </button>
            <input
              v-model.number="formAgregar.cantidad"
              type="number"
              min="1"
              required
              class="w-20 rounded-xl border border-slate-200 py-2 text-center text-sm font-bold outline-none focus:border-slate-400"
            />
            <button
              type="button"
              @click="formAgregar.cantidad++"
              class="h-10 w-10 rounded-xl bg-slate-100 text-lg font-bold text-slate-600 transition hover:bg-slate-200 active:scale-95"
            >
              ＋
            </button>
            <div v-if="servicioElegido" class="ml-auto text-right">
              <p class="text-xs text-slate-400">
                Precio vigente: {{ formatoPrecio(servicioElegido.precio) }}
              </p>
              <p class="text-lg font-black text-emerald-600">{{ formatoPrecio(subtotalPreview) }}</p>
            </div>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Observación</label>
          <input v-model="formAgregar.observacion" placeholder="Ej: para la habitación 204" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>

        <div class="rounded-xl bg-amber-50 p-3 text-xs text-amber-700 ring-1 ring-amber-200">
          🔒 Al confirmar, se registra el precio vigente de <strong>hoy</strong>. Si mañana el precio cambia, este consumo mantiene el suyo.
        </div>

        <div class="flex justify-end gap-3 pt-1">
          <button type="button" @click="modalAgregar = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button
            type="submit"
            :disabled="procesando || !servicioElegido"
            class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-40"
          >
            {{ procesando ? 'Agregando...' : 'Agregar a la cuenta' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <!-- Modal editar consumo (solo cantidad/observación) -->
    <BaseModal :abierta="modalEditar" titulo="Editar Consumo" @cerrar="modalEditar = false">
      <form @submit.prevent="guardarEdicion" class="space-y-4">
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Cantidad</label>
          <div class="flex items-center gap-3">
            <button type="button" @click="formEditar.cantidad = Math.max(1, formEditar.cantidad - 1)" class="h-10 w-10 rounded-xl bg-slate-100 text-lg font-bold text-slate-600 transition hover:bg-slate-200">−</button>
            <input v-model.number="formEditar.cantidad" type="number" min="1" required class="w-20 rounded-xl border border-slate-200 py-2 text-center text-sm font-bold outline-none focus:border-slate-400" />
            <button type="button" @click="formEditar.cantidad++" class="h-10 w-10 rounded-xl bg-slate-100 text-lg font-bold text-slate-600 transition hover:bg-slate-200">＋</button>
          </div>
          <p class="mt-1 text-[11px] text-slate-400">El precio unitario congelado no se modifica</p>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Observación</label>
          <input v-model="formEditar.observacion" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div class="flex justify-end gap-3 pt-1">
          <button type="button" @click="modalEditar = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button type="submit" :disabled="procesando" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60">
            {{ procesando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <ConfirmDialog
      :abierta="!!aAnular"
      :cargando="procesando"
      :titulo="`¿Anular ${servicioDe(aAnular?.id_servicio)?.nombre || 'consumo'}?`"
      mensaje="La línea saldrá de la cuenta y el total se recalculará."
      textoConfirmar="Anular"
      @cancelar="aAnular = null"
      @confirmar="anular"
    />
  </div>
</template>