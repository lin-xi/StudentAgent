import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useLearningStore } from "./learning.js"



export const useUserStore = defineStore('user', () => {
  const currentUser = ref(null)
  const isAuthenticated = ref(false)

  async function checkAuth() {
    try {
      if (currentUser.value) {
        return true
      } else {
        const res = await fetch('/api/me')
        const data = await res.json()
        if (data.data.user_id) {
          currentUser.value = data.data
          isAuthenticated.value = true

          const learningStore = useLearningStore();
          console.log("checkAuth>>>", "获取用户信息", data.data);

          learningStore.setSelectedSubject({ id: data.data.subject_id, name: data.data.subject });
          learningStore.setGrade({ id: data.data.grade_id, name: data.data.grade });

          return true
        }
      }
    } catch (e) {
      console.error('检查登录状态失败:', e)
    }
    currentUser.value = null
    isAuthenticated.value = false
    return false
  }

  function setAuth(userData) {
    currentUser.value = userData
    isAuthenticated.value = true
  }

  function getUser() {
    return currentUser.value
  }

  function clearAuth() {
    currentUser.value = null
    isAuthenticated.value = false
  }

  return {
    currentUser,
    isAuthenticated,
    checkAuth,
    setAuth,
    getUser,
    clearAuth,
  }
})
