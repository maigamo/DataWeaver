import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    userRole: localStorage.getItem('userRole') || ''
  }),

  actions: {
    setUserInfo(token: string, username: string, userRole: string) {
      this.token = token
      this.username = username
      this.userRole = userRole
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      localStorage.setItem('userRole', userRole)
    },

    clearUserInfo() {
      this.token = ''
      this.username = ''
      this.userRole = ''
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('userRole')
    }
  }
})