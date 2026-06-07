import React, { useState, useEffect } from 'react'
import {
  customerOpsAPI, customersAPI, techniciansAPI, appointmentsAPI,
  getRiskLevelMeta, getMemberLevelMeta, getContactTypeLabel, CONTACT_TYPES
} from '../utils/api.js'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'

const RISK_COLORS = ['#10b981', '#f59e0b', '#ef4444']

export default function CustomerOpsPage() {
  const [highRiskList, setHighRiskList] = useState([])
  const [filterLevel, setFilterLevel] = useState('all')
  const [threshold, setThreshold] = useState(40)
  const [selected, setSelected] = useState(null)
  const [showContactModal, setShowContactModal] = useState(false)
  const [showApptModal, setShowApptModal] = useState(false)
  const [contactForm, setContactForm] = useState({ contact_type: 'wechat', content: '', operator: '' })
  const [apptForm, setApptForm] = useState({ technician: '', appointment_date: '', appointment_time: '' })
  const [technicians, setTechnicians] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
    techniciansAPI.list().then(r => setTechnicians(r.data.results || r.data))
  }, [threshold])

  const loadData = () => {
    setLoading(true)
    customerOpsAPI.highRisk(threshold).then(r => {
      setHighRiskList(r.data)
      setLoading(false)
    })
  }

  const filteredList = filterLevel === 'all'
    ? highRiskList
    : highRiskList.filter(c => c.risk_level === filterLevel)

  const openContactModal = (customer) => {
    setSelected(customer)
    setContactForm({
      contact_type: 'wechat',
      content: customer.scripts?.[0] || '',
      operator: ''
    })
    setShowContactModal(true)
  }

  const openApptModal = (customer) => {
    setSelected(customer)
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    setApptForm({
      technician: technicians[0]?.id || '',
      appointment_date: tomorrow.toISOString().slice(0, 10),
      appointment_time: '14:00:00'
    })
    setShowApptModal(true)
  }

  const submitContact = (e) => {
    e.preventDefault()
    customersAPI.addContact(selected.id, contactForm).then(() => {
      setShowContactModal(false)
      alert('跟进记录已创建！')
      loadData()
    })
  }

  const submitAppt = (e) => {
    e.preventDefault()
    customersAPI.createFollowupAppointment(selected.id, apptForm).then(() => {
      setShowApptModal(false)
      alert('预约草稿已创建！')
    })
  }

  const copyScript = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('话术已复制到剪贴板！')
    })
  }

  const stats = {
    total: highRiskList.length,
    high: highRiskList.filter(c => c.risk_level === 'high').length,
    medium: highRiskList.filter(c => c.risk_level === 'medium').length,
    low: highRiskList.filter(c => c.risk_level === 'low').length,
  }

  const distributionData = [
    { name: '低风险', value: stats.low },
    { name: '中风险', value: stats.medium },
    { name: '高风险', value: stats.high },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>🎯 客户运营</h2>
          <p className="text-gray">会员复购管理与流失预警，高风险顾客跟进与回访</p>
        </div>
        <div className="flex gap-10">
          <button className="btn btn-secondary" onClick={loadData}>🔄 重新计算风险评分</button>
        </div>
      </div>

      <div className="grid grid-4 mb-24">
        <div className="stat-card">
          <h3>风险顾客总数</h3>
          <div className="value">{stats.total}</div>
          <div className="sub">评分 ≥ {threshold} 分</div>
        </div>
        <div className="stat-card" style={{ borderLeftColor: '#ef4444' }}>
          <h3>🔴 高风险</h3>
          <div className="value" style={{ color: '#ef4444' }}>{stats.high}</div>
          <div className="sub">需紧急回访</div>
        </div>
        <div className="stat-card" style={{ borderLeftColor: '#f59e0b' }}>
          <h3>🟡 中风险</h3>
          <div className="value" style={{ color: '#f59e0b' }}>{stats.medium}</div>
          <div className="sub">建议两周内联系</div>
        </div>
        <div className="stat-card" style={{ borderLeftColor: '#10b981' }}>
          <h3>🟢 低风险</h3>
          <div className="value" style={{ color: '#10b981' }}>{stats.low}</div>
          <div className="sub">正常维护即可</div>
        </div>
      </div>

      <div className="grid grid-2 mb-24">
        <div className="chart-container">
          <h3 className="chart-title">风险分布</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={distributionData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {distributionData.map((_, i) => (
                  <Cell key={i} fill={RISK_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-container">
          <h3 className="chart-title">风险评分阈值设置</h3>
          <div className="mb-16">
            <div className="flex justify-between text-gray fs-13 mb-6">
              <span>仅显示评分 ≥</span>
              <span className="fw-700 text-pink-dark">{threshold} 分</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={threshold}
              onChange={e => setThreshold(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div className="flex justify-between text-lightgray fs-12 mt-4">
              <span>0</span><span>25</span><span>50</span><span>75</span><span>100</span>
            </div>
          </div>
          <div className="fs-13 text-gray lh-18">
            <p>📌 评分说明：</p>
            <p>• 最近到店时间（权重 35%）</p>
            <p>• 预约取消次数（权重 20%）</p>
            <p>• 满意度下降（权重 20%）</p>
            <p>• 偏好变化（权重 15%）</p>
            <p>• 作品维持时长（权重 10%）</p>
          </div>
        </div>
      </div>

      <div className="filter-bar">
        <span className="text-gray fs-14">筛选风险等级：</span>
        <div className="tabs" style={{ borderBottom: 'none', marginBottom: 0 }}>
          <button className={`tab ${filterLevel === 'all' ? 'active' : ''}`} onClick={() => setFilterLevel('all')}>全部</button>
          <button className={`tab ${filterLevel === 'high' ? 'active' : ''}`} onClick={() => setFilterLevel('high')}>🔴 高风险</button>
          <button className={`tab ${filterLevel === 'medium' ? 'active' : ''}`} onClick={() => setFilterLevel('medium')}>🟡 中风险</button>
          <button className={`tab ${filterLevel === 'low' ? 'active' : ''}`} onClick={() => setFilterLevel('low')}>🟢 低风险</button>
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><div className="icon">⏳</div><p>正在计算风险评分...</p></div>
      ) : filteredList.length > 0 ? (
        <div className="risk-card-grid">
          {filteredList.map(customer => {
            const riskMeta = getRiskLevelMeta(customer.risk_level)
            const levelMeta = getMemberLevelMeta(customer.member_level)
            return (
              <div key={customer.id} className="risk-card" style={{ borderTop: `4px solid ${riskMeta.color}` }}>
                <div className="flex justify-between items-start mb-12">
                  <div>
                    <div className="flex items-center gap-8 mb-4">
                      <h4 className="fs-16">{customer.name}</h4>
                      <span className="badge" style={{ background: levelMeta.color + '22', color: levelMeta.color }}>
                        {levelMeta.label}
                      </span>
                    </div>
                    <p className="text-gray fs-13">{customer.phone}</p>
                  </div>
                  <div className="text-right">
                    <div className="risk-score" style={{ color: riskMeta.color }}>
                      {customer.risk_score.toFixed(1)}
                    </div>
                    <span className={`badge ${riskMeta.cls}`}>{riskMeta.label}</span>
                  </div>
                </div>

                <div className="mb-12">
                  <div className="fs-12 text-gray mb-6">⚠️ 风险原因：</div>
                  <div className="flex gap-4 flex-wrap">
                    {customer.risk_reasons && customer.risk_reasons.length > 0 ? (
                      customer.risk_reasons.map((r, i) => (
                        <span key={i} className="risk-reason-tag">{r}</span>
                      ))
                    ) : (
                      <span className="text-lightgray fs-12">暂无</span>
                    )}
                  </div>
                </div>

                {customer.scripts && customer.scripts.length > 0 && (
                  <div className="mb-12">
                    <div className="fs-12 text-gray mb-6">💬 推荐回访话术：</div>
                    {customer.scripts.map((s, i) => (
                      <div key={i} className="script-bubble">
                        <span className="fs-13">{s}</span>
                        <button className="btn btn-sm btn-secondary" onClick={() => copyScript(s)}>📋 复制</button>
                      </div>
                    ))}
                  </div>
                )}

                {customer.recommended_action && (
                  <div className="mb-14">
                    <div className="fs-12 text-gray mb-4">📋 推荐动作：</div>
                    <p className="fs-13 text-pink-dark">{customer.recommended_action}</p>
                  </div>
                )}

                <div className="flex gap-8">
                  <button className="btn btn-primary btn-sm flex-1" onClick={() => openContactModal(customer)}>
                    ✍️ 创建跟进备注
                  </button>
                  <button className="btn btn-secondary btn-sm flex-1" onClick={() => openApptModal(customer)}>
                    📅 创建预约草稿
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="empty-state"><div className="icon">🎉</div><p>暂无风险顾客，继续保持！</p></div>
      )}

      {showContactModal && selected && (
        <div className="modal-overlay" onClick={() => setShowContactModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>创建跟进备注 - {selected.name}</h3>
              <button className="modal-close" onClick={() => setShowContactModal(false)}>×</button>
            </div>
            <form onSubmit={submitContact}>
              <div className="modal-body">
                <div className="form-group">
                  <label>联系方式</label>
                  <select className="select" value={contactForm.contact_type}
                    onChange={e => setContactForm({ ...contactForm, contact_type: e.target.value })}>
                    {CONTACT_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>联系内容</label>
                  <textarea className="textarea" rows="5" value={contactForm.content}
                    onChange={e => setContactForm({ ...contactForm, content: e.target.value })}
                    placeholder="请输入联系内容..." required />
                </div>
                <div className="form-group">
                  <label>操作人</label>
                  <input className="input" value={contactForm.operator}
                    onChange={e => setContactForm({ ...contactForm, operator: e.target.value })}
                    placeholder="请输入操作人姓名" />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowContactModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary">创建跟进记录</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showApptModal && selected && (
        <div className="modal-overlay" onClick={() => setShowApptModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>创建预约草稿 - {selected.name}</h3>
              <button className="modal-close" onClick={() => setShowApptModal(false)}>×</button>
            </div>
            <form onSubmit={submitAppt}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label>预约日期 *</label>
                    <input type="date" className="input" required value={apptForm.appointment_date}
                      onChange={e => setApptForm({ ...apptForm, appointment_date: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>预约时间 *</label>
                    <input type="time" className="input" required value={apptForm.appointment_time}
                      onChange={e => setApptForm({ ...apptForm, appointment_time: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>服务美甲师 *</label>
                  <select className="select" required value={apptForm.technician}
                    onChange={e => setApptForm({ ...apptForm, technician: e.target.value })}>
                    <option value="">请选择美甲师</option>
                    {technicians.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowApptModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary">创建预约草稿</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
