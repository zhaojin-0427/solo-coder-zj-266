import React, { useState, useEffect } from 'react'
import {
  customersAPI, worksAPI, appointmentsAPI, renderStars, SEASONS, getOccasionLabel, getShapeLabel,
  getMemberLevelMeta, getRiskLevelMeta, getContactTypeLabel, CONTACT_TYPES,
  tryOnAPI, getTryOnStatusMeta
} from '../utils/api.js'
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'
import { DataTable, FilterBar, ModalForm, StatusTag, EmptyState, useToast } from '../components'
import { useApiRequest } from '../hooks'

const NAIL_SHAPES_LIST = ['oval', 'square', 'squoval', 'almond', 'stiletto', 'coffin', 'ballerina', 'round']
const OCCASION_LIST = ['daily', 'wedding', 'party', 'office', 'festival', 'travel', 'date']
const COLOR_OPTIONS = ['粉色系', '裸色系', '黑色系', '蓝色系', '白色系', '棕色系', '紫色系', '绿色系', '红色系', '奶茶色系', '灰色系', '橘色系']
const STYLE_OPTIONS = ['甜美', '酷飒', '简约', '奢华', '艺术', '清新', '新娘', '节日', '经典']

const TagChip = ({ label, color = 'hotpink' }) => (
  <span className="tag-chip" style={{ background: color }}>{label}</span>
)

export default function CustomerPage() {
  const [list, setList] = useState([])
  const [selected, setSelected] = useState(null)
  const [preference, setPreference] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [works, setWorks] = useState([])
  const [appointments, setAppointments] = useState([])
  const [churnRisk, setChurnRisk] = useState(null)
  const [riskHistory, setRiskHistory] = useState([])
  const [contactRecords, setContactRecords] = useState([])
  const [tab, setTab] = useState('info')
  const [search, setSearch] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [tryOnHistory, setTryOnHistory] = useState([])
  const [form, setForm] = useState({ name: '', phone: '', gender: 'female', birthday: '', notes: '', member_level: 'normal' })
  const [showPref, setShowPref] = useState(false)
  const [prefForm, setPrefForm] = useState({
    preferred_colors: '', preferred_shapes: '', preferred_styles: '', preferred_occasions: ''
  })
  const [showContact, setShowContact] = useState(false)
  const [contactForm, setContactForm] = useState({ contact_type: 'wechat', content: '', operator: '' })

  const toast = useToast()
  const { loading: submitLoading, request: submitRequest } = useApiRequest()

  useEffect(() => { loadData() }, [search])

  const loadData = () => {
    customersAPI.list().then(r => {
      const data = r.data.results || r.data
      const filtered = search ? data.filter(c => c.name.includes(search) || c.phone.includes(search)) : data
      setList(filtered)
    })
  }

  const selectCustomer = async (c) => {
    setSelected(c)
    customersAPI.preference(c.id).then(r => {
      setPreference(r.data)
      setPrefForm({
        preferred_colors: r.data.preferred_colors,
        preferred_shapes: r.data.preferred_shapes,
        preferred_styles: r.data.preferred_styles,
        preferred_occasions: r.data.preferred_occasions,
      })
    })
    customersAPI.recommendations(c.id).then(r => setRecommendations(r.data))
    customersAPI.churnRisk(c.id).then(r => setChurnRisk(r.data))
    customersAPI.riskHistory(c.id).then(r => setRiskHistory(r.data.results || r.data))
    customersAPI.contactRecords(c.id).then(r => setContactRecords(r.data.results || r.data))
    worksAPI.list({ customer: c.id }).then(r => setWorks(r.data.results || r.data))
    appointmentsAPI.list({ customer: c.id }).then(r => setAppointments(r.data.results || r.data))
    tryOnAPI.myHistory(c.id).then(r => setTryOnHistory(r.data.results || r.data))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await submitRequest(customersAPI.create(form), {
      showSuccessToast: true,
      successMessage: '顾客已创建',
    })
    if (result.success) {
      loadData()
      setShowAdd(false)
      setForm({ name: '', phone: '', gender: 'female', birthday: '', notes: '', member_level: 'normal' })
    }
  }

  const savePref = async () => {
    const result = await submitRequest(customersAPI.updatePreference(selected.id, prefForm), {
      showSuccessToast: true,
      successMessage: '偏好已更新',
    })
    if (result.success) {
      setPreference(result.data)
      setShowPref(false)
    }
  }

  const submitContact = async (e) => {
    e.preventDefault()
    const result = await submitRequest(customersAPI.addContact(selected.id, contactForm), {
      showSuccessToast: true,
      successMessage: '跟进记录已创建',
    })
    if (result.success) {
      setShowContact(false)
      customersAPI.contactRecords(selected.id).then(r => setContactRecords(r.data.results || r.data))
      customersAPI.churnRisk(selected.id).then(r => setChurnRisk(r.data))
    }
  }

  const togglePrefItem = (field, value) => {
    const current = prefForm[field] ? prefForm[field].split(',').map(s => s.trim()).filter(Boolean) : []
    const next = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value]
    setPrefForm({ ...prefForm, [field]: next.join(', ') })
  }

  const renderTags = (str, labelMap, color) => {
    const items = str ? str.split(',').filter(Boolean).map(s => s.trim()) : []
    if (items.length === 0) return <span className="text-lightgray fs-13">未设置</span>
    return (
      <div className="flex gap-4 flex-wrap">
        {items.map((item, i) => (
          <TagChip key={i} label={labelMap ? labelMap(item) : item} color={color} />
        ))}
      </div>
    )
  }

  const renderListPage = () => {
    const columns = [
      { key: 'name', title: '姓名', render: (v) => <span className="fw-500">{v}</span> },
      { key: 'phone', title: '手机号' },
      {
        key: 'member_level',
        title: '会员等级',
        render: (v) => {
          const meta = getMemberLevelMeta(v)
          return <StatusTag label={meta.label} color={meta.color} />
        }
      },
      { key: 'gender', title: '性别', render: (v) => v === 'female' ? '女' : v === 'male' ? '男' : '其他' },
      { key: 'birthday', title: '生日', render: (v) => v || '-' },
      { key: 'works_count', title: '作品数', render: (v) => v || 0 },
      { key: 'created_at', title: '注册时间', render: (v) => v ? v.slice(0, 10) : '' },
      {
        key: 'actions',
        title: '操作',
        render: (_, row) => (
          <button className="btn btn-sm btn-primary" onClick={() => selectCustomer(row)}>查看详情</button>
        )
      },
    ]

    return (
      <div>
        <div className="page-header">
          <div>
            <h2>顾客档案</h2>
            <p className="text-gray">管理顾客信息、偏好设置和智能推荐</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ 新增顾客</button>
        </div>

        <FilterBar>
          <input
            className="input"
            placeholder="搜索顾客姓名或手机号..."
            style={{ width: 280 }}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </FilterBar>

        <div className="card">
          <DataTable
            columns={columns}
            data={list}
            emptyIcon="👥"
            emptyText="暂无顾客数据"
          />
        </div>

        <ModalForm
          open={showAdd}
          onClose={() => setShowAdd(false)}
          title="新增顾客"
          onSubmit={handleSubmit}
          submitText="创建"
          submitDisabled={submitLoading}
        >
          <div className="form-row">
            <div className="form-group">
              <label>姓名 *</label>
              <input
                className="input"
                required
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>手机号 *</label>
              <input
                className="input"
                required
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>性别</label>
              <select
                className="select"
                value={form.gender}
                onChange={e => setForm({ ...form, gender: e.target.value })}
              >
                <option value="female">女</option>
                <option value="male">男</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div className="form-group">
              <label>生日</label>
              <input
                type="date"
                className="input"
                value={form.birthday}
                onChange={e => setForm({ ...form, birthday: e.target.value })}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>会员等级</label>
              <select
                className="select"
                value={form.member_level}
                onChange={e => setForm({ ...form, member_level: e.target.value })}
              >
                <option value="normal">普通会员</option>
                <option value="silver">银卡会员</option>
                <option value="gold">金卡会员</option>
                <option value="platinum">钻石会员</option>
              </select>
            </div>
            <div className="form-group" />
          </div>
          <div className="form-group">
            <label>备注</label>
            <textarea
              className="textarea"
              rows="3"
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
            />
          </div>
        </ModalForm>
      </div>
    )
  }

  const renderDetailPage = () => {
    const memberMeta = getMemberLevelMeta(selected.member_level)
    const riskMeta = churnRisk ? getRiskLevelMeta(churnRisk.risk_level) : null

    const worksColumns = [
      { key: 'completed_at', title: '完成日期' },
      { key: 'technician_name', title: '美甲师' },
      { key: 'design_name', title: '款式', render: (v) => v || '-' },
      { key: 'actual_color', title: '色系', render: (v) => v || '-' },
      { key: 'satisfaction', title: '满意度', render: (v) => <span className="stars">{renderStars(v)}</span> },
      { key: 'duration_days', title: '维持天数', render: (v) => `${v} 天` },
    ]

    const apptColumns = [
      { key: 'appointment_date', title: '日期' },
      { key: 'appointment_time', title: '时间' },
      { key: 'technician_name', title: '美甲师' },
      { key: 'design_name', title: '款式', render: (v) => v || '-' },
      {
        key: 'status',
        title: '状态',
        render: (v) => {
          const labels = { pending: '待确认', confirmed: '已确认', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }
          return <StatusTag label={labels[v]} cls={`badge-${v}`} />
        }
      },
    ]

    const contactColumns = [
      { key: 'contacted_at', title: '联系时间', render: (v) => v ? v.slice(0, 16).replace('T', ' ') : '-' },
      {
        key: 'contact_type',
        title: '联系方式',
        render: (v) => <TagChip label={getContactTypeLabel(v)} color="#6366f1" />
      },
      { key: 'content', title: '联系内容' },
      { key: 'operator', title: '操作人', render: (v) => v || '-' },
    ]

    const tryonColumns = [
      { key: 'id', title: '任务ID', render: (v) => `#${v}` },
      {
        key: 'status',
        title: '状态',
        render: (v) => {
          const sm = getTryOnStatusMeta(v)
          return <StatusTag label={sm.label} cls={sm.cls} />
        }
      },
      { key: 'skin_tone_display', title: '识别肤色', render: (v) => v || '-' },
      { key: 'hand_shape_display', title: '识别手型', render: (v) => v || '-' },
      { key: 'nail_length_display', title: '指甲长度', render: (v) => v || '-' },
      { key: 'target_occasion_display', title: '目标场合', render: (v) => v || '-' },
      { key: 'budget_display', title: '预算', render: (v) => v || '-' },
      { key: 'similar_results', title: '推荐款式', render: (v) => `${v?.length || 0} 款` },
      {
        key: 'converted_appointment_id',
        title: '是否转化',
        render: (v) => v
          ? <StatusTag label={`预约 #${v}`} cls="badge-completed" />
          : <span className="text-lightgray fs-13">未转化</span>
      },
      { key: 'created_at', title: '时间', render: (v) => v?.slice(0, 16).replace('T', ' ') },
    ]

    return (
      <div>
        <div className="flex items-start gap-16 mb-24">
          <button className="btn btn-secondary" onClick={() => setSelected(null)}>← 返回列表</button>
          <div>
            <div className="flex items-center gap-10 mb-4">
              <h2 className="fs-22">{selected.name}</h2>
              <StatusTag label={memberMeta.label} color={memberMeta.color} />
              {riskMeta && (
                <StatusTag label={`${riskMeta.label} ${churnRisk.score.toFixed(1)}分`} cls={riskMeta.cls} />
              )}
            </div>
            <p className="text-gray">{selected.phone}</p>
          </div>
        </div>

        <div className="customer-detail">
          <div>
            <div className="card mb-20">
              <div className="customer-avatar">👩</div>
              <ul className="info-list">
                <li><span className="label">性别</span><span className="val">{selected.gender === 'female' ? '女' : selected.gender === 'male' ? '男' : '其他'}</span></li>
                <li>
                  <span className="label">会员等级</span>
                  <span className="val" style={{ color: memberMeta.color, fontWeight: 600 }}>{memberMeta.label}</span>
                </li>
                <li><span className="label">生日</span><span className="val">{selected.birthday || '-'}</span></li>
                <li><span className="label">作品数</span><span className="val">{selected.works_count || 0}</span></li>
                <li><span className="label">最近到店</span><span className="val">{selected.last_visit || '-'}</span></li>
                <li><span className="label">最近联系</span><span className="val">{selected.last_contact_at ? selected.last_contact_at.slice(0, 10) : '-'}</span></li>
                <li><span className="label">注册时间</span><span className="val">{selected.created_at ? selected.created_at.slice(0, 10) : '-'}</span></li>
              </ul>
              {churnRisk && churnRisk.recommended_action && (
                <div style={{ padding: '10px 0', borderTop: '1px solid #f3f4f6' }}>
                  <div className="fs-13 text-gray">📋 推荐动作：<span className="text-pink-dark fw-600">{churnRisk.recommended_action}</span></div>
                </div>
              )}
              {selected.notes && (
                <div style={{ padding: '10px 0', borderTop: '1px solid #f3f4f6' }}>
                  <div className="fs-13 text-gray">备注：{selected.notes}</div>
                </div>
              )}
            </div>

            <div className="card">
              <div className="flex justify-between items-center mb-14">
                <h4 className="fs-15">🎯 顾客偏好</h4>
                <button className="btn btn-sm btn-secondary" onClick={() => setShowPref(true)}>编辑</button>
              </div>
              {preference && (
                <div>
                  <div className="mb-10">
                    <div className="fs-12 text-gray mb-4">偏好色系</div>
                    {renderTags(preference.preferred_colors, null, 'hotpink')}
                  </div>
                  <div className="mb-10">
                    <div className="fs-12 text-gray mb-4">偏好甲型</div>
                    {renderTags(preference.preferred_shapes, getShapeLabel, 'rebeccapurple')}
                  </div>
                  <div className="mb-10">
                    <div className="fs-12 text-gray mb-4">偏好风格</div>
                    {renderTags(preference.preferred_styles, null, 'mediumseagreen')}
                  </div>
                  <div>
                    <div className="fs-12 text-gray mb-4">偏好场合</div>
                    {renderTags(preference.preferred_occasions, getOccasionLabel, 'darkorange')}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="tabs">
              <button className={`tab ${tab === 'info' ? 'active' : ''}`} onClick={() => setTab('info')}>基本信息</button>
              <button className={`tab ${tab === 'risk' ? 'active' : ''}`} onClick={() => setTab('risk')}>风险趋势</button>
              <button className={`tab ${tab === 'rec' ? 'active' : ''}`} onClick={() => setTab('rec')}>智能推荐</button>
              <button className={`tab ${tab === 'works' ? 'active' : ''}`} onClick={() => setTab('works')}>历史作品</button>
              <button className={`tab ${tab === 'appts' ? 'active' : ''}`} onClick={() => setTab('appts')}>预约记录</button>
              <button className={`tab ${tab === 'contacts' ? 'active' : ''}`} onClick={() => setTab('contacts')}>跟进记录</button>
              <button className={`tab ${tab === 'tryon' ? 'active' : ''}`} onClick={() => setTab('tryon')}>✨ 试甲历史</button>
            </div>

            {tab === 'info' && (
              <div className="card">
                <h4 className="mb-14">📋 顾客详情</h4>
                <p className="text-gray lh-18">
                  点击上方标签查看顾客的智能推荐、历史作品和预约记录。
                  系统会基于顾客偏好和当季流行趋势自动推荐合适的美甲款式。
                </p>
              </div>
            )}

            {tab === 'rec' && recommendations && (
              <div>
                <div className="card mb-20">
                  <div className="flex items-center gap-10 mb-14">
                    <h4 className="fs-15">🌸 当季趋势</h4>
                    <StatusTag label={SEASONS[recommendations.season]} cls="badge-completed" />
                  </div>
                  <div className="flex gap-6 flex-wrap">
                    {recommendations.season_colors && recommendations.season_colors.map((c, i) => (
                      <TagChip key={i} label={`${c}色系`} color="hotpink" />
                    ))}
                  </div>
                </div>
                <div className="card">
                  <h4 className="fs-15 mb-14">✨ 为 {selected.name} 推荐</h4>
                  {recommendations.recommendations && recommendations.recommendations.length > 0 ? (
                    recommendations.recommendations.map((rec, i) => (
                      <div key={i} className="recommendation-item">
                        <div className="rec-image">💅</div>
                        <div className="flex-1">
                          <h5>{rec.design.name}</h5>
                          <p>{rec.design.color_system} · {getShapeLabel(rec.design.nail_shape)} · {getOccasionLabel(rec.design.occasion)}</p>
                          <div className="reasons">
                            {rec.reasons.map((r, j) => (
                              <span key={j} className="reason-tag">{r}</span>
                            ))}
                          </div>
                        </div>
                        <div className="text-pink fw-700">¥{rec.design.price}</div>
                      </div>
                    ))
                  ) : (
                    <EmptyState icon="💭" text="暂无推荐，可完善顾客偏好后获得更精准推荐" />
                  )}
                </div>
              </div>
            )}

            {tab === 'works' && (
              <div className="card">
                <DataTable
                  columns={worksColumns}
                  data={works}
                  emptyIcon="📸"
                  emptyText="暂无作品记录"
                />
              </div>
            )}

            {tab === 'appts' && (
              <div className="card">
                <DataTable
                  columns={apptColumns}
                  data={appointments}
                  emptyIcon="📅"
                  emptyText="暂无预约记录"
                />
              </div>
            )}

            {tab === 'risk' && churnRisk && (
              <div>
                <div className="card mb-20">
                  <div className="flex justify-between items-center mb-14">
                    <h4 className="fs-15">⚠️ 当前流失风险评估</h4>
                    <div className="flex items-center gap-8">
                      <StatusTag label={riskMeta.label} cls={riskMeta.cls} />
                      <span className="fs-22 fw-700" style={{ color: riskMeta.color }}>{churnRisk.score.toFixed(1)} 分</span>
                    </div>
                  </div>

                  <div className="mb-14">
                    <div className="fs-13 text-gray mb-6">📌 风险原因：</div>
                    <div className="flex gap-4 flex-wrap">
                      {churnRisk.reasons && churnRisk.reasons.length > 0 ? (
                        churnRisk.reasons.map((r, i) => (
                          <span key={i} className="risk-reason-tag">{r}</span>
                        ))
                      ) : (
                        <span className="text-lightgray fs-13">暂无明显风险</span>
                      )}
                    </div>
                  </div>

                  <div className="mb-14">
                    <div className="fs-13 text-gray mb-6">📊 评分因子详情：</div>
                    <div className="grid grid-3 gap-10">
                      {churnRisk.factors && Object.entries(churnRisk.factors).map(([k, v]) => (
                        <div key={k} className="bg-lightpink pad-8 radius-6">
                          <div className="fs-12 text-gray">{k}</div>
                          <div className="fs-14 fw-600">{String(v)}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {churnRisk.scripts && churnRisk.scripts.length > 0 && (
                    <div>
                      <div className="fs-13 text-gray mb-6">💬 推荐回访话术：</div>
                      {churnRisk.scripts.map((s, i) => (
                        <div key={i} className="script-bubble">
                          <span className="fs-13">{s}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="card">
                  <h4 className="fs-15 mb-14">📈 风险评分趋势</h4>
                  {riskHistory && riskHistory.length > 1 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={riskHistory.map(h => ({
                        time: new Date(h.recorded_at).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }),
                        score: h.score,
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Line type="monotone" dataKey="score" name="风险评分" stroke="#ec4899" strokeWidth={2} dot={{ fill: '#ec4899' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyState icon="📈" text="暂无趋势数据，计算一次后即可查看" />
                  )}
                </div>
              </div>
            )}

            {tab === 'contacts' && (
              <div className="card">
                <div className="flex justify-between items-center mb-14">
                  <h4 className="fs-15">📞 跟进记录</h4>
                  <button className="btn btn-sm btn-primary" onClick={() => {
                    setContactForm({ contact_type: 'wechat', content: '', operator: '' })
                    setShowContact(true)
                  }}>+ 新增跟进</button>
                </div>
                <DataTable
                  columns={contactColumns}
                  data={contactRecords}
                  emptyIcon="📞"
                  emptyText="暂无跟进记录"
                />
              </div>
            )}

            {tab === 'tryon' && (
              <div>
                <div className="grid grid-3 mb-20">
                  <div className="stat-card">
                    <h3>试甲总次数</h3>
                    <div className="value">{tryOnHistory.length}</div>
                  </div>
                  <div className="stat-card" style={{ borderLeftColor: '#10b981' }}>
                    <h3>已转化预约</h3>
                    <div className="value" style={{ color: '#10b981' }}>
                      {tryOnHistory.filter(t => t.converted_appointment_id).length}
                    </div>
                  </div>
                  <div className="stat-card" style={{ borderLeftColor: '#8b5cf6' }}>
                    <h3>转化率</h3>
                    <div className="value" style={{ color: '#8b5cf6' }}>
                      {tryOnHistory.length > 0
                        ? ((tryOnHistory.filter(t => t.converted_appointment_id).length / tryOnHistory.length) * 100).toFixed(0)
                        : 0}%
                    </div>
                  </div>
                </div>

                <div className="card">
                  <DataTable
                    columns={tryonColumns}
                    data={tryOnHistory}
                    emptyIcon="✨"
                    emptyText="暂无试甲记录"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <ModalForm
          open={showPref}
          onClose={() => setShowPref(false)}
          title="编辑顾客偏好"
          onSubmit={(e) => { e.preventDefault(); savePref() }}
          submitDisabled={submitLoading}
        >
          <div className="form-group">
            <label>偏好色系（可多选）</label>
            <div className="flex gap-6 flex-wrap">
              {COLOR_OPTIONS.map(c => {
                const active = prefForm.preferred_colors && prefForm.preferred_colors.includes(c)
                return (
                  <button key={c} type="button"
                    className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => togglePrefItem('preferred_colors', c)}>{c}</button>
                )
              })}
            </div>
          </div>
          <div className="form-group">
            <label>偏好甲型（可多选）</label>
            <div className="flex gap-6 flex-wrap">
              {NAIL_SHAPES_LIST.map(s => {
                const active = prefForm.preferred_shapes && prefForm.preferred_shapes.includes(s)
                return (
                  <button key={s} type="button"
                    className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => togglePrefItem('preferred_shapes', s)}>{getShapeLabel(s)}</button>
                )
              })}
            </div>
          </div>
          <div className="form-group">
            <label>偏好风格（可多选）</label>
            <div className="flex gap-6 flex-wrap">
              {STYLE_OPTIONS.map(s => {
                const active = prefForm.preferred_styles && prefForm.preferred_styles.includes(s)
                return (
                  <button key={s} type="button"
                    className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => togglePrefItem('preferred_styles', s)}>{s}</button>
                )
              })}
            </div>
          </div>
          <div className="form-group">
            <label>偏好场合（可多选）</label>
            <div className="flex gap-6 flex-wrap">
              {OCCASION_LIST.map(o => {
                const active = prefForm.preferred_occasions && prefForm.preferred_occasions.includes(o)
                return (
                  <button key={o} type="button"
                    className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => togglePrefItem('preferred_occasions', o)}>{getOccasionLabel(o)}</button>
                )
              })}
            </div>
          </div>
        </ModalForm>

        <ModalForm
          open={showContact}
          onClose={() => setShowContact(false)}
          title={`新增跟进记录 - ${selected.name}`}
          onSubmit={submitContact}
          submitText="创建跟进记录"
          submitDisabled={submitLoading}
        >
          <div className="form-group">
            <label>联系方式</label>
            <select
              className="select"
              value={contactForm.contact_type}
              onChange={e => setContactForm({ ...contactForm, contact_type: e.target.value })}
            >
              {CONTACT_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>联系内容 *</label>
            <textarea
              className="textarea"
              rows="5"
              value={contactForm.content}
              onChange={e => setContactForm({ ...contactForm, content: e.target.value })}
              placeholder="请输入联系内容..."
              required
            />
          </div>
          <div className="form-group">
            <label>操作人</label>
            <input
              className="input"
              value={contactForm.operator}
              onChange={e => setContactForm({ ...contactForm, operator: e.target.value })}
              placeholder="请输入操作人姓名"
            />
          </div>
        </ModalForm>
      </div>
    )
  }

  return selected ? renderDetailPage() : renderListPage()
}
