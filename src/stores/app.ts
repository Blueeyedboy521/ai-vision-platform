import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const isDarkMode = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  return {
    sidebarCollapsed,
    isDarkMode,
    toggleSidebar,
    toggleDarkMode
  }
})
