<script setup>
import { ref, watch } from 'vue'
import api from '@/api/client'

const props = defineProps({
  abierta: Boolean,
  idReserva: Number,
})
const emit = defineEmits(['cerrar'])

const detalle = ref(null)
const cargando = ref(false)

watch(
  () => props.abierta,
  async (abierta) => {
    if (!abierta || !props.idReserva) return
    cargando.value = true
    detalle.value = null
    try {
      const { data } = await api.get(`/reserva/${props.idReserva}`)
      detalle.value = data
    } finally {
      cargando.value = false
    }
  },
)

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`
const formatoFecha = (f) =>
  new Date(f).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })

const fila = (label, valor, destacado = false) => ({ label, valor, destacado })
</script>

<template>
  <div
    v-if="abierta"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
    @click.self="emit('cerrar')"
  >
    <div class="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h3 class="text-lg font-bold text-slate-800">
          Cuenta · Reserva #{{ idReserva }}
        </h3>
        <button @click="emit('cerrar')" class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700">✕</button>
      </div>

      <div class="max-h-[70vh] overflow-y-auto p-6">
        <div v-if="cargando" class="py-8 text-center text-slate-400">Calculando cuenta...</div>

        <div v-else-if="detalle" class="space-y-5">
          <!-- Info del huésped y estadía -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Huésped</p>
              <p class="font-semibold text-slate-800">
                {{ detalle.huesped.nombre }} {{ detalle.huesped.apellido }}
              </p>
              <p class="font-mono text-xs text-slate-400">CI {{ detalle.huesped.ci }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Estadía</p>
              <p class="font-semibold text-slate-800">
                {{ formatoFecha(detalle.fecha_entrada) }} → {{ formatoFecha(detalle.fecha_salida) }}
              </p>
              <p class="text-xs text-slate-400">
                Hab. {{ detalle.habitacion.numero }} · {{ detalle.noches }} noche(s)
              </p>
            </div>
          </div>

          <!-- Desglose -->
          <div class="space-y-1.5 text-sm">
            <div class="flex justify-between text-slate-600">
              <span>🏨 Habitación ({{ detalle.noches }}n × {{ formatoPrecio(detalle.habitacion.tipo_habitacion?.precio_noche) }})</span>
              <span class="font-semibold">{{ formatoPrecio(detalle.total_habitacion) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>🍳 Servicios adicionales</span>
              <span class="font-semibold">{{ formatoPrecio(detalle.total_servicios) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>💳 Pagos realizados</span>
              <span class="font-semibold text-emerald-600">−{{ formatoPrecio(detalle.total_pagado) }}</span>
            </div>
          </div>

          <!-- Saldo -->
          <div
            class="flex items-center justify-between rounded-xl p-4"
            :class="Number(detalle.saldo) > 0 ? 'bg-rose-50 ring-1 ring-rose-200' : 'bg-emerald-50 ring-1 ring-emerald-200'"
          >
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {{ Number(detalle.saldo) > 0 ? 'Saldo pendiente' : 'Cuenta saldada ✅' }}
              </p>
              <p
                class="text-2xl font-black"
                :class="Number(detalle.saldo) > 0 ? 'text-rose-600' : 'text-emerald-600'"
              >
                {{ formatoPrecio(detalle.saldo) }}
              </p>
            </div>
            <span class="text-4xl">{{ Number(detalle.saldo) > 0 ? '💸' : '🎉' }}</span>
          </div>

          <p v-if="Number(detalle.saldo) > 0" class="text-center text-xs text-slate-400">
            Registra el pago antes del check-out — el backend bloquea la salida con deuda
          </p>
        </div>
      </div>
    </div>
  </div>
</template>