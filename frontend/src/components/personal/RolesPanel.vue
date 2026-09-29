<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from './BaseModal.vue'

const toast = useToastStore()

const roles = ref([])
const cargando = ref(true)
const modalAbierto = ref(false)
const guardando = ref(false)
const form = ref({ id_rol: '', nombre: '', descripcion: '' })

const sugerirId = (lista) => {
  const max = lista.reduce((m, r) => {
    const n = parseInt(String(r.id_rol).replace(/\D/g, '')) || 0
    return Math.max(m, n)
  }, 0)
  return `ROL${String(max + 1).padStart(3, '0')}`
}

const formatoFecha = (f) =>
  new Date(f).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/rol/')
    roles.value = data
  } catch {
    toast.show('Error al cargar los roles', 'error')
  } finally {
    cargando.value = false
  }
}

function abrirModal() {
  form.value = { id_rol: sugerirId(roles.value), nombre: '', descripcion: '' }
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    await api.post('/rol/', form.value)
    toast.show(`Rol "${form.value.nombre}" creado correctamente`)
    modalAbierto.value = false
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al crear el rol', 'error')
  } finally {
    guardando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
    <div class="flex items-center justify-between border-b border-slate-100 p-5">
      <p class="text-sm text-slate-500">{{ roles.length }} rol(es) registrados</p>
      <button
        @click="abrirModal"
        class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
      >
        <span class="text-lg leading-none">＋</span> Nuevo Rol
      </button>
    </div>

    <div class="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
      <div v-if="cargando" class="col-span-full p-12 text-center text-slate-400">Cargando roles...</div>

      <div
        v-for="(r, i) in roles"
        :key="r.id_rol"
        class="group rounded-2xl border border-slate-100 p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="mb-3 flex items-center gap-3">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl text-lg text-white shadow-md"
            :class="['bg-gradient-to-br from-rose-500 to-pink-600', 'from-sky-500 to-blue-600', 'from-emerald-500 to-teal-600', 'from-violet-500 to-purple-600'][i % 4]"
          >
            🛡️
          </div>
          <div>
            <p class="font-bold text-slate-800">{{ r.nombre }}</p>
            <p class="text-xs text-slate-400">{{ r.id_rol }}</p>
          </div>
        </div>
        <p class="min-h-10 text-sm text-slate-500">{{ r.descripcion || 'Sin descripción' }}</p>
        <p class="mt-3 text-xs text-slate-400">Registrado el {{ formatoFecha(r.fecha_creacion) }}</p>
      </div>

      <div v-if="!cargando && !roles.length" class="col-span-full p-12 text-center text-slate-400">
        🛡️ Aún no hay roles registrados
      </div>
    </div>

    <BaseModal :abierta="modalAbierto" titulo="Nuevo Rol" @cerrar="modalAbierto = false">
      <form @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">ID *</label>
            <input v-model="form.id_rol" required readonly class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-500" />
          </div>
          <div class="col-span-2">
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nombre *</label>
            <input v-model="form.nombre" required placeholder="Ej: Recepcionista" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Descripción</label>
          <textarea v-model="form.descripcion" rows="3" class="w-full resize-none rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="modalAbierto = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">Cancelar</button>
          <button type="submit" :disabled="guardando" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60">
            {{ guardando ? 'Guardando...' : 'Crear Rol' }}
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>