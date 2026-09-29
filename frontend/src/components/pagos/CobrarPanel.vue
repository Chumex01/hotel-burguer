<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import AnularPagoModal from './AnularPagoModal.vue'

const toast = useToastStore()

const reservas = ref([])
const huespedes = ref([])
const habitaciones = ref([])
const cargando = ref(true)

const reservaSel = ref(null)
const cuenta = ref(null)
const pagos = ref([])
const cargandoCuenta = ref(false)

const guardando = ref(false)
const aAnular = ref(null)
const aReembolsar = ref(null)
const procesando = ref(false)

const form = ref({ monto: '', metodo_pago: 'Efectivo', observacion: '' })

const METODOS = [
  { id: 'Efectivo', emoji: '💵' },
  { id: 'Transferencia', emoji: '🏦' },
  { id: 'Tarjeta', emoji: '💳' },
  { id: 'QR', emoji: '📱' },
]
const emojiMetodo = (m) => METODOS.find((x) => x.id === m)?.emoji || '💰'

const estilosPago = {
  Pagado: 'bg-emerald-100 text-emerald-700',
  Pendiente: 'bg-amber-100 text-amber-700',
  Anulado: 'bg-rose-100 text-rose-500',
  Reembolsado: 'bg-sky-100 text-sky-700',
}

// Reservas que admiten cobros (el backend bloquea las Canceladas)
const reservasPagables = computed(() =>
  reservas.value.filter((r) => r.estado !== 'Cancelada'),
)

const huespedDe = (id) => huespedes.value.find((h) => h.id_huesped === id)
const habitacionDe = (id) => habitaciones.value.find((h) => h.id_habitacion === id)

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`
const formatoFechaHora = (f) =>
  new Date(f).toLocaleString('es-BO', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })

const saldo = computed(() => (cuenta.value ? Number(cuenta.value.saldo) : 0))
const cuentaSaldada = computed(() => saldo.value <= 0)

const montoValido = computed(() => {
  const m = Number(form.value.monto)
  return m > 0 && m <= saldo.value
})

const puedeRegistrar = computed(
  () => reservaSel.value && !cuentaSaldada.value && montoValido.value,
)

// --- Carga ---
async function cargar() {
  cargando.value = true
  try {
    const [resR, resH, resHab] = await Promise.all([
      api.get('/reserva/'),
      api.get('/huesped/'),
      api.get('/habitacion/'),
    ])
    reservas.value = resR.data
    huespedes.value = resH.data
    habitaciones.value = resHab.data
  } catch {
    toast.show('Error al cargar los datos', 'error')
  } finally {
    cargando.value = false
  }
}

async function seleccionarReserva(id) {
  reservaSel.value = reservas.value.find((r) => r.id_reserva === Number(id)) || null
  cuenta.value = null
  pagos.value = []
  form.value = { monto: '', metodo_pago: 'Efectivo', observacion: '' }
  if (reservaSel.value) await recargar()
}

async function recargar() {
  cargandoCuenta.value = true
  try {
    const [resC, resP] = await Promise.all([
      api.get('/pago/cuenta-completa', { params: { id_reserva: reservaSel.value.id_reserva } }),
      api.get('/pago/', { params: { id_reserva: reservaSel.value.id_reserva } }),
    ])
    cuenta.value = resC.data
    pagos.value = resP.data
  } catch {
    toast.show('Error al cargar la cuenta', 'error')
  } finally {
    cargandoCuenta.value = false
  }
}

function pagarTodo() {
  form.value.monto = saldo.value
}

// --- Registrar pago ---
async function registrar() {
  guardando.value = true
  try {
    const { data } = await api.post('/pago/', {
      id_reserva: reservaSel.value.id_reserva,
      monto: Number(form.value.monto),
      metodo_pago: form.value.metodo_pago,
      estado: 'Pagado',
      observacion: form.value.observacion || null,
    })
    toast.show(`${emojiMetodo(data.metodo_pago)} Pago de ${formatoPrecio(data.monto)} registrado`)
    form.value = { monto: '', metodo_pago: form.value.metodo_pago, observacion: '' }
    await recargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al registrar el pago', 'error')
  } finally {
    guardando.value = false
  }
}

// --- Anular / Reembolsar ---
async function anular(observacion) {
  procesando.value = true
  try {
    await api.patch(`/pago/${aAnular.value.id_pago}/anular`, null, {
      params: { observacion },
    })
    toast.show('Pago anulado — queda registrado con su justificación', 'info')
    aAnular.value = null
    await recargar()
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
    toast.show('Pago marcado como reembolsado', 'info')
    aReembolsar.value = null
    await recargar()
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
    <!-- Selector -->
    <div class="mb-5 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
        Selecciona la reserva a cobrar
      </label>
      <select
        @change="seleccionarReserva($event.target.value)"
        class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"
      >
        <option value="" :selected="!reservaSel">— Elegir reserva —</option>
        <option v-for="r in reservasPagables" :key="r.id_reserva" :value="r.id_reserva">
          #{{ r.id_reserva }} · {{ huespedDe(r.id_huesped)?.nombre }} {{ huespedDe(r.id_huesped)?.apellido }}
          · Hab {{ habitacionDe(r.id_habitacion)?.numero }} · {{ r.estado }}
        </option>
      </select>
    </div>

    <div v-if="reservaSel" class="mx-auto max-w-2xl">
      <!-- FACTURA -->
      <div class="overflow-hidden rounded-2xl shadow-sm ring-1 ring-slate-200">
        <!-- Header -->
        <div class="bg-slate-900 p-5 text-white">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-lg font-black">Reserva #{{ reservaSel.id_reserva }}</p>
              <p class="text-sm text-slate-300">
                {{ huespedDe(reservaSel.id_huesped)?.nombre }} {{ huespedDe(reservaSel.id_huesped)?.apellido }}
                · Hab {{ habitacionDe(reservaSel.id_habitacion)?.numero }}
              </p>
            </div>
            <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold">
              {{ cuenta?.estado_reserva || reservaSel.estado }}
            </span>
          </div>
        </div>

        <div v-if="cargandoCuenta" class="p-10 text-center text-slate-400">
          Calculando cuenta...
        </div>

        <div v-else-if="cuenta" class="bg-white">
          <!-- Desglose -->
          <div class="space-y-2 px-5 py-4 text-sm">
            <div class="flex justify-between text-slate-600">
              <span>🏨 Habitación · {{ cuenta.noches }}n × {{ formatoPrecio(cuenta.precio_noche) }}</span>
              <span class="font-semibold">{{ formatoPrecio(cuenta.total_habitacion) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>🍳 Servicios adicionales</span>
              <span class="font-semibold">{{ formatoPrecio(cuenta.total_servicios) }}</span>
            </div>
            <div class="flex justify-between border-t border-dashed border-slate-200 pt-2 text-slate-600">
              <span>💳 Ya pagado</span>
              <span class="font-semibold text-emerald-600">−{{ formatoPrecio(cuenta.total_pagado) }}</span>
            </div>
          </div>

          <!-- SALDO -->
          <div
            class="flex items-center justify-between px-5 py-4"
            :class="cuentaSaldada ? 'bg-emerald-50' : 'bg-rose-50'"
          >
            <div>
              <p class="text-xs font-bold uppercase tracking-wide text-slate-500">
                {{ cuentaSaldada ? 'Cuenta saldada' : 'Saldo pendiente' }}
              </p>
              <p
                class="text-3xl font-black"
                :class="cuentaSaldada ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ formatoPrecio(saldo) }}
              </p>
            </div>
            <span class="text-4xl">{{ cuentaSaldada ? '🎉' : '💸' }}</span>
          </div>
        </div>
      </div>

      <!-- FORM DE PAGO -->
      <div v-if="cuenta" class="mt-5 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <p class="mb-4 text-xs font-bold uppercase tracking-wide text-slate-400">Registrar pago</p>

        <div v-if="cuentaSaldada" class="rounded-xl bg-emerald-50 p-4 text-center text-sm font-semibold text-emerald-700 ring-1 ring-emerald-200">
          ✅ Esta cuenta está saldada. No hay nada por cobrar.
        </div>

        <form v-else @submit.prevent="registrar" class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Monto (máx. {{ formatoPrecio(saldo) }})</label>
            <div class="flex gap-2">
              <input
                v-model="form.monto"
                type="number"
                step="0.01"
                :min="0.01"
                :max="saldo"
                required
                placeholder="0.00"
                class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-lg font-bold outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
              />
              <button
                type="button"
                @click="pagarTodo"
                class="shrink-0 rounded-xl bg-amber-100 px-4 text-sm font-bold text-amber-700 ring-1 ring-amber-200 transition hover:bg-amber-200 active:scale-95"
              >
                Pagar todo
              </button>
            </div>
            <p v-if="form.monto && !montoValido" class="mt-1 text-xs font-semibold text-rose-600">
              ⚠️ El monto no puede exceder el saldo ({{ formatoPrecio(saldo) }})
            </p>
          </div>

          <div>
            <label class="mb-1.5 block text-xs font-semibold text-slate-500">Método de pago</label>
            <div class="grid grid-cols-4 gap-2">
              <button
                v-for="m in METODOS"
                :key="m.id"
                type="button"
                @click="form.metodo_pago = m.id"
                class="rounded-xl border-2 py-2.5 text-center transition-all"
                :class="form.metodo_pago === m.id
                  ? 'border-slate-900 bg-slate-900 text-white shadow-md'
                  : 'border-slate-100 bg-white hover:border-slate-300'"
              >
                <p class="text-xl">{{ m.emoji }}</p>
                <p class="text-[11px] font-semibold" :class="form.metodo_pago === m.id ? 'text-slate-200' : 'text-slate-500'">
                  {{ m.id }}
                </p>
              </button>
            </div>
          </div>

          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Observación</label>
            <input v-model="form.observacion" placeholder="Ej: anticipo, pago parcial..." class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>

          <button
            type="submit"
            :disabled="!puedeRegistrar || guardando"
            class="w-full rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {{ guardando ? 'Registrando...' : `💵 Cobrar ${formatoPrecio(form.monto || 0)}` }}
          </button>
        </form>
      </div>

      <!-- HISTORIAL DE PAGOS DE LA RESERVA -->
      <div v-if="cuenta" class="mt-5 rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <div class="border-b border-slate-100 px-5 py-3">
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">
            Historial de pagos ({{ pagos.length }})
          </p>
        </div>

        <div class="divide-y divide-slate-50">
          <div
            v-for="p in pagos"
            :key="p.id_pago"
            class="group flex items-center gap-3 px-5 py-3"
            :class="{ 'opacity-50': p.estado === 'Anulado' }"
          >
            <span class="text-xl">{{ emojiMetodo(p.metodo_pago) }}</span>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-bold text-slate-800" :class="{ 'line-through': p.estado === 'Anulado' }">
                {{ formatoPrecio(p.monto) }}
                <span class="ml-1 font-normal text-slate-400">· {{ p.metodo_pago }} · #{{ p.id_pago }}</span>
              </p>
              <p class="text-xs text-slate-400">
                {{ formatoFechaHora(p.fecha_pago) }}
                <span v-if="p.estado === 'Anulado' && p.observacion"> · 📝 {{ p.observacion }}</span>
              </p>
            </div>
            <span class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase" :class="estilosPago[p.estado]">
              {{ p.estado }}
            </span>
            <div class="flex gap-1 opacity-0 transition group-hover:opacity-100">
              <button
                v-if="p.estado === 'Pagado'"
                @click="aAnular = p"
                title="Anular"
                class="rounded-lg p-1.5 transition hover:bg-rose-50"
              >🚫</button>
              <button
                v-if="p.estado === 'Pagado'"
                @click="aReembolsar = p"
                title="Reembolsar"
                class="rounded-lg p-1.5 transition hover:bg-sky-50"
              >↩️</button>
            </div>
          </div>

          <div v-if="!pagos.length" class="p-8 text-center text-sm text-slate-400">
            💳 Sin pagos registrados aún
          </div>
        </div>
      </div>
    </div>

    <div v-else class="rounded-2xl border-2 border-dashed border-slate-200 p-16 text-center text-slate-400">
      💰 Selecciona una reserva arriba para ver su cuenta y registrar cobros
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