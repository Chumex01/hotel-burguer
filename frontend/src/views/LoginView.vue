<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const usuario = ref('')
const password = ref('')
const verPassword = ref(false)
const cargando = ref(false)
const error = ref('')
const sacudir = ref(false)

async function ingresar() {
  if (!usuario.value || !password.value) {
    dispararError('Completa usuario y contraseña')
    return
  }

  cargando.value = true
  error.value = ''
  try {
    await auth.login(usuario.value, password.value)
    toast.show(`¡Bienvenido, ${auth.user.nombre}!`)
    router.push('/')
  } catch (e) {
    dispararError(e.response?.data?.detail || 'Usuario o contraseña incorrectos')
  } finally {
    cargando.value = false
  }
}

function dispararError(mensaje) {
  error.value = mensaje
  sacudir.value = true
  setTimeout(() => (sacudir.value = false), 500)
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-900 px-4">
    <!-- Fondo decorativo -->
    <div class="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-amber-500/20 blur-3xl" />
    <div class="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-sky-500/20 blur-3xl" />

    <div
      class="relative w-full max-w-md"
      :class="{ 'animate-shake': sacudir }"
    >
      <div class="rounded-3xl border border-white/10 bg-slate-800/60 p-8 shadow-2xl backdrop-blur-xl">
        <!-- Logo -->
        <div class="mb-8 text-center">
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-3xl shadow-lg shadow-amber-500/40">
            🏨
          </div>
          <h1 class="text-2xl font-bold text-white">HotelSys</h1>
          <p class="mt-1 text-sm text-slate-400">Inicia sesión para continuar</p>
        </div>

        <!-- Error -->
        <Transition
          enter-active-class="transition duration-200"
          enter-from-class="opacity-0 -translate-y-1"
        >
          <div v-if="error" class="mb-4 flex items-center gap-2 rounded-xl bg-rose-500/15 px-4 py-3 text-sm text-rose-300">
            <span>⚠️</span> {{ error }}
          </div>
        </Transition>

        <form @submit.prevent="ingresar" class="space-y-5">
          <div>
            <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-400">Usuario</label>
            <input
              v-model="usuario"
              type="text"
              autocomplete="username"
              placeholder="admin"
              class="w-full rounded-xl border border-slate-600/50 bg-slate-700/50 px-4 py-3 text-white placeholder-slate-500 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30"
            />
          </div>

          <div>
            <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-400">Contraseña</label>
            <div class="relative">
              <input
                v-model="password"
                :type="verPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                class="w-full rounded-xl border border-slate-600/50 bg-slate-700/50 px-4 py-3 pr-12 text-white placeholder-slate-500 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30"
              />
              <button
                type="button"
                @click="verPassword = !verPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-white"
              >
                {{ verPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <button
            type="submit"
            :disabled="cargando"
            class="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 py-3 font-semibold text-white shadow-lg shadow-amber-500/30 transition-all hover:shadow-amber-500/50 hover:brightness-110 active:scale-[0.98] disabled:opacity-60"
          >
            <svg v-if="cargando" class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ cargando ? 'Ingresando...' : 'Ingresar' }}
          </button>
        </form>
      </div>

      <p class="mt-6 text-center text-xs text-slate-500">Sistema de Gestión Hotelera © 2026</p>
    </div>
  </div>
</template>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}
.animate-shake { animation: shake 0.4s ease; }
</style>