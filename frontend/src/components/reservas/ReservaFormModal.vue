<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'

const props = defineProps({
  abierta: Boolean,
  reserva: Object,        // null = crear
  habitaciones: Array,
  tipos: Array,
  huespedes: Array,
  reservas: Array,        // para calcular disponibilidad local
})
const emit = defineEmits(['cerrar', 'guardado'])

const toast = useToastStore()

const HORA_ENTRADA = '14:00'
const HORA_SALIDA = '12:00'

const guardando = ref(false)

// --- Form ---
const hoy = new Date().toISOString().slice(0, 10)
const form = ref({
  busquedaHuesped: '',
  huespedSeleccionado: null,
  fecha_entrada: '',
  fecha_salida: '',
  id_habitacion: '',
  cantidad_personas: 1,
  estado: 'Confirmada',
  observaciones: '',
})

// Al abrir: reset o precargar según crear/editar
watch(
  () => props.abierta,
  (abierta) => {
    if (!abierta) return
    if (props.reserva) {
      const h = props.huespedes.find((hu) => hu.id_huesped === props.reserva.id_huesped)
      form.value = {
        busquedaHuesped: '',
        huespedSeleccionado: h || null,
        fecha_entrada: props.reserva.fecha_entrada.slice(0, 10),
        fecha_salida: props.reserva.fecha_salida.slice(0, 10),
        id_habitacion: props.reserva.id_habitacion,
        cantidad_personas: props.reserva.cantidad_personas,
        estado: props.reserva.estado,
        observaciones: props.reserva.observaciones || '',
      }
    } else {
      form.value = {
        busquedaHuesped: '',
        huespedSeleccionado: null,
        fecha_entrada: '',
        fecha_salida: '',
        id_habitacion: '',
        cantidad_personas: 1,
        estado: 'Confirmada',
        observaciones: '',
      }
    }
  },
)

// --- Búsqueda de huésped (local, instantánea) ---
const resultadosHuesped = computed(() => {
  const q = form.value.busquedaHuesped.toLowerCase().trim()
  if (!q || form.value.huespedSeleccionado) return []
  return props.huespedes
    .filter(
      (h) =>
        `${h.nombre} ${h.apellido}`.toLowerCase().includes(q) ||
        h.ci.includes(q),
    )
    .slice(0, 6)
})

function seleccionarHuesped(h) {
  form.value.huespedSeleccionado = h
  form.value.busquedaHuesped = ''
}

// --- Fechas y cálculos en vivo ---
const noches = computed(() => {
  if (!form.value.fecha_entrada || !form.value.fecha_salida) return 0
  const n = Math.round(
    (new Date(form.value.fecha_salida) - new Date(form.value.fecha_entrada)) / 86400000,
  )
  return n
})

const fechasValidas = computed(() => noches.value >= 1)

// 🎯 Disponibilidad: replica la lógica del backend
const habitacionesDisponibles = computed(() => {
  if (!fechasValidas.value) return []
  const entrada = `${form.value.fecha_entrada}T${HORA_ENTRADA}:00`
  const salida = `${form.value.fecha_salida}T${HORA_SALIDA}:00`

  return props.habitaciones.filter((h) => {
    if (h.estado === 'Mantenimiento') return false
    const cruza = props.reservas.some(
      (r) =>
        r.id_habitacion === h.id_habitacion &&
        ['Pendiente', 'Confirmada', 'Check-in'].includes(r.estado) &&
        r.id_reserva !== props.reserva?.id_reserva &&
        new Date(r.fecha_entrada) < new Date(salida) &&
        new Date(r.fecha_salida) > new Date(entrada),
    )
    return !cruza
  })
})

// Si las fechas cambian y la habitación elegida ya no está disponible → deseleccionar
watch(habitacionesDisponibles, (disponibles) => {
  if (
    form.value.id_habitacion &&
    !disponibles.some((h) => h.id_habitacion === form.value.id_habitacion)
  ) {
    form.value.id_habitacion = ''
  }
})

const habitacionElegida = computed(() =>
  props.habitaciones.find((h) => h.id_habitacion === form.value.id_habitacion),
)
const tipoElegido = computed(() =>
  habitacionElegida.value
    ? props.tipos.find((t) => t.id_tipo === habitacionElegida.value.id_tipo)
    : null,
)

const capacidadMax = computed(() => tipoElegido.value?.capacidad || 0)

// Si cambia de habitación y hay más personas que capacidad → ajustar
watch(capacidadMax, (cap) => {
  if (cap && form.value.cantidad_personas > cap) {
    form.value.cantidad_personas = cap
  }
})

const totalEstimado = computed(() =>
  tipoElegido.value ? Number(tipoElegido.value.precio_noche) * noches.value : 0,
)

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

const puedeGuardar = computed(
  () =>
    form.value.huespedSeleccionado &&
    fechasValidas.value &&
    form.value.id_habitacion &&
    form.value.cantidad_personas >= 1 &&
    form.value.cantidad_personas <= capacidadMax.value,
)

// --- Guardar ---
async function guardar() {
  guardando.value = true
  try {
    const datos = {
      id_huesped: form.value.huespedSeleccionado.id_huesped,
      id_habitacion: form.value.id_habitacion,
      fecha_entrada: `${form.value.fecha_entrada}T${HORA_ENTRADA}:00`,
      fecha_salida: `${form.value.fecha_salida}T${HORA_SALIDA}:00`,
      cantidad_personas: form.value.cantidad_personas,
      estado: form.value.estado,
      observaciones: form.value.observaciones || null,
    }

    if (props.reserva) {
      await api.put(`/reserva/${props.reserva.id_reserva}`, datos)
      toast.show(`Reserva #${props.reserva.id_reserva} actualizada`)
    } else {
      const { data } = await api.post('/reserva/', datos)
      toast.show(`Reserva #${data.id_reserva} creada 🎉`)
    }
    emit('guardado')
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al guardar la reserva', 'error')
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :abierta="abierta"
    :titulo="reserva ? `Editar Reserva #${reserva.id_reserva}` : 'Nueva Reserva'"
    @cerrar="emit('cerrar')"
  >
    <form @submit.prevent="guardar" class="space-y-5">
      <!-- 1. Huésped -->
      <div>
        <p class="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">1 · Huésped</p>

        <!-- Seleccionado -->
        <div
          v-if="form.huespedSeleccionado"
          class="flex items-center gap-3 rounded-xl bg-emerald-50 p-3 ring-1 ring-emerald-200"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 font-bold text-white">
            {{ form.huespedSeleccionado.nombre[0] }}{{ form.huespedSeleccionado.apellido[0] }}
          </div>
          <div class="flex-1">
            <p class="font-semibold text-slate-800">
              {{ form.huespedSeleccionado.nombre }} {{ form.huespedSeleccionado.apellido }}
            </p>
            <p class="font-mono text-xs text-slate-500">CI {{ form.huespedSeleccionado.ci }}</p>
          </div>
          <button
            v-if="!reserva"
            type="button"
            @click="form.huespedSeleccionado = null"
            class="rounded-lg px-2 py-1 text-xs text-slate-400 transition hover:bg-white hover:text-slate-600"
          >
            cambiar
          </button>
        </div>

        <!-- Buscador -->
        <div v-else class="relative">
          <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
          <input
            v-model="form.busquedaHuesped"
            placeholder="Buscar por nombre o CI..."
            class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
          />
          <div
            v-if="resultadosHuesped.length"
            class="absolute z-10 mt-1 w-full overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-slate-200"
          >
            <button
              v-for="h in resultadosHuesped"
              :key="h.id_huesped"
              type="button"
              @click="seleccionarHuesped(h)"
              class="flex w-full items-center gap-3 px-4 py-2.5 text-left transition hover:bg-slate-50"
            >
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-600">
                {{ h.nombre[0] }}{{ h.apellido[0] }}
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-800">{{ h.nombre }} {{ h.apellido }}</p>
                <p class="font-mono text-xs text-slate-400">CI {{ h.ci }}</p>
              </div>
            </button>
          </div>
          <p v-else-if="form.busquedaHuesped" class="mt-1.5 text-xs text-amber-600">
            Sin resultados — regístralo primero en el módulo Huéspedes
          </p>
        </div>
      </div>

      <!-- 2. Fechas -->
      <div>
        <p class="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">2 · Estadía</p>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Entrada (check-in {{ HORA_ENTRADA }})</label>
            <input
              v-model="form.fecha_entrada"
              type="date"
              :min="reserva ? undefined : hoy"
              required
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Salida (check-out {{ HORA_SALIDA }})</label>
            <input
              v-model="form.fecha_salida"
              type="date"
              :min="form.fecha_entrada || hoy"
              required
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
          </div>
        </div>
        <div v-if="form.fecha_entrada && form.fecha_salida" class="mt-2">
          <p v-if="fechasValidas" class="text-sm font-semibold text-emerald-600">
            🌙 {{ noches }} noche{{ noches > 1 ? 's' : '' }}
          </p>
          <p v-else class="text-sm font-semibold text-rose-600">
            ⚠️ La salida debe ser posterior a la entrada
          </p>
        </div>
      </div>

      <!-- 3. Habitación -->
      <div>
        <p class="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">3 · Habitación</p>

        <p v-if="!fechasValidas" class="rounded-xl bg-slate-50 p-4 text-center text-sm text-slate-400">
          Elige las fechas para ver disponibilidad
        </p>
        <p v-else-if="!habitacionesDisponibles.length" class="rounded-xl bg-amber-50 p-4 text-center text-sm text-amber-600">
          😕 No hay habitaciones disponibles en esas fechas
        </p>

        <div v-else class="grid max-h-44 grid-cols-2 gap-2 overflow-y-auto rounded-xl p-1 sm:grid-cols-3">
          <button
            v-for="h in habitacionesDisponibles"
            :key="h.id_habitacion"
            type="button"
            @click="form.id_habitacion = h.id_habitacion"
            class="rounded-xl border-2 p-3 text-left transition-all"
            :class="form.id_habitacion === h.id_habitacion
              ? 'border-slate-900 bg-slate-900 text-white shadow-lg'
              : 'border-slate-100 bg-white hover:border-slate-300'"
          >
            <p class="text-lg font-black">{{ h.numero }}</p>
            <p class="text-xs" :class="form.id_habitacion === h.id_habitacion ? 'text-slate-300' : 'text-slate-500'">
              {{ tipos.find((t) => t.id_tipo === h.id_tipo)?.nombre }}
            </p>
            <p class="text-xs font-bold" :class="form.id_habitacion === h.id_habitacion ? 'text-amber-300' : 'text-emerald-600'">
              {{ formatoPrecio(tipos.find((t) => t.id_tipo === h.id_tipo)?.precio_noche) }}
            </p>
          </button>
        </div>

        <div v-if="habitacionElegida" class="mt-3 flex items-center gap-4">
          <div class="flex-1">
            <label class="mb-1 block text-xs font-semibold text-slate-500">
              Personas (máx. {{ capacidadMax }})
            </label>
            <input
              v-model.number="form.cantidad_personas"
              type="number"
              min="1"
              :max="capacidadMax"
              required
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
          </div>
          <div class="flex-1">
            <label class="mb-1 block text-xs font-semibold text-slate-500">Estado</label>
            <select
              v-model="form.estado"
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400"
            >
              <option>Confirmada</option>
              <option>Pendiente</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 4. Resumen -->
      <div v-if="puedeGuardar" class="rounded-xl bg-slate-900 p-4 text-white">
        <p class="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">Resumen</p>
        <div class="space-y-1 text-sm">
          <div class="flex justify-between text-slate-300">
            <span>Habitación {{ habitacionElegida.numero }} ({{ tipoElegido.nombre }})</span>
            <span>{{ formatoPrecio(tipoElegido.precio_noche) }} × {{ noches }}n</span>
          </div>
          <div class="flex justify-between border-t border-slate-700 pt-2 text-base font-bold">
            <span>Total estimado</span>
            <span class="text-amber-400">{{ formatoPrecio(totalEstimado) }}</span>
          </div>
          <p class="text-[11px] text-slate-500">* Los servicios adicionales se suman durante la estadía</p>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-semibold text-slate-500">Observaciones</label>
        <textarea
          v-model="form.observaciones"
          rows="2"
          placeholder="Ej: llega tarde, pedirá cuna..."
          class="w-full resize-none rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
        />
      </div>

      <div class="flex justify-end gap-3 pt-1">
        <button
          type="button"
          @click="emit('cerrar')"
          class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100"
        >
          Cancelar
        </button>
        <button
          type="submit"
          :disabled="!puedeGuardar || guardando"
          class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {{ guardando ? 'Guardando...' : reserva ? 'Guardar Cambios' : 'Crear Reserva' }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>