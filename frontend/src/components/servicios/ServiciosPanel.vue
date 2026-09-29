<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToastStore()

const servicios = ref([])
const cargando = ref(true)
const filtro = ref('Todos')

const modalAbierto = ref(false)
const editandoId = ref(null)
const guardando = ref(false)
const aEliminar = ref(null)
const eliminando = ref(false)

const formVacio = { nombre: '', descripcion: '', precio: '' }
const form = ref({ ...formVacio })

// Emojis por nombre (con fallback)
const emojis = {
  desayuno: '🥐', almuerzo: '🍛', cena: '🍝', piscina: '🏊', sauna: '🧖',
  recreacion: '🎲', recreación: '🎲', lavanderia: '🧺', lavandería: '🧺',
  traslado: '🚐', masaje: '💆', gimnasio: '🏋️', bar: '🍸',
  habitacion: '🛎️', 'habitación': '🛎️', minibar: '🥤',
}
const emojiDe = (s) => {
  const q = s.nombre.toLowerCase()
  for (const k in emojis) if (q.includes(k)) return emojis[k]
  return '🍽️'
}

const gradientes = [
  'from-amber-400 to-orange-500', 'from-emerald-500 to-teal-600',
  'from-sky-500 to-blue-600', 'from-violet-500 to-purple-600',
  'from-rose-500 to-pink-600',
]
const gradienteDe = (i) => gradientes[i % gradientes.length]

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

const filtrados = computed(() =>
  filtro.value === 'Todos'
    ? servicios.value
    : servicios.value.filter((s) => s.estado === filtro.value),
)

const conteo = (estado) =>
  estado === 'Todos'
    ? servicios.value.length
    : servicios.value.filter((s) => s.estado === estado).length

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/servicio/')
    servicios.value = data
  } catch {
    toast.show('Error al cargar los servicios', 'error')
  } finally {
    cargando.value = false
  }
}

function abrirCrear() {
  form.value = { ...formVacio }
  editandoId.value = null
  modalAbierto.value = true
}

function abrirEditar(s) {
  form.value = {
    nombre: s.nombre,
    descripcion: s.descripcion || '',
    precio: Number(s.precio),
  }
  editandoId.value = s.id_servicio
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    const datos = { ...form.value, precio: Number(form.value.precio) }
    if (editandoId.value) {
      await api.put(`/servicio/${editandoId.value}`, datos)
      toast.show(`Servicio "${datos.nombre}" actualizado`)
    } else {
      await api.post('/servicio/', datos)
      toast.show(`Servicio "${datos.nombre}" creado`)
    }
    modalAbierto.value = false
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al guardar', 'error')
  } finally {
    guardando.value = false
  }
}

async function cambiarEstado(s) {
  const nuevo = s.estado === 'Activo' ? 'Inactivo' : 'Activo'
  const anterior = s.estado
  s.estado = nuevo // optimista
  try {
    await api.patch(`/servicio/${s.id_servicio}/estado`, { estado: nuevo })
    toast.show(`"${s.nombre}" ahora está ${nuevo}`, 'info')
  } catch (e) {
    s.estado = anterior
    toast.show(e.response?.data?.detail || 'Error al cambiar estado', 'error')
  }
}

async function eliminar() {
  eliminando.value = true
  try {
    await api.delete(`/servicio/${aEliminar.value.id_servicio}`)
    toast.show(`Servicio "${aEliminar.value.nombre}" eliminado`)
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
    <!-- Filtros + botón -->
    <div class="mb-5 flex flex-wrap items-center gap-2 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <button
        v-for="f in ['Todos', 'Activo', 'Inactivo']"
        :key="f"
        @click="filtro = f"
        class="rounded-full px-4 py-1.5 text-xs font-semibold transition"
        :class="filtro === f ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
      >
        {{ f }} ({{ conteo(f) }})
      </button>
      <button
        @click="abrirCrear"
        class="ml-auto flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
      >
        <span class="text-lg leading-none">＋</span> Nuevo Servicio
      </button>
    </div>

    <!-- Grid de servicios -->
    <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando servicios...</div>

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <div
        v-for="(s, i) in filtrados"
        :key="s.id_servicio"
        class="group relative rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
        :class="{ 'opacity-60': s.estado === 'Inactivo' }"
      >
        <div class="mb-3 flex items-start justify-between">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br text-2xl text-white shadow-md"
            :class="gradienteDe(i)"
          >
            {{ emojiDe(s) }}
          </div>

          <!-- Switch Activo/Inactivo -->
          <button
            @click="cambiarEstado(s)"
            :title="s.estado === 'Activo' ? 'Desactivar' : 'Activar'"
            class="relative h-6 w-11 rounded-full transition-colors duration-200"
            :class="s.estado === 'Activo' ? 'bg-emerald-500' : 'bg-slate-300'"
          >
            <span
              class="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200"
              :class="s.estado === 'Activo' ? 'translate-x-5' : ''"
            />
          </button>
        </div>

        <p class="font-bold text-slate-800">{{ s.nombre }}</p>
        <p class="mt-1 min-h-10 text-xs text-slate-500">{{ s.descripcion || 'Sin descripción' }}</p>

        <div class="mt-3 flex items-end justify-between border-t border-slate-50 pt-3">
          <div>
            <p class="text-xl font-black text-slate-800">{{ formatoPrecio(s.precio) }}</p>
            <p class="text-[11px] text-slate-400">precio vigente</p>
          </div>
          <div class="flex gap-1 opacity-0 transition group-hover:opacity-100">
            <button @click="abrirEditar(s)" title="Editar" class="rounded-lg p-1.5 transition hover:bg-slate-100">✏️</button>
            <button @click="aEliminar = s" title="Eliminar" class="rounded-lg p-1.5 transition hover:bg-rose-50">🗑️</button>
          </div>
        </div>

        <span
          class="absolute top-3 left-3 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
          :class="s.estado === 'Activo' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'"
          v-if="s.estado === 'Inactivo'"
        >
          Inactivo
        </span>
      </div>

      <div v-if="!filtrados.length" class="col-span-full rounded-2xl border-2 border-dashed border-slate-200 p-12 text-center text-slate-400">
        🍽️ No hay servicios con ese filtro
      </div>
    </div>

    <!-- Modal crear/editar -->
    <BaseModal
      :abierta="modalAbierto"
      :titulo="editandoId ? `Editar: ${form.nombre}` : 'Nuevo Servicio'"
      @cerrar="modalAbierto = false"
    >
      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Nombre *</label>
          <input v-model="form.nombre" required placeholder="Ej: Desayuno bufet" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Descripción</label>
          <textarea v-model="form.descripcion" rows="2" class="w-full resize-none rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Precio (Bs) *</label>
          <input v-model="form.precio" type="number" step="0.01" min="0.01" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          <p v-if="editandoId" class="mt-1 text-[11px] text-amber-600">
            ⚠️ Cambiar el precio NO afecta los consumos ya registrados (tienen precio congelado)
          </p>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="modalAbierto = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button type="submit" :disabled="guardando" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60">
            {{ guardando ? 'Guardando...' : editandoId ? 'Guardar Cambios' : 'Crear Servicio' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <ConfirmDialog
      :abierta="!!aEliminar"
      :cargando="eliminando"
      :titulo="`¿Eliminar servicio ${aEliminar?.nombre}?`"
      mensaje="El servicio saldrá del catálogo. Los consumos históricos conservan su precio registrado."
      @cancelar="aEliminar = null"
      @confirmar="eliminar"
    />
  </div>
</template>