import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { API_ENDPOINTS } from '../config'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('auth_token') || '',
    user: null,
    loading: false
  }),
  getters: {
    isAuthenticated: state => !!state.token
  },
  actions: {
    async login(username, password) {
      this.loading = true
      try {
        const res = await fetch(`${API_ENDPOINTS.auth}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        })
        if (!res.ok) {
          throw new Error('登录失败')
        }
        const data = await res.json()
        this.token = data.access_token
        localStorage.setItem('auth_token', this.token)
        await this.fetchMe()
        ElMessage.success('登录成功')
      } catch (e) {
        ElMessage.error(e.message || '登录失败')
        this.logout()
      } finally {
        this.loading = false
      }
    },
    async register(username, password, displayName) {
      this.loading = true
      try {
        const res = await fetch(`${API_ENDPOINTS.auth}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username,
            password,
            display_name: displayName || null
          })
        })
        if (!res.ok) {
          const errorText = await res.text()
          throw new Error(errorText || '注册失败')
        }
        ElMessage.success('注册成功，请使用该账号登录')
      } catch (e) {
        ElMessage.error(e.message || '注册失败')
      } finally {
        this.loading = false
      }
    },
    async fetchMe() {
      if (!this.token) return
      const res = await fetch(`${API_ENDPOINTS.auth}/me`, {
        headers: { Authorization: `Bearer ${this.token}` }
      })
      if (!res.ok) {
        throw new Error('获取用户信息失败')
      }
      this.user = await res.json()
    },
    async init() {
      if (!this.token) return
      try {
        await this.fetchMe()
      } catch (e) {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('auth_token')
    }
  }
})
