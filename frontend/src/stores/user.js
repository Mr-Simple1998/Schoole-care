import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isPlatform: (state) => state.user?.role === 'platform',
    isPrincipal: (state) => state.user?.role === 'principal',
    isSubPrincipal: (state) => state.user?.role === 'sub_principal' || state.user?.role === 'campus_head',
    isTeacher: (state) => state.user?.role === 'teacher',
    isCampusHead: (state) => state.user?.role === 'campus_head',
  },
  actions: {
    async login(username, password) {
      const body = new URLSearchParams()
      body.append('username', username)
      body.append('password', password)
      const data = await request.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return data
    },
    async fetchMe() {
      const data = await request.get('/auth/me')
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
