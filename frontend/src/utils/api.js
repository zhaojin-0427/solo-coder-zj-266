import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export default api

export const techniciansAPI = {
  list: () => api.get('/technicians/'),
  get: (id) => api.get(`/technicians/${id}/`),
  create: (data) => api.post('/technicians/', data),
  update: (id, data) => api.put(`/technicians/${id}/`, data),
  delete: (id) => api.delete(`/technicians/${id}/`),
}

export const customersAPI = {
  list: () => api.get('/customers/'),
  get: (id) => api.get(`/customers/${id}/`),
  create: (data) => api.post('/customers/', data),
  update: (id, data) => api.put(`/customers/${id}/`, data),
  delete: (id) => api.delete(`/customers/${id}/`),
  preference: (id) => api.get(`/customers/${id}/preference/`),
  updatePreference: (id, data) => api.post(`/customers/${id}/update_preference/`, data),
  recommendations: (id) => api.get(`/customers/${id}/recommendations/`),
}

export const styleTagsAPI = {
  list: () => api.get('/style-tags/'),
}

export const designsAPI = {
  list: (params = {}) => api.get('/designs/', { params }),
  get: (id) => api.get(`/designs/${id}/`),
  create: (data) => api.post('/designs/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/designs/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/designs/${id}/`),
}

export const appointmentsAPI = {
  list: (params = {}) => api.get('/appointments/', { params }),
  get: (id) => api.get(`/appointments/${id}/`),
  create: (data) => api.post('/appointments/', data),
  update: (id, data) => api.put(`/appointments/${id}/`, data),
  delete: (id) => api.delete(`/appointments/${id}/`),
}

export const worksAPI = {
  list: (params = {}) => api.get('/works/', { params }),
  get: (id) => api.get(`/works/${id}/`),
  create: (data) => api.post('/works/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/works/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/works/${id}/`),
}

export const statisticsAPI = {
  overview: () => api.get('/statistics/overview/'),
  colorRanking: (months = 6) => api.get('/statistics/color_ranking/', { params: { months } }),
  designLifecycle: () => api.get('/statistics/design_lifecycle/'),
  preferenceTrend: (months = 6) => api.get('/statistics/preference_trend/', { params: { months } }),
  technicianEfficiency: (months = 3) => api.get('/statistics/technician_efficiency/', { params: { months } }),
}

export const NAIL_SHAPES = [
  { value: 'oval', label: '椭圆形' },
  { value: 'square', label: '方形' },
  { value: 'squoval', label: '方圆形' },
  { value: 'almond', label: '杏仁形' },
  { value: 'stiletto', label: '尖形' },
  { value: 'coffin', label: '棺材形' },
  { value: 'ballerina', label: '芭蕾舞形' },
  { value: 'round', label: '圆形' },
]

export const OCCASIONS = [
  { value: 'daily', label: '日常' },
  { value: 'wedding', label: '婚礼' },
  { value: 'party', label: '派对' },
  { value: 'office', label: '职场' },
  { value: 'festival', label: '节日' },
  { value: 'travel', label: '旅行' },
  { value: 'date', label: '约会' },
]

export const APPOINTMENT_STATUS = [
  { value: 'pending', label: '待确认', cls: 'badge-pending' },
  { value: 'confirmed', label: '已确认', cls: 'badge-confirmed' },
  { value: 'in_progress', label: '进行中', cls: 'badge-in_progress' },
  { value: 'completed', label: '已完成', cls: 'badge-completed' },
  { value: 'cancelled', label: '已取消', cls: 'badge-cancelled' },
]

export const SEASONS = {
  spring: '春季',
  summer: '夏季',
  autumn: '秋季',
  winter: '冬季',
}

export const renderStars = (n) => {
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}

export const getShapeLabel = (v) => NAIL_SHAPES.find(s => s.value === v)?.label || v
export const getOccasionLabel = (v) => OCCASIONS.find(s => s.value === v)?.label || v
export const getStatusMeta = (v) => APPOINTMENT_STATUS.find(s => s.value === v) || { label: v, cls: '' }
