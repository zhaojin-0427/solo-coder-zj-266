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
  partialUpdate: (id, data) => api.patch(`/technicians/${id}/`, data),
  delete: (id) => api.delete(`/technicians/${id}/`),
}

export const customersAPI = {
  list: () => api.get('/customers/'),
  get: (id) => api.get(`/customers/${id}/`),
  create: (data) => api.post('/customers/', data),
  update: (id, data) => api.put(`/customers/${id}/`, data),
  partialUpdate: (id, data) => api.patch(`/customers/${id}/`, data),
  delete: (id) => api.delete(`/customers/${id}/`),
  preference: (id) => api.get(`/customers/${id}/preference/`),
  updatePreference: (id, data) => api.post(`/customers/${id}/update_preference/`, data),
  recommendations: (id) => api.get(`/customers/${id}/recommendations/`),
  churnRisk: (id) => api.get(`/customers/${id}/churn_risk/`),
  contactRecords: (id) => api.get(`/customers/${id}/contact_records/`),
  riskHistory: (id) => api.get(`/customers/${id}/risk_history/`),
  addContact: (id, data) => api.post(`/customers/${id}/add_contact/`, data),
  createFollowupAppointment: (id, data) => api.post(`/customers/${id}/create_followup_appointment/`, data),
}

export const contactRecordsAPI = {
  list: (params = {}) => api.get('/contact-records/', { params }),
  create: (data) => api.post('/contact-records/', data),
}

export const customerOpsAPI = {
  highRisk: (threshold = 40) => api.get('/customer-ops/high_risk/', { params: { threshold } }),
  recalculateAll: () => api.post('/customer-ops/recalculate_all/'),
}

export const styleTagsAPI = {
  list: () => api.get('/style-tags/'),
}

export const designsAPI = {
  list: (params = {}) => api.get('/designs/', { params }),
  get: (id) => api.get(`/designs/${id}/`),
  create: (data) => api.post('/designs/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/designs/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  partialUpdate: (id, data) => api.patch(`/designs/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/designs/${id}/`),
}

export const appointmentsAPI = {
  list: (params = {}) => api.get('/appointments/', { params }),
  get: (id) => api.get(`/appointments/${id}/`),
  create: (data) => api.post('/appointments/', data),
  update: (id, data) => api.put(`/appointments/${id}/`, data),
  partialUpdate: (id, data) => api.patch(`/appointments/${id}/`, data),
  delete: (id) => api.delete(`/appointments/${id}/`),
}

export const worksAPI = {
  list: (params = {}) => api.get('/works/', { params }),
  get: (id) => api.get(`/works/${id}/`),
  create: (data) => api.post('/works/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/works/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  partialUpdate: (id, data) => api.patch(`/works/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/works/${id}/`),
}

export const statisticsAPI = {
  overview: () => api.get('/statistics/overview/'),
  colorRanking: (months = 6) => api.get('/statistics/color_ranking/', { params: { months } }),
  designLifecycle: () => api.get('/statistics/design_lifecycle/'),
  preferenceTrend: (months = 6) => api.get('/statistics/preference_trend/', { params: { months } }),
  technicianEfficiency: (months = 3) => api.get('/statistics/technician_efficiency/', { params: { months } }),
  memberLevelDistribution: () => api.get('/statistics/member_level_distribution/'),
  repurchaseInterval: () => api.get('/statistics/repurchase_interval/'),
  churnRiskTrend: (months = 6) => api.get('/statistics/churn_risk_trend/', { params: { months } }),
}

export const MEMBER_LEVELS = [
  { value: 'normal', label: '普通会员', color: '#9ca3af' },
  { value: 'silver', label: '银卡会员', color: '#6b7280' },
  { value: 'gold', label: '金卡会员', color: '#f59e0b' },
  { value: 'platinum', label: '钻石会员', color: '#8b5cf6' },
]

export const CONTACT_TYPES = [
  { value: 'phone', label: '电话' },
  { value: 'wechat', label: '微信' },
  { value: 'sms', label: '短信' },
  { value: 'visit', label: '到店' },
  { value: 'other', label: '其他' },
]

export const RISK_LEVELS = {
  low: { label: '低风险', color: '#10b981', cls: 'badge-completed' },
  medium: { label: '中风险', color: '#f59e0b', cls: 'badge-pending' },
  high: { label: '高风险', color: '#ef4444', cls: 'badge-cancelled' },
}

export const getMemberLevelMeta = (v) => MEMBER_LEVELS.find(m => m.value === v) || MEMBER_LEVELS[0]
export const getRiskLevelMeta = (v) => RISK_LEVELS[v] || RISK_LEVELS.low
export const getContactTypeLabel = (v) => CONTACT_TYPES.find(c => c.value === v)?.label || v

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
