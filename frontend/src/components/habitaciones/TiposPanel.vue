<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToastStore()

const tipos = ref([])
const cargando = ref(true)
const modalAbierto = ref(false)
const editandoId = ref(null)
const guardando = ref(false)
const aEliminar = ref(null)
const eliminando = ref(false)

const formVacio = { nombre: '', descripcion: '', capacidad: 2, precio_noche: '' }
const form = ref({ ...formVacio })

const gradientes = [
  'from-sky-500 to-blue-600',
  'from-emerald-500 to-teal-600',
  'from-violet-500 to-purple-600',
  'from-amber-500 to-orange-600',
  'from-rose-500 to-pink-600',
]
const gradienteDe = (i) => gradientes[i % gradientes.length]

const formatoPrecio = (p) => `Bs ${Number(p || 0).toFixed(2)}`

const resumen = computed(() =>
  `Capacidad promedio: ${
    tipos.value.length
      ? (tipos.value.reduce((a, t) => a + t.capacidad, 0) / tipos.value.length).toFixed(1)
      : 0
  } personas · Rango de precios: ${
    tipos.value.length
      ? `${formatoPrecio(Math.min(...tipos.value.map((t) => Number(t.precio_noche))))} — ${formatoPrecio(Math.max(...tipos.value.map((t) => Number(t.precio_noche))))}`
      : '—'
  }`,
)

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/tipo-habitacion/')
    tipos.value = data
  } catch {
    toast.show('Error al cargar los tipos', 'error')
  } finally {
    cargando.value = false
  }
}

function abrirCrear() {
  form.value = { ...formVacio }
  editandoId.value = null
  modalAbierto.value = true
}

function abrirEditar(t) {
  form.value = {
    nombre: t.nombre,
    descripcion: t.descripcion || '',
    capacidad: t.capacidad,
    precio_noche: Number(t.precio_noche),
  }
  editandoId.value = t.id_tipo
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    const datos = { ...form.value, precio_noche: Number(form.value.precio_noche) }
    if (editandoId.value) {
      await api.put(`/tipo-habitacion/${editandoId.value}`, datos)
      toast.show(`Tipo "${datos.nombre}" actualizado`)
    } else {
      await api.post('/tipo-habitacion/', datos)
      toast.show(`Tipo "${datos.nombre}" creado`)
    }
    modalAbierto.value = false
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al guardar', 'error')
  } finally {
    guardando.value = false
  }
}

async function eliminar() {
  eliminando.value = true
  try {
    await api.delete(`/tipo-habitacion/${aEliminar.value.id_tipo}`)
    toast.show(`Tipo "${aEliminar.value.nombre}" eliminado`)
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
  <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-5">
      <p class="text-sm text-slate-500">{{ resumen }}</p>
      <button
        @click="abrirCrear"
        class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
      >
        <span class="text-lg leading-none">＋</span> Nuevo Tipo
      </button>
    </div>

    <div class="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
      <div v-if="cargando" class="col-span-full p-12 text-center text-slate-400">Cargando tipos...</div>

      <div
        v-for="(t, i) in tipos"
        :key="t.id_tipo"
        class="group relative rounded-2xl border border-slate-100 p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="mb-3 flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-lg text-white shadow-md" :class="gradienteDe(i)">
            🛏️
          </div>
          <div>
            <p class="font-bold text-slate-800">{{ t.nombre }}</p>
            <p class="text-xs text-slate-400">Tipo #{{ t.id_tipo }}</p>
          </div>
        </div>

        <p class="min-h-10 text-sm text-slate-500">{{ t.descripcion || 'Sin descripción' }}</p>

        <div class="mt-4 flex items-end justify-between border-t border-slate-50 pt-3">
          <div>
            <p class="text-xl font-black text-slate-800">{{ formatoPrecio(t.precio_noche) }}</p>
            <p class="text-[11px] text-slate-400">por noche</p>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            👤 {{ t.capacidad }}
          </span>
        </div>

        <!-- Botones al hover -->
        <div class="absolute right-3 top-3 flex gap-1 opacity-0 transition group-hover:opacity-100">
          <button @click="abrirEditar(t)" title="Editar" class="rounded-lg bg-white/90 p-1.5 shadow ring-1 ring-slate-200 transition hover:bg-slate-50">✏️</button>
          <button @click="aEliminar = t" title="Eliminar" class="rounded-lg bg-white/90 p-1.5 shadow ring-1 ring-slate-200 transition hover:bg-rose-50">🗑️</button>
        </div>
      </div>

      <div v-if="!cargando && !tipos.length" class="col-span-full p-12 text-center text-slate-400">
        🏷️ Aún no hay tipos de habitación
      </div>
    </div>

    <BaseModal :abierta="modalAbierto" :titulo="editandoId ? `Editar Tipo: ${form.nombre}` : 'Nuevo Tipo de Habitación'" @cerrar="modalAbierto = false">
      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Nombre *</label>
          <input v-model="form.nombre" required placeholder="Ej: Matrimonial" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Descripción</label>
          <textarea v-model="form.descripcion" rows="3" class="w-full resize-none rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Capacidad (personas) *</label>
            <input v-model.number="form.capacidad" type="number" min="1" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Precio por noche (Bs) *</label>
            <input v-model="form.precio_noche" type="number" step="0.01" min="0.01" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="modalAbierto = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button type="submit" :disabled="guardando" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60">
            {{ guardando ? 'Guardando...' : editandoId ? 'Guardar Cambios' : 'Crear Tipo' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <ConfirmDialog
      :abierta="!!aEliminar"
      :cargando="eliminando"
      :titulo="`¿Eliminar tipo ${aEliminar?.nombre}?`"
      mensaje="No será posible si tiene habitaciones asociadas."
      @cancelar="aEliminar = null"
      @confirmar="eliminar"
    />
  </div>
</template>