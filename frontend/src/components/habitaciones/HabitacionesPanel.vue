<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToastStore()

const ESTADOS = ['Disponible', 'Ocupada', 'Mantenimiento', 'Limpieza']

const habitaciones = ref([])
const tipos = ref([])
const cargando = ref(true)

const filtroEstado = ref('Todos')
const filtroPiso = ref('')
const filtroTipo = ref('')

const modalAbierto = ref(false)
const editandoId = ref(null)
const guardando = ref(false)
const aEliminar = ref(null)
const eliminando = ref(false)

const formVacio = { numero: '', piso: 1, id_tipo: '', estado: 'Disponible' }
const form = ref({ ...formVacio })

const coloresEstado = {
  Disponible: { bg: 'bg-emerald-500', hover: 'hover:bg-emerald-600', texto: 'text-emerald-600', chip: 'bg-emerald-500' },
  Ocupada: { bg: 'bg-rose-500', hover: 'hover:bg-rose-600', texto: 'text-rose-600', chip: 'bg-rose-500' },
  Mantenimiento: { bg: 'bg-amber-500', hover: 'hover:bg-amber-600', texto: 'text-amber-600', chip: 'bg-amber-500' },
  Limpieza: { bg: 'bg-sky-500', hover: 'hover:bg-sky-600', texto: 'text-sky-600', chip: 'bg-sky-500' },
}

// --- Datos derivados ---
const pisos = computed(() =>
  [...new Set(habitaciones.value.map((h) => h.piso))].sort((a, b) => a - b),
)

const tipoDe = (id) => tipos.value.find((t) => t.id_tipo === id)

const filtradas = computed(() =>
  habitaciones.value.filter(
    (h) =>
      (filtroEstado.value === 'Todos' || h.estado === filtroEstado.value) &&
      (!filtroPiso.value || h.piso === Number(filtroPiso.value)) &&
      (!filtroTipo.value || h.id_tipo === Number(filtroTipo.value)),
  ),
)

const conteo = (estado) => habitaciones.value.filter((h) => h.estado === estado).length

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

// --- Acciones ---
async function cargar() {
  cargando.value = true
  try {
    const [resH, resT] = await Promise.all([api.get('/habitacion/'), api.get('/tipo-habitacion/')])
    habitaciones.value = resH.data
    tipos.value = resT.data
  } catch {
    toast.show('Error al cargar las habitaciones', 'error')
  } finally {
    cargando.value = false
  }
}

function abrirCrear() {
  form.value = { ...formVacio }
  editandoId.value = null
  modalAbierto.value = true
}

function abrirEditar(h) {
  form.value = { numero: h.numero, piso: h.piso, id_tipo: h.id_tipo, estado: h.estado }
  editandoId.value = h.id_habitacion
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    if (editandoId.value) {
      await api.put(`/habitacion/${editandoId.value}`, form.value)
      toast.show(`Habitación ${form.value.numero} actualizada`)
    } else {
      await api.post('/habitacion/', form.value)
      toast.show(`Habitación ${form.value.numero} creada`)
    }
    modalAbierto.value = false
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al guardar', 'error')
  } finally {
    guardando.value = false
  }
}

async function cambiarEstado(h, nuevoEstado) {
  if (h.estado === nuevoEstado) return
  const anterior = h.estado
  h.estado = nuevoEstado // 🎨 optimista: se ve al instante
  try {
    await api.patch(`/habitacion/${h.id_habitacion}/estado`, { estado: nuevoEstado })
    toast.show(`Habitación ${h.numero} → ${nuevoEstado}`, 'info')
  } catch (e) {
    h.estado = anterior // ↩️ rollback si falla
    toast.show(e.response?.data?.detail || 'Error al cambiar estado', 'error')
  }
}

async function eliminar() {
  eliminando.value = true
  try {
    await api.delete(`/habitacion/${aEliminar.value.id_habitacion}`)
    toast.show(`Habitación ${aEliminar.value.numero} eliminada`)
    aEliminar.value = null
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al eliminar', 'error')
    aEliminar.value = null
  } finally {
    eliminando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <!-- Barra de filtros -->
    <div class="mb-5 flex flex-wrap items-center gap-2 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <button
        @click="filtroEstado = 'Todos'"
        class="rounded-full px-4 py-1.5 text-xs font-semibold transition"
        :class="filtroEstado === 'Todos' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
      >
        Todas ({{ habitaciones.length }})
      </button>
      <button
        v-for="e in ESTADOS"
        :key="e"
        @click="filtroEstado = e"
        class="rounded-full px-4 py-1.5 text-xs font-semibold text-white transition opacity-90 hover:opacity-100"
        :class="filtroEstado === e ? `${coloresEstado[e].chip} ring-2 ring-offset-2 ring-slate-300` : coloresEstado[e].chip"
      >
        {{ e }} ({{ conteo(e) }})
      </button>

      <div class="ml-auto flex items-center gap-2">
        <select v-model="filtroPiso" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-slate-400">
          <option value="">Todos los pisos</option>
          <option v-for="p in pisos" :key="p" :value="p">Piso {{ p }}</option>
        </select>
        <select v-model="filtroTipo" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-slate-400">
          <option value="">Todos los tipos</option>
          <option v-for="t in tipos" :key="t.id_tipo" :value="t.id_tipo">{{ t.nombre }}</option>
        </select>
        <button
          @click="abrirCrear"
          class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
        >
          <span class="text-lg leading-none">＋</span> Nueva
        </button>
      </div>
    </div>

    <!-- Grid de habitaciones -->
    <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando habitaciones...</div>

    <div v-else class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6">
      <div
        v-for="h in filtradas"
        :key="h.id_habitacion"
        class="group relative overflow-hidden rounded-2xl bg-white p-4 pt-5 shadow-sm ring-1 ring-slate-200 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
      >
        <!-- Cinta de color según estado -->
        <div class="absolute inset-x-0 top-0 h-1.5" :class="coloresEstado[h.estado].bg" />

        <div class="flex items-start justify-between">
          <div>
            <p class="text-2xl font-black tracking-tight text-slate-800">{{ h.numero }}</p>
            <p class="text-xs font-semibold" :class="coloresEstado[h.estado].texto">{{ h.estado }}</p>
          </div>
          <button
            @click="abrirEditar(h)"
            title="Editar"
            class="rounded-lg p-1.5 text-slate-300 opacity-0 transition hover:bg-slate-100 hover:text-slate-600 group-hover:opacity-100"
          >
            ✏️
          </button>
        </div>

        <div class="mt-2 min-h-12">
          <p class="text-sm font-semibold text-slate-700">{{ tipoDe(h.id_tipo)?.nombre || '—' }}</p>
          <p class="text-xs text-slate-400">
            {{ formatoPrecio(tipoDe(h.id_tipo)?.precio_noche) }}/noche · 👤 {{ tipoDe(h.id_tipo)?.capacidad ?? '?' }}
          </p>
        </div>

        <!-- Cambio rápido de estado -->
        <select
          :value="h.estado"
          @change="cambiarEstado(h, $event.target.value)"
          class="mt-3 w-full cursor-pointer appearance-none rounded-lg px-2.5 py-1.5 text-center text-xs font-semibold text-white outline-none transition"
          :class="coloresEstado[h.estado].bg"
        >
          <option v-for="e in ESTADOS" :key="e" :value="e">{{ e }}</option>
        </select>
      </div>

      <div v-if="!filtradas.length" class="col-span-full rounded-2xl border-2 border-dashed border-slate-200 p-12 text-center text-slate-400">
        🛏️ No hay habitaciones con esos filtros
      </div>
    </div>

    <!-- Modal crear/editar -->
    <BaseModal :abierta="modalAbierto" :titulo="editandoId ? `Editar Habitación ${form.numero}` : 'Nueva Habitación'" @cerrar="modalAbierto = false">
      <form @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Número *</label>
            <input v-model="form.numero" required placeholder="Ej: 204" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Piso *</label>
            <input v-model.number="form.piso" type="number" min="1" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Tipo *</label>
          <select v-model="form.id_tipo" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200">
            <option value="" disabled>Seleccionar...</option>
            <option v-for="t in tipos" :key="t.id_tipo" :value="t.id_tipo">
              {{ t.nombre }} — {{ formatoPrecio(t.precio_noche) }}/noche · {{ t.capacidad }} personas
            </option>
          </select>
          <p v-if="!tipos.length" class="mt-1 text-xs text-amber-600">
            ⚠️ Primero crea un tipo en la pestaña "Tipos y Precios"
          </p>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Estado</label>
          <select v-model="form.estado" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200">
            <option v-for="e in ESTADOS" :key="e">{{ e }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="modalAbierto = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button type="submit" :disabled="guardando" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60">
            {{ guardando ? 'Guardando...' : editandoId ? 'Guardar Cambios' : 'Crear Habitación' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <!-- Confirmar eliminación -->
    <ConfirmDialog
      :abierta="!!aEliminar"
      :cargando="eliminando"
      :titulo="`¿Eliminar habitación ${aEliminar?.numero}?`"
      mensaje="Esta acción no se puede deshacer. No será posible si tiene reservas asociadas."
      @cancelar="aEliminar = null"
      @confirmar="eliminar"
    />
  </div>
</template>