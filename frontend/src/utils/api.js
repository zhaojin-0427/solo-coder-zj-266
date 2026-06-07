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

export const tryOnAPI = {
  list: (params = {}) => api.get('/try-on-tasks/', { params }),
  get: (id) => api.get(`/try-on-tasks/${id}/`),
  create: (data) => api.post('/try-on-tasks/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/try-on-tasks/${id}/`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  partialUpdate: (id, data) => api.patch(`/try-on-tasks/${id}/`, data),
  delete: (id) => api.delete(`/try-on-tasks/${id}/`),
  reprocess: (id) => api.post(`/try-on-tasks/${id}/reprocess/`),
  recommendations: (id) => api.get(`/try-on-tasks/${id}/recommendations/`),
  logClick: (id, data) => api.post(`/try-on-tasks/${id}/log_click/`, data),
  createAppointmentDraft: (id, data) => api.post(`/try-on-tasks/${id}/create_appointment_draft/`, data),
  myHistory: (customerId) => api.get('/try-on-tasks/my_history/', { params: { customer: customerId } }),
}

export const designClicksAPI = {
  list: (params = {}) => api.get('/design-clicks/', { params }),
  create: (data) => api.post('/design-clicks/', data),
}

export const tryOnStatisticsAPI = {
  conversionOverview: (months = 6) => api.get('/try-on-statistics/conversion_overview/', { params: { months } }),
  conversionTrend: (months = 6) => api.get('/try-on-statistics/conversion_trend/', { params: { months } }),
  similarDesignRanking: (months = 3, limit = 10) => api.get('/try-on-statistics/similar_design_ranking/', { params: { months, limit } }),
  skinTonePreference: (months = 6) => api.get('/try-on-statistics/skin_tone_preference/', { params: { months } }),
  handShapePreference: (months = 6) => api.get('/try-on-statistics/hand_shape_preference/', { params: { months } }),
}

export const SKIN_TONES = [
  { value: 'fair', label: '冷白肤色' },
  { value: 'light', label: '白皙肤色' },
  { value: 'medium', label: '自然肤色' },
  { value: 'tan', label: '小麦肤色' },
  { value: 'dark', label: '健康肤色' },
]

export const HAND_SHAPES = [
  { value: 'slender', label: '纤细修长型' },
  { value: 'standard', label: '标准匀称型' },
  { value: 'plump', label: '丰满圆润型' },
  { value: 'broad', label: '宽厚有力型' },
]

export const NAIL_LENGTHS = [
  { value: 'very_short', label: '超短（<1mm）' },
  { value: 'short', label: '短（1-3mm）' },
  { value: 'medium', label: '中（3-6mm）' },
  { value: 'long', label: '长（6-10mm）' },
  { value: 'very_long', label: '超长（>10mm）' },
]

export const BUDGETS = [
  { value: 'low', label: '平价（100元以下）' },
  { value: 'medium', label: '中档（100-300元）' },
  { value: 'high', label: '高档（300-600元）' },
  { value: 'luxury', label: '奢华（600元以上）' },
]

export const TRYON_STATUS = [
  { value: 'pending', label: '待处理', cls: 'badge-pending' },
  { value: 'processing', label: '识别中', cls: 'badge-in_progress' },
  { value: 'completed', label: '已完成', cls: 'badge-completed' },
  { value: 'failed', label: '失败', cls: 'badge-cancelled' },
]

export const COLOR_PALETTE = [
  '粉色系', '裸色系', '黑色系', '蓝色系', '白色系', '棕色系',
  '紫色系', '绿色系', '红色系', '奶茶色系', '灰色系', '橘色系',
  '玫瑰色', '酒红色', '焦糖色', '墨绿色', '金黄色', '闪钻系',
]

export const getSkinToneLabel = (v) => SKIN_TONES.find(s => s.value === v)?.label || v
export const getHandShapeLabel = (v) => HAND_SHAPES.find(s => s.value === v)?.label || v
export const getNailLengthLabel = (v) => NAIL_LENGTHS.find(s => s.value === v)?.label || v
export const getBudgetLabel = (v) => BUDGETS.find(s => s.value === v)?.label || v
export const getTryOnStatusMeta = (v) => TRYON_STATUS.find(s => s.value === v) || { label: v, cls: '' }

export const renderStars = (n) => {
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}

export const getShapeLabel = (v) => NAIL_SHAPES.find(s => s.value === v)?.label || v
export const getOccasionLabel = (v) => OCCASIONS.find(s => s.value === v)?.label || v
export const getStatusMeta = (v) => APPOINTMENT_STATUS.find(s => s.value === v) || { label: v, cls: '' }
