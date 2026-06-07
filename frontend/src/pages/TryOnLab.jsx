import React, { useState, useEffect } from 'react'
import {
  tryOnAPI, customersAPI, worksAPI, designsAPI, appointmentsAPI,
  OCCASIONS, NAIL_SHAPES, COLOR_PALETTE, BUDGETS, getOccasionLabel,
  getShapeLabel, getBudgetLabel, getSkinToneLabel, getHandShapeLabel,
  getNailLengthLabel, getTryOnStatusMeta, getStatusMeta, renderStars
} from '../utils/api.js'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'

const SCORE_COLORS = ['#ec4899', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#6366f1']

export default function TryOnLab() {
  const [tab, setTab] = useState('create')
  const [customers, setCustomers] = useState([])
  const [customerWorks, setCustomerWorks] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [photoFile, setPhotoFile] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)
  const [useReferenceWork, setUseReferenceWork] = useState(false)
  const [selectedWork, setSelectedWork] = useState(null)
  const [targetOccasion, setTargetOccasion] = useState('')
  const [budget, setBudget] = useState('')
  const [preferredColors, setPreferredColors] = useState([])
  const [submitting, setSubmitting] = useState(false)

  const [taskList, setTaskList] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [compareItems, setCompareItems] = useState([])
  const [showCompare, setShowCompare] = useState(false)
  const [showAppointmentModal, setShowAppointmentModal] = useState(false)
  const [appointmentDesign, setAppointmentDesign] = useState(null)
  const [appointmentForm, setAppointmentForm] = useState({
    appointment_date: '', appointment_time: '14:00', technician_id: '', notes: ''
  })
  const [technicians, setTechnicians] = useState([])

  const [filterCustomer, setFilterCustomer] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSimMin, setFilterSimMin] = useState('')
  const [filterSimMax, setFilterSimMax] = useState('')

  useEffect(() => {
    loadCustomers()
    loadTaskList()
    import('../utils/api.js').then(m => {
      m.techniciansAPI.list().then(r => setTechnicians(r.data.results || r.data))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (filterCustomer || filterStatus || filterSimMin || filterSimMax) {
      loadTaskList()
    }
  }, [filterCustomer, filterStatus, filterSimMin, filterSimMax])

  const loadCustomers = () => {
    customersAPI.list().then(r => setCustomers(r.data.results || r.data))
  }

  const loadTaskList = () => {
    const params = {}
    if (filterCustomer) params.customer = filterCustomer
    if (filterStatus) params.status = filterStatus
    if (filterSimMin) params.sim_min = filterSimMin
    if (filterSimMax) params.sim_max = filterSimMax
    tryOnAPI.list(params).then(r => setTaskList(r.data.results || r.data))
  }

  const handleCustomerSelect = (c) => {
    setSelectedCustomer(c)
    if (c) {
      worksAPI.list({ customer: c.id }).then(r => setCustomerWorks(r.data.results || r.data))
    } else {
      setCustomerWorks([])
      setSelectedWork(null)
    }
  }

  const handlePhotoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setPhotoFile(file)
      const reader = new FileReader()
      reader.onload = (ev) => setPhotoPreview(ev.target.result)
      reader.readAsDataURL(file)
      setUseReferenceWork(false)
      setSelectedWork(null)
    }
  }

  const toggleColor = (c) => {
    setPreferredColors(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedCustomer) {
      alert('请先选择顾客')
      return
    }
    if (!photoFile && !useReferenceWork) {
      alert('请上传手部照片或选择历史作品')
      return
    }
    setSubmitting(true)
    try {
      const fd = new FormData()
      fd.append('customer', selectedCustomer.id)
      fd.append('target_occasion', targetOccasion)
      fd.append('budget', budget)
      fd.append('preferred_colors', preferredColors.join(', '))
      if (photoFile && !useReferenceWork) {
        fd.append('photo', photoFile)
      }
      if (useReferenceWork && selectedWork) {
        fd.append('reference_work', selectedWork.id)
      }
      const res = await tryOnAPI.create(fd)
      setSubmitting(false)
      alert('试甲任务创建成功，正在分析...')
      setTimeout(() => {
        tryOnAPI.get(res.data.id).then(r => {
          setSelectedTask(r.data)
          setRecommendations(r.data.similar_results || [])
          setTab('result')
        })
        loadTaskList()
      }, 500)
    } catch (err) {
      setSubmitting(false)
      alert('创建失败：' + (err.response?.data?.detail || err.message))
    }
  }

  const selectTask = (task) => {
    setSelectedTask(task)
    tryOnAPI.recommendations(task.id).then(r => {
      setRecommendations(r.data.results || r.data)
    })
    setTab('result')
  }

  const handleLogClick = (designId, clickType = 'view') => {
    if (!selectedTask) return
    tryOnAPI.logClick(selectedTask.id, { design_id: designId, click_type: clickType })
  }

  const toggleCompare = (rec) => {
    setCompareItems(prev => {
      if (prev.find(p => p.id === rec.id)) {
        return prev.filter(p => p.id !== rec.id)
      }
      if (prev.length >= 3) {
        alert('最多对比3个款式')
        return prev
      }
      handleLogClick(rec.design_id, 'compare')
      return [...prev, rec]
    })
  }

  const openAppointment = (rec) => {
    handleLogClick(rec.design_id, 'book')
    setAppointmentDesign(rec)
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    setAppointmentForm({
      appointment_date: tomorrow.toISOString().slice(0, 10),
      appointment_time: '14:00',
      technician_id: technicians[0]?.id || '',
      notes: `[试甲转化] 来自试甲任务#${selectedTask?.id}，相似度评分：${rec.similarity_score}`
    })
    setShowAppointmentModal(true)
  }

  const handleCreateAppointment = async () => {
    if (!selectedTask) return
    try {
      const res = await tryOnAPI.createAppointmentDraft(selectedTask.id, {
        design_id: appointmentDesign?.design_id
      })
      if (appointmentForm.appointment_date) {
        await appointmentsAPI.partialUpdate(res.data.id, appointmentForm)
      }
      setShowAppointmentModal(false)
      alert('预约草稿创建成功！')
      loadTaskList()
      tryOnAPI.get(selectedTask.id).then(r => setSelectedTask(r.data))
    } catch (err) {
      alert('创建失败：' + (err.response?.data?.error || err.message))
    }
  }

  const renderAnalysisCard = () => {
    if (!selectedTask) return null
    const t = selectedTask
    const statusMeta = getTryOnStatusMeta(t.status)
    return (
      <div className="card mb-20">
        <div className="flex justify-between items-center mb-14">
          <h3 className="fs-16 fw-600">🔍 视觉识别结果</h3>
          <span className={`badge ${statusMeta.cls}`}>{statusMeta.label}</span>
        </div>
        <div className="grid grid-4 mb-14">
          <div className="bg-lightpink pad-8 radius-6">
            <div className="fs-12 text-gray mb-4">识别肤色</div>
            <div className="fs-16 fw-600 text-pink-dark">{t.skin_tone_display || '-'}</div>
          </div>
          <div className="bg-lightpink pad-8 radius-6">
            <div className="fs-12 text-gray mb-4">识别手型</div>
            <div className="fs-16 fw-600 text-pink-dark">{t.hand_shape_display || '-'}</div>
          </div>
          <div className="bg-lightpink pad-8 radius-6">
            <div className="fs-12 text-gray mb-4">指甲长度</div>
            <div className="fs-16 fw-600 text-pink-dark">{t.nail_length_display || '-'}</div>
          </div>
          <div className="bg-lightpink pad-8 radius-6">
            <div className="fs-12 text-gray mb-4">置信度</div>
            <div className="fs-16 fw-600 text-pink-dark">{t.analysis_details?.confidence || '-'}%</div>
          </div>
        </div>
        {(t.target_occasion_display || t.budget_display || t.preferred_colors) && (
          <div className="flex gap-10 flex-wrap">
            {t.target_occasion_display && <span className="tag-chip" style={{ background: '#8b5cf6' }}>场合：{t.target_occasion_display}</span>}
            {t.budget_display && <span className="tag-chip" style={{ background: '#06b6d4' }}>预算：{t.budget_display}</span>}
            {t.preferred_colors && t.preferred_colors.split(',').filter(Boolean).map((c, i) => (
              <span key={i} className="tag-chip" style={{ background: '#10b981' }}>{c.trim()}</span>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderRecommendations = () => {
    if (!recommendations || recommendations.length === 0) {
      return (
        <div className="card">
          <div className="empty-state">
            <div className="icon">💅</div>
            <p>暂无推荐结果</p>
          </div>
        </div>
      )
    }
    return (
      <div>
        <div className="flex justify-between items-center mb-14">
          <h3 className="fs-16 fw-600">✨ 相似款式推荐（{recommendations.length}个）</h3>
          {compareItems.length > 0 && (
            <button className="btn btn-sm btn-secondary" onClick={() => setShowCompare(true)}>
              📊 对比选中 ({compareItems.length})
            </button>
          )}
        </div>
        <div className="design-grid">
          {recommendations.map(rec => {
            const d = rec.design_data || {}
            const inCompare = compareItems.find(p => p.id === rec.id)
            return (
              <div key={rec.id} className="design-card" onClick={() => handleLogClick(d.id, 'view')}>
                <div className="design-image">
                  {d.image ? <img src={d.image} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt={d.name} /> : '💅'}
                  <div style={{ position: 'absolute', top: 8, left: 8, display: 'flex', gap: 4 }}>
                    <span style={{ background: 'rgba(236,72,153,0.95)', color: 'white', padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                      TOP {rec.rank} · {rec.similarity_score}分
                    </span>
                  </div>
                </div>
                <div className="design-info">
                  <h4>{d.name}</h4>
                  <div className="design-meta">
                    {d.style_tags_data?.map((t, i) => (
                      <span key={i} className="tag-chip" style={{ background: t.color || '#ec4899' }}>{t.name}</span>
                    ))}
                    <span className="tag-chip" style={{ background: '#6366f1' }}>{getShapeLabel(d.nail_shape)}</span>
                    <span className="tag-chip" style={{ background: '#06b6d4' }}>{getOccasionLabel(d.occasion)}</span>
                  </div>
                  <div className="fs-13 text-gray mb-8">{d.color_system} · {d.decoration}</div>
                  <div style={{ marginBottom: 8 }}>
                    <ResponsiveContainer width="100%" height={80}>
                      <RadarChart data={[
                        { subject: '甲型', A: rec.shape_score || 0 },
                        { subject: '色系', A: rec.color_score || 0 },
                        { subject: '装饰', A: rec.decoration_score || 0 },
                        { subject: '风格', A: rec.style_score || 0 },
                        { subject: '场合', A: rec.occasion_score || 0 },
                        { subject: '预算', A: rec.budget_score || 0 },
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis domain={[0, 100]} tick={false} />
                        <Radar name="匹配度" dataKey="A" stroke="#ec4899" fill="#ec4899" fillOpacity={0.4} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="design-footer">
                    <span className="price">¥{d.price}</span>
                    <div className="flex gap-6">
                      <button
                        className={`btn btn-sm ${inCompare ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={(e) => { e.stopPropagation(); toggleCompare(rec) }}
                      >{inCompare ? '已选' : '对比'}</button>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={(e) => { e.stopPropagation(); openAppointment(rec) }}
                      >预约</button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderCompareModal = () => {
    if (!showCompare || compareItems.length < 2) return null
    const chartData = compareItems.map(rec => ({
      name: (rec.design_data?.name || '').slice(0, 6),
      甲型: rec.shape_score || 0,
      色系: rec.color_score || 0,
      装饰: rec.decoration_score || 0,
      风格: rec.style_score || 0,
      场合: rec.occasion_score || 0,
      预算: rec.budget_score || 0,
    }))
    return (
      <div className="modal-overlay" onClick={() => setShowCompare(false)}>
        <div className="modal" style={{ maxWidth: 900 }} onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📊 款式对比分析</h3>
            <button className="modal-close" onClick={() => setShowCompare(false)}>×</button>
          </div>
          <div className="modal-body">
            <div className="chart-container mb-20">
              <h4 className="chart-title">各维度匹配度对比</h4>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  {['甲型', '色系', '装饰', '风格', '场合', '预算'].map((k, i) => (
                    <Bar key={k} dataKey={k} fill={SCORE_COLORS[i % SCORE_COLORS.length]} radius={[4, 4, 0, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="grid" style={{ gridTemplateColumns: `repeat(${compareItems.length}, 1fr)` }}>
              {compareItems.map(rec => {
                const d = rec.design_data || {}
                return (
                  <div key={rec.id} className="card">
                    <div className="design-image" style={{ borderRadius: 10, marginBottom: 12 }}>
                      {d.image ? <img src={d.image} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }} alt={d.name} /> : '💅'}
                    </div>
                    <h4 className="fs-15 fw-600 mb-6">{d.name}</h4>
                    <div className="fs-13 text-gray mb-8">{d.color_system} · {getShapeLabel(d.nail_shape)}</div>
                    <ul className="info-list">
                      <li><span className="label">综合相似度</span><span className="val text-pink fw-700">{rec.similarity_score}分</span></li>
                      <li><span className="label">甲型匹配</span><span className="val">{rec.shape_score}分</span></li>
                      <li><span className="label">色系匹配</span><span className="val">{rec.color_score}分</span></li>
                      <li><span className="label">装饰匹配</span><span className="val">{rec.decoration_score}分</span></li>
                      <li><span className="label">风格匹配</span><span className="val">{rec.style_score}分</span></li>
                      <li><span className="label">场合匹配</span><span className="val">{rec.occasion_score}分</span></li>
                      <li><span className="label">预算匹配</span><span className="val">{rec.budget_score}分</span></li>
                      <li><span className="label">参考价格</span><span className="val text-pink fw-600">¥{d.price}</span></li>
                    </ul>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowCompare(false)}>关闭</button>
            <button className="btn btn-primary" onClick={() => {
              const best = [...compareItems].sort((a, b) => b.similarity_score - a.similarity_score)[0]
              setShowCompare(false)
              openAppointment(best)
            }}>用最高分款式生成预约</button>
          </div>
        </div>
      </div>
    )
  }

  const renderAppointmentModal = () => {
    if (!showAppointmentModal || !appointmentDesign) return null
    const d = appointmentDesign.design_data || {}
    return (
      <div className="modal-overlay" onClick={() => setShowAppointmentModal(false)}>
        <div className="modal" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📅 生成预约草稿</h3>
            <button className="modal-close" onClick={() => setShowAppointmentModal(false)}>×</button>
          </div>
          <div className="modal-body">
            <div className="recommendation-item mb-20">
              <div className="rec-image">
                {d.image ? <img src={d.image} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8 }} alt={d.name} /> : '💅'}
              </div>
              <div className="flex-1">
                <h5>{d.name}</h5>
                <p>{d.color_system} · {getShapeLabel(d.nail_shape)} · {getOccasionLabel(d.occasion)}</p>
                <p>相似度评分：<span className="text-pink fw-700">{appointmentDesign.similarity_score}分</span></p>
              </div>
              <div className="text-pink fw-700 fs-20">¥{d.price}</div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>预约日期</label>
                <input type="date" className="input" value={appointmentForm.appointment_date}
                  onChange={e => setAppointmentForm({ ...appointmentForm, appointment_date: e.target.value })} />
              </div>
              <div className="form-group">
                <label>预约时间</label>
                <input type="time" className="input" value={appointmentForm.appointment_time}
                  onChange={e => setAppointmentForm({ ...appointmentForm, appointment_time: e.target.value })} />
              </div>
            </div>
            <div className="form-group">
              <label>美甲师</label>
              <select className="select" value={appointmentForm.technician_id}
                onChange={e => setAppointmentForm({ ...appointmentForm, technician_id: e.target.value })}>
                {technicians.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>备注</label>
              <textarea className="textarea" rows="3" value={appointmentForm.notes}
                onChange={e => setAppointmentForm({ ...appointmentForm, notes: e.target.value })} />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowAppointmentModal(false)}>取消</button>
            <button className="btn btn-primary" onClick={handleCreateAppointment}>确认生成预约草稿</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>✨ 试甲实验室</h2>
          <p className="text-gray">AI 视觉试甲与款式相似检索，上传照片获取个性化推荐</p>
        </div>
      </div>

      <div className="tabs mb-24">
        <button className={`tab ${tab === 'create' ? 'active' : ''}`} onClick={() => { setTab('create'); setSelectedTask(null); setCompareItems([]) }}>🆕 新建试甲</button>
        <button className={`tab ${tab === 'result' ? 'active' : ''}`} onClick={() => setTab('result')}>🎯 试甲结果</button>
        <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>📋 历史任务</button>
      </div>

      {tab === 'create' && (
        <div className="grid grid-2">
          <div className="card">
            <h3 className="fs-16 fw-600 mb-16">📷 上传手部照片 / 选择历史作品</h3>

            <div className="form-group">
              <label>选择顾客 *</label>
              <select className="select" value={selectedCustomer?.id || ''}
                onChange={e => {
                  const c = customers.find(x => x.id == e.target.value)
                  handleCustomerSelect(c || null)
                }}>
                <option value="">请选择顾客</option>
                {customers.map(c => <option key={c.id} value={c.id}>{c.name} ({c.phone})</option>)}
              </select>
            </div>

            <div className="flex gap-10 mb-14">
              <button className={`btn btn-sm ${!useReferenceWork ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => { setUseReferenceWork(false); setSelectedWork(null) }}>📷 上传照片</button>
              <button className={`btn btn-sm ${useReferenceWork ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => { setUseReferenceWork(true); setPhotoFile(null); setPhotoPreview(null) }}>📁 历史作品</button>
            </div>

            {!useReferenceWork && (
              <div className="form-group">
                <label>上传手部照片</label>
                <input type="file" accept="image/*" className="input" onChange={handlePhotoChange} />
                {photoPreview && (
                  <div style={{ marginTop: 12, width: '100%', height: 200, background: '#fdf2f8', borderRadius: 10, overflow: 'hidden' }}>
                    <img src={photoPreview} style={{ width: '100%', height: '100%', objectFit: 'contain' }} alt="preview" />
                  </div>
                )}
              </div>
            )}

            {useReferenceWork && (
              <div className="form-group">
                <label>选择历史作品</label>
                {customerWorks.length > 0 ? (
                  <div className="grid grid-3 gap-10">
                    {customerWorks.map(w => (
                      <div key={w.id} onClick={() => setSelectedWork(w)}
                        style={{
                          padding: 10, borderRadius: 10, cursor: 'pointer',
                          border: selectedWork?.id === w.id ? '2px solid #ec4899' : '1px solid #e5e7eb',
                          background: selectedWork?.id === w.id ? '#fdf2f8' : 'white'
                        }}>
                        <div style={{ width: '100%', aspectRatio: 1, background: '#fce7f3', borderRadius: 8, marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                          {w.photo ? <img src={w.photo} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" /> : '💅'}
                        </div>
                        <div className="fs-12 text-center text-gray">{w.completed_at}</div>
                        <div className="fs-12 text-center text-pink-dark fw-500">{renderStars(w.satisfaction)}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray fs-13">该顾客暂无历史作品</p>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <h3 className="fs-16 fw-600 mb-16">⚙️ 个性化筛选条件</h3>

            <div className="form-group">
              <label>目标场合</label>
              <select className="select" value={targetOccasion}
                onChange={e => setTargetOccasion(e.target.value)}>
                <option value="">不限场合</option>
                {OCCASIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>预算范围</label>
              <select className="select" value={budget}
                onChange={e => setBudget(e.target.value)}>
                <option value="">不限预算</option>
                {BUDGETS.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>偏好色系（可多选）</label>
              <div className="flex gap-6 flex-wrap">
                {COLOR_PALETTE.map(c => {
                  const active = preferredColors.includes(c)
                  return (
                    <button key={c} type="button"
                      className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => toggleColor(c)}>{c}</button>
                  )
                })}
              </div>
            </div>

            <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid #f3f4f6' }}>
              <button className="btn btn-primary" style={{ width: '100%', padding: '12px 0', fontSize: 15 }}
                onClick={handleSubmit} disabled={submitting}>
                {submitting ? '🔄 正在提交分析...' : '✨ 开始 AI 试甲分析'}
              </button>
              <p className="fs-12 text-gray text-center mt-10">
                系统将基于照片/历史作品识别肤色、手型、指甲长度，并结合款式图库计算相似度推荐
              </p>
            </div>
          </div>
        </div>
      )}

      {tab === 'result' && selectedTask && (
        <div>
          {renderAnalysisCard()}
          {renderRecommendations()}
        </div>
      )}

      {tab === 'result' && !selectedTask && (
        <div className="card">
          <div className="empty-state">
            <div className="icon">✨</div>
            <p>请先从"历史任务"中选择一个试甲结果，或新建试甲任务</p>
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div>
          <div className="filter-bar">
            <select className="select" value={filterCustomer} onChange={e => setFilterCustomer(e.target.value)}>
              <option value="">全部顾客</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select className="select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="">全部状态</option>
              {['pending', 'processing', 'completed', 'failed'].map(s => (
                <option key={s} value={s}>{getTryOnStatusMeta(s).label}</option>
              ))}
            </select>
            <input type="number" className="input" placeholder="最低相似度" style={{ width: 140 }}
              value={filterSimMin} onChange={e => setFilterSimMin(e.target.value)} />
            <input type="number" className="input" placeholder="最高相似度" style={{ width: 140 }}
              value={filterSimMax} onChange={e => setFilterSimMax(e.target.value)} />
          </div>

          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>任务ID</th>
                  <th>顾客</th>
                  <th>状态</th>
                  <th>肤色</th>
                  <th>手型</th>
                  <th>指甲</th>
                  <th>场合</th>
                  <th>是否转化</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {taskList.length > 0 ? taskList.map(t => {
                  const sm = getTryOnStatusMeta(t.status)
                  return (
                    <tr key={t.id}>
                      <td>#{t.id}</td>
                      <td>{t.customer_name || '-'}</td>
                      <td><span className={`badge ${sm.cls}`}>{sm.label}</span></td>
                      <td>{t.skin_tone_display || '-'}</td>
                      <td>{t.hand_shape_display || '-'}</td>
                      <td>{t.nail_length_display || '-'}</td>
                      <td>{t.target_occasion_display || '-'}</td>
                      <td>
                        {t.converted_appointment_id
                          ? <span className="badge badge-completed">已转化 #{t.converted_appointment_id}</span>
                          : <span className="text-lightgray fs-13">未转化</span>}
                      </td>
                      <td>{t.created_at?.slice(0, 16).replace('T', ' ')}</td>
                      <td>
                        <button className="btn btn-sm btn-primary" onClick={() => selectTask(t)}>查看结果</button>
                      </td>
                    </tr>
                  )
                }) : (
                  <tr><td colSpan="10"><div className="empty-state"><div className="icon">📋</div><p>暂无试甲任务</p></div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {renderCompareModal()}
      {renderAppointmentModal()}
    </div>
  )
}
