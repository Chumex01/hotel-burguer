<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from './BaseModal.vue'

const toast = useToastStore()

const usuarios = ref([])
const roles = ref([])
const cargando = ref(true)
const busqueda = ref('')
const modalAbierto = ref(false)
const guardando = ref(false)
const verPassword = ref(false)

const formVacio = {
  nombre: '', apellido: '', usuario: '',
  email: '', password: '', id_rol: '', estado: 'Activo',
}
const form = ref({ ...formVacio })

const usuariosFiltrados = computed(() => {
  const q = busqueda.value.toLowerCase()
  if (!q) return usuarios.value
  return usuarios.value.filter(
    (u) =>
      u.nombre.toLowerCase().includes(q) ||
      u.apellido.toLowerCase().includes(q) ||
      u.usuario.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q),
  )
})

const nombreRol = (id) => roles.value.find((r) => r.id_rol === id)?.nombre || id

const iniciales = (u) =>
  (u.nombre[0] + (u.apellido[0] || '')).toUpperCase()

// Colores de avatar según id (consistente por usuario)
const colores = ['from-rose-500 to-pink-600', 'from-sky-500 to-blue-600', 'from-emerald-500 to-teal-600', 'from-violet-500 to-purple-600', 'from-amber-500 to-orange-600']
const colorAvatar = (u) => {
  const n = u.id_usuario.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  return colores[n % colores.length]
}

const formatoFecha = (f) =>
  new Date(f).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })

async function cargar() {
  cargando.value = true
  try {
    const [resU, resR] = await Promise.all([api.get('/usuario/'), api.get('/rol/')])
    usuarios.value = resU.data
    roles.value = resR.data
  } catch (e) {
    toast.show('Error al cargar los datos', 'error')
  } finally {
    cargando.value = false
  }
}

function abrirModal() {
  form.value = { ...formVacio }
  verPassword.value = false
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    await api.post('/usuario/', form.value)
    toast.show(`Usuario "${form.value.usuario}" creado correctamente`)
    modalAbierto.value = false
    form.value = { ...formVacio }
    await cargar()
  } catch (e) {
    toast.show(e.response?.data?.detail || 'Error al crear el usuario', 'error')
  } finally {
    guardando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
    <!-- Barra superior -->
    <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 p-5">
      <div class="relative">
        <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
        <input
          v-model="busqueda"
          placeholder="Buscar por nombre, usuario o email..."
          class="w-80 rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
        />
      </div>
<button @click="abrirModal" class="...">
  <span class="text-lg leading-none">＋</span> Nuevo Usuario
</button>
    </div>

    <!-- Tabla -->
    <div class="overflow-x-auto p-2">
      <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando usuarios...</div>

      <table v-else class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs uppercase tracking-wide text-slate-400">
            <th class="px-4 py-3">Usuario</th>
            <th class="px-4 py-3">Correo</th>
            <th class="px-4 py-3">Rol</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Registro</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in usuariosFiltrados"
            :key="u.id_usuario"
            class="border-t border-slate-50 transition hover:bg-slate-50/80"
          >
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-3">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-sm font-bold text-white"
                  :class="colorAvatar(u)"
                >
                  {{ iniciales(u) }}
                </div>
                <div>
                  <p class="font-semibold text-slate-800">{{ u.nombre }} {{ u.apellido }}</p>
                  <p class="text-xs text-slate-400">@{{ u.usuario }} · {{ u.id_usuario }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3.5 text-slate-600">{{ u.email }}</td>
            <td class="px-4 py-3.5">
              <span class="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                {{ nombreRol(u.id_rol) }}
              </span>
            </td>
            <td class="px-4 py-3.5">
              <span
                class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
                :class="u.estado === 'Activo' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'"
              >
                <span class="h-1.5 w-1.5 rounded-full" :class="u.estado === 'Activo' ? 'bg-emerald-500' : 'bg-rose-500'" />
                {{ u.estado }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-slate-500">{{ formatoFecha(u.fecha_creacion) }}</td>
          </tr>

          <tr v-if="!usuariosFiltrados.length">
            <td colspan="5" class="px-4 py-12 text-center text-slate-400">
              🗂️ No hay usuarios que coincidan con la búsqueda
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <BaseModal :abierta="modalAbierto" titulo="Nuevo Usuario" @cerrar="modalAbierto = false">
      <form @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nombre *</label>
            <input v-model="form.nombre" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Apellido *</label>
            <input v-model="form.apellido" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Nombre de usuario *</label>
          <input v-model="form.usuario" required placeholder="recepcion01" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Correo electrónico *</label>
          <input v-model="form.email" type="email" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Rol *</label>
            <select v-model="form.id_rol" required class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200">
              <option value="" disabled>Seleccionar...</option>
              <option v-for="r in roles" :key="r.id_rol" :value="r.id_rol">{{ r.nombre }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Estado</label>
            <select v-model="form.estado" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200">
              <option>Activo</option>
              <option>Inactivo</option>
            </select>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">Contraseña * (mín. 8 caracteres)</label>
          <div class="relative">
            <input v-model="form.password" :type="verPassword ? 'text' : 'password'" required minlength="8" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-12 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
            <button type="button" @click="verPassword = !verPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-sm">{{ verPassword ? '🙈' : '👁️' }}</button>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="modalAbierto = false" class="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100">
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="guardando"
            class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95 disabled:opacity-60"
          >
            {{ guardando ? 'Guardando...' : 'Crear Usuario' }}
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>