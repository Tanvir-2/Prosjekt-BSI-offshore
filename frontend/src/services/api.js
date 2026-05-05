import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Auto-attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)


export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
}


export const searchApi = {
  search: (params) => api.get('/search', { params }),
  suggest: (params) => api.get('/search/suggest', { params }),
}


export const docsApi = {
  getMetadata: (id) => api.get(`/docs/${id}`),
  previewUrl: (id) => `/api/docs/${id}/preview?token=${localStorage.getItem('token')}`,
  downloadUrl: (id) => `/api/docs/${id}/download?token=${localStorage.getItem('token')}`,
}


export const adminApi = {
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deactivateUser: (id) => api.delete(`/admin/users/${id}`),
  activateUser: (id) => api.put(`/admin/users/${id}`, { is_active: true }),
  deleteUser: (id) => api.delete(`/admin/users/${id}/delete`),
  getConfig: () => api.get('/admin/config'),
  updateConfig: (data) => api.put('/admin/config', data),
  reindex: () => api.post('/admin/reindex'),
  getStats: () => api.get('/admin/stats'),
}

export default api
