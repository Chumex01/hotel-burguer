<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/personal/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToastStore()

const huespedes = ref([])
const cargando = ref(true)
const busqueda = ref('')

const modalAbierto = ref(false)
const editandoId = ref(null)
const guardando = ref(false)
const aEliminar = ref(null)
const eliminando = ref(false)

const formVacio = { ci: '', nombre: '', apellido: '', telefono: '', email: '', nacionalidad: '' }
const form = ref({ ...formVacio })

// --- Presentación ---
const banderas = {
  boliviana: '🇧🇴', boliviano: '🇧🇴',
  argentina: '🇦🇷', argentino: '🇦🇷',
  peruana: '🇵🇪', peruano: '🇵🇪',
  brasileña: '🇧🇷', brasileño: '🇧🇷', brasilena: '🇧🇷',
  chilena: '🇨🇱', chileno: '🇨🇱',
  colombiana: '🇨🇴', colombiano: '🇨🇴',
  ecuatoriana: '🇪🇨', ecuatoriano: '🇪🇨',
  mexicana: '🇲🇽', mexicano: '🇲🇽',
  española: '🇪🇸', espanola: '🇪🇸', español: '🇪🇸',
  estadounidense: '🇺🇸', americana: '🇺🇸',
  uruguaya: '🇺🇾', paraguaya: '🇵🇾', venezolana: '🇻🇪',
}
const banderaDe = (nac) => banderas[nac?.toLowerCase().trim()] || '🌎'

const colores = [
  'from-rose-500 to-pink-600', 'from-sky-500 to-blue-600',
  'from-emerald-500 to-teal-600', 'from-violet-500 to-purple-600',
  'from-amber-500 to-orange-600',
]
const colorAvatar = (h) => {
  const n = String(h.id_huesped).split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  return colores[n % colores.length]
}
const iniciales = (h) => (h.nombre[0] + (h.apellido[0] || '')).toUpperCase()

const formatoFecha = (f) =>
  new Date(f).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })

// --- Datos derivados ---
const ordenados = computed(() =>
  [...huespedes.value].sort(
    (a, b) => new Date(b.fecha_registro) - new Date(a.fecha_registro),
  ),
)

const filtrados = computed(() => {
  const q = busqueda.value.toLowerCase().trim()
  if (!q) return ordenados.value
  return ordenados.value.filter(
    (h) =>
      `${h.nombre} ${h.apellido}`.toLowerCase().includes(q) ||
      h.ci.toLowerCase().includes(q) ||
      (h.email || '').toLowerCase().includes(q) ||
      (h.telefono || '').includes(q),
  )
})

const stats = computed(() => {
  const hoy = new Date()
  return {
    total: huespedes.value.length,
    nuevosMes: huespedes.value.filter((h) => {
      const f = new Date(h.fecha_registro)
      return f.getMonth() === hoy.getMonth() && f.getFullYear() === hoy.getFullYear()
    }).length,
    nacionalidades: new Set(huespedes.value.map((h) => h.nacionalidad).filter(Boolean)).size,
    conContacto: huespedes.value.filter((h) => h.telefono || h.email).length,
  }
})

// --- Acciones ---
async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/huesped/')
    huespedes.value = data
  } catch {
    toast.show('Error al cargar los huéspedes', 'error')
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
  form.value = {
    ci: h.ci,
    nombre: h.nombre,
    apellido: h.apellido,
    telefono: h.telefono || '',
    email: h.email || '',
    nacionalidad: h.nacionalidad || '',
  }
  editandoId.value = h.id_huesped
  modalAbierto.value = true
}

// Campos opcionales vacíos → null (evita dejar "" sucio en la BD)
function normalizar(datos) {
  const limpio = { ...datos }
  for (const campo of ['telefono', 'email', 'nacionalidad']) {
    if (!limpio[campo] || !String(limpio[campo]).trim()) limpio[campo] = null
  }
  return limpio
}

async function guardar() {
  guardando.value = true
  try {
    const datos = normalizar(form.value)
    if (editandoId.value) {
      await api.put(`/huesped/${editandoId.value}`, datos)
      toast.show(`Huésped "${datos.nombre} ${datos.apellido}" actualizado`)
    } else {
      await api.post('/huesped/', datos)
      toast.show(`Huésped "${datos.nombre} ${datos.apellido}" registrado 🎉`)
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
    await api.delete(`/huesped/${aEliminar.value.id_huesped}`)
    toast.show('Huésped eliminado')
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
    <!-- Stats -->
    <div class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Total huéspedes</p>
            <p class="mt-1 text-3xl font-black text-slate-800">{{ stats.total }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-2xl">👥</div>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Nuevos este mes</p>
            <p class="mt-1 text-3xl font-black text-emerald-600">{{ stats.nuevosMes }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-2xl">📅</div>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Nacionalidades</p>
            <p class="mt-1 text-3xl font-black text-violet-600">{{ stats.nacionalidades }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-2xl">🌎</div>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Con contacto</p>
            <p class="mt-1 text-3xl font-black text-amber-600">{{ stats.conContacto }}</p>
          </div>
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-2xl">📱</div>
        </div>
      </div>
    </div>

    <!-- Tabla -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 p-5">
        <div class="relative">
          <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
          <input
            v-model="busqueda"
            placeholder="Buscar por nombre, CI, email o teléfono..."
            class="w-80 rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
          />
        </div>
        <p class="text-xs text-slate-400">
          {{ filtrados.length }} de {{ huespedes.length }} huéspedes
        </p>
        <button
          @click="abrirCrear"
          class="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 active:scale-95"
        >
          <span class="text-lg leading-none">＋</span> Nuevo Huésped
        </button>
      </div>

      <div class="overflow-x-auto p-2">
        <div v-if="cargando" class="p-12 text-center text-slate-400">Cargando huéspedes...</div>

        <table v-else class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs uppercase tracking-wide text-slate-400">
              <th class="px-4 py-3">Huésped</th>
              <th class="px-4 py-3">Contacto</th>
              <th class="px-4 py-3">Nacionalidad</th>
              <th class="px-4 py-3">Registro</th>
              <th class="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="h in filtrados"
              :key="h.id_huesped"
              class="group border-t border-slate-50 transition hover:bg-slate-50/80"
            >
              <td class="px-4 py-3.5">
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-sm font-bold text-white"
                    :class="colorAvatar(h)"
                  >
                    {{ iniciales(h) }}
                  </div>
                  <div>
                    <p class="font-semibold text-slate-800">{{ h.nombre }} {{ h.apellido }}</p>
                    <p class="font-mono text-xs text-slate-400">CI: {{ h.ci }}</p>
                  </div>
                </div>
              </td>

              <td class="px-4 py-3.5">
                <div class="flex flex-col gap-0.5">
                  <a
                    v-if="h.telefono"
                    :href="`tel:${h.telefono}`"
                    class="flex items-center gap-1.5 text-xs text-slate-600 transition hover:text-sky-600"
                  >
                    📞 {{ h.telefono }}
                  </a>
                  <a
                    v-if="h.email"
                    :href="`mailto:${h.email}`"
                    class="flex items-center gap-1.5 text-xs text-slate-600 transition hover:text-sky-600"
                  >
                    ✉️ {{ h.email }}
                  </a>
                  <span v-if="!h.telefono && !h.email" class="text-xs text-slate-300">Sin contacto</span>
                </div>
              </td>

              <td class="px-4 py-3.5">
                <span v-if="h.nacionalidad" class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  {{ banderaDe(h.nacionalidad) }} {{ h.nacionalidad }}
                </span>
                <span v-else class="text-xs text-slate-300">—</span>
              </td>

              <td class="px-4 py-3.5 text-slate-500">{{ formatoFecha(h.fecha_registro) }}</td>

              <td class="px-4 py-3.5">
                <div class="flex justify-end gap-1 opacity-0 transition group-hover:opacity-100">
                  <button
                    @click="abrirEditar(h)"
                    title="Editar"
                    class="rounded-lg p-2 transition hover:bg-white hover:shadow-sm"
                  >
                    ✏️
                  </button>
                  <button
                    @click="aEliminar = h"
                    title="Eliminar"
                    class="rounded-lg p-2 transition hover:bg-rose-50"
                  >
                    🗑️
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="!filtrados.length">
              <td colspan="5" class="px-4 py-12 text-center text-slate-400">
                {{ busqueda ? '🕵️ Ningún huésped coincide con la búsqueda' : '👤 Aún no hay huéspedes registrados' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal crear/editar -->
    <BaseModal
      :abierta="modalAbierto"
      :titulo="editandoId ? 'Editar Huésped' : 'Nuevo Huésped'"
      @cerrar="modalAbierto = false"
    >
      <form @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Cédula de identidad *</label>
            <input
              v-model="form.ci"
              required
              placeholder="Ej: 1234567"
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 font-mono text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
            <p class="mt-1 text-[11px] text-slate-400">Único por huésped — es su identificador</p>
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nacionalidad</label>
            <input
              v-model="form.nacionalidad"
              placeholder="Ej: Boliviana"
              class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
          </div>
        </div>

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

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Teléfono</label>
            <input v-model="form.telefono" type="tel" placeholder="70012345" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Email</label>
            <input v-model="form.email" type="email" placeholder="juan@correo.com" class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200" />
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
            {{ guardando ? 'Guardando...' : editandoId ? 'Guardar Cambios' : 'Registrar Huésped' }}
          </button>
        </div>
      </form>
    </BaseModal>

    <!-- Confirmar eliminación -->
    <ConfirmDialog
      :abierta="!!aEliminar"
      :cargando="eliminando"
      :titulo="`¿Eliminar a ${aEliminar?.nombre} ${aEliminar?.apellido}?`"
      mensaje="No será posible si el huésped tiene reservas asociadas."
      @cancelar="aEliminar = null"
      @confirmar="eliminar"
    />
  </div>
</template>