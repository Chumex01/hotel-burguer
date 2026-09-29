import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function show(mensaje, tipo = 'success') {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, mensaje, tipo })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 4000)
  }

  return { toasts, show }
})