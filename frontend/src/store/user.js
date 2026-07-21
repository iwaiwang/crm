import { defineStore } from 'pinia'
import { ref } from 'vue'

export function normalizeUser(rawUser) {
  if (!rawUser || typeof rawUser !== 'object') {
    return null
  }

  let menuPermissions = rawUser.menu_permissions
  if (typeof menuPermissions === 'string') {
    try {
      menuPermissions = JSON.parse(menuPermissions)
    } catch (error) {
      menuPermissions = []
    }
  }

  return {
    ...rawUser,
    menu_permissions: Array.isArray(menuPermissions) ? menuPermissions : [],
  }
}

function readStoredUser() {
  try {
    return normalizeUser(JSON.parse(localStorage.getItem('user') || 'null'))
  } catch (error) {
    localStorage.removeItem('user')
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(readStoredUser())

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(newUser) {
    const normalizedUser = normalizeUser(newUser)
    user.value = normalizedUser
    localStorage.setItem('user', JSON.stringify(normalizedUser))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
    setToken,
    setUser,
    logout,
  }
})
