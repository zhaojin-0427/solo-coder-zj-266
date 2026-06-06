import React, { useState, useEffect } from 'react'
import { customersAPI, worksAPI, appointmentsAPI, renderStars, SEASONS, getOccasionLabel, getShapeLabel } from '../utils/api.js'

const NAIL_SHAPES_LIST = ['oval', 'square', 'squoval', 'almond', 'stiletto', 'coffin', 'ballerina', 'round']
const OCCASION_LIST = ['daily', 'wedding', 'party', 'office', 'festival', 'travel', 'date']
const COLOR_OPTIONS = ['粉色系', '裸色系', '黑色系', '蓝色系', '白色系', '棕色系', '紫色系', '绿色系', '红色系', '奶茶色系', '灰色系', '橘色系']
const STYLE_OPTIONS = ['甜美', '酷飒', '简约', '奢华', '艺术', '清新', '新娘', '节日', '经典']

export default function CustomerPage() {
  const [list, setList] = useState([])
  const [selected, setSelected] = useState(null)
  const [preference, setPreference] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [works, setWorks] = useState([])
  const [appointments, setAppointments] = useState([])
  const [tab, setTab] = useState('info')
  const [search, setSearch] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', gender: 'female', birthday: '', notes: '' })
  const [showPref, setShowPref] = useState(false)
  const [prefForm, setPrefForm] = useState({
    preferred_colors: '', preferred_shapes: '', preferred_styles: '', preferred_occasions: ''
  })

  useEffect(() => { loadData() }, [])
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
    worksAPI.list({ customer: c.id }).then(r => setWorks(r.data.results || r.data))
    appointmentsAPI.list({ customer: c.id }).then(r => setAppointments(r.data.results || r.data))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    customersAPI.create(form).then(() => {
      loadData()
      setShowAdd(false)
      setForm({ name: '', phone: '', gender: 'female', birthday: '', notes: '' })
    })
  }

  const savePref = () => {
    customersAPI.updatePreference(selected.id, prefForm).then(r => {
      setPreference(r.data)
      setShowPref(false)
    })
  }

  const togglePrefItem = (field, value) => {
    const current = prefForm[field] ? prefForm[field].split(',').map(s => s.trim()).filter(Boolean) : []
    const next = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value]
    setPrefForm({ ...prefForm, [field]: next.join(', ') })
  }

  const TagChip = ({ label }) => (
    <span className="tag-chip" style={{ background: 'hotpink' }}>{label}</span>
  )

  if (selected) return (
    <div>
      <div className="flex items-start gap-16 mb-24">
        <button className="btn btn-secondary" onClick={() => setSelected(null)}>← 返回列表</button>
        <div>
          <h2 className="fs-22">{selected.name}</h2>
          <p className="text-gray">{selected.phone}</p>
        </div>
      </div>

      <div className="customer-detail">
        <div>
          <div className="card mb-20">
            <div className="customer-avatar">👩</div>
            <ul className="info-list">
              <li><span className="label">性别</span><span className="val">{selected.gender === 'female' ? '女' : selected.gender === 'male' ? '男' : '其他'}</span></li>
              <li><span className="label">生日</span><span className="val">{selected.birthday || '-'}</span></li>
              <li><span className="label">作品数</span><span className="val">{selected.works_count || 0}</span></li>
              <li><span className="label">最近到店</span><span className="val">{selected.last_visit || '-'}</span></li>
              <li><span className="label">注册时间</span><span className="val">{selected.created_at ? selected.created_at.slice(0, 10) : '-'}</span></li>
            </ul>
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
                  <div className="flex gap-4 flex-wrap">
                    {preference.preferred_colors && preference.preferred_colors.split(',').filter(Boolean).map((c, i) => (
                      <TagChip key={i} label={c.trim()} />
                    ))}
                    {!preference.preferred_colors && <span className="text-lightgray fs-13">未设置</span>}
                  </div>
                </div>
                <div className="mb-10">
                  <div className="fs-12 text-gray mb-4">偏好甲型</div>
                  <div className="flex gap-4 flex-wrap">
                    {preference.preferred_shapes && preference.preferred_shapes.split(',').filter(Boolean).map((c, i) => (
                      <span key={i} className="tag-chip" style={{ background: 'rebeccapurple' }}>{getShapeLabel(c.trim())}</span>
                    ))}
                    {!preference.preferred_shapes && <span className="text-lightgray fs-13">未设置</span>}
                  </div>
                </div>
                <div className="mb-10">
                  <div className="fs-12 text-gray mb-4">偏好风格</div>
                  <div className="flex gap-4 flex-wrap">
                    {preference.preferred_styles && preference.preferred_styles.split(',').filter(Boolean).map((c, i) => (
                      <span key={i} className="tag-chip" style={{ background: 'mediumseagreen' }}>{c.trim()}</span>
                    ))}
                    {!preference.preferred_styles && <span className="text-lightgray fs-13">未设置</span>}
                  </div>
                </div>
                <div>
                  <div className="fs-12 text-gray mb-4">偏好场合</div>
                  <div className="flex gap-4 flex-wrap">
                    {preference.preferred_occasions && preference.preferred_occasions.split(',').filter(Boolean).map((c, i) => (
                      <span key={i} className="tag-chip" style={{ background: 'darkorange' }}>{getOccasionLabel(c.trim())}</span>
                    ))}
                    {!preference.preferred_occasions && <span className="text-lightgray fs-13">未设置</span>}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="tabs">
            <button className={`tab ${tab === 'info' ? 'active' : ''}`} onClick={() => setTab('info')}>基本信息</button>
            <button className={`tab ${tab === 'rec' ? 'active' : ''}`} onClick={() => setTab('rec')}>智能推荐</button>
            <button className={`tab ${tab === 'works' ? 'active' : ''}`} onClick={() => setTab('works')}>历史作品</button>
            <button className={`tab ${tab === 'appts' ? 'active' : ''}`} onClick={() => setTab('appts')}>预约记录</button>
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
                  <span className="badge badge-completed">{SEASONS[recommendations.season]}</span>
                </div>
                <div className="flex gap-6 flex-wrap">
                  {recommendations.season_colors && recommendations.season_colors.map((c, i) => (
                    <span key={i} className="tag-chip" style={{ background: 'hotpink' }}>{c}色系</span>
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
                  <div className="empty-state">
                    <div className="icon">💭</div>
                    <p>暂无推荐，可完善顾客偏好后获得更精准推荐</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {tab === 'works' && (
            <div className="card">
              <table className="table">
                <thead>
                  <tr>
                    <th>完成日期</th>
                    <th>美甲师</th>
                    <th>款式</th>
                    <th>色系</th>
                    <th>满意度</th>
                    <th>维持天数</th>
                  </tr>
                </thead>
                <tbody>
                  {works.length > 0 ? works.map(w => (
                    <tr key={w.id}>
                      <td>{w.completed_at}</td>
                      <td>{w.technician_name}</td>
                      <td>{w.design_name || '-'}</td>
                      <td>{w.actual_color || '-'}</td>
                      <td><span className="stars">{renderStars(w.satisfaction)}</span></td>
                      <td>{w.duration_days} 天</td>
                    </tr>
                  )) : (
                    <tr><td colSpan="6"><div className="empty-state"><div className="icon">📸</div><p>暂无作品记录</p></div></td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'appts' && (
            <div className="card">
              <table className="table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>时间</th>
                    <th>美甲师</th>
                    <th>款式</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.length > 0 ? appointments.map(a => (
                    <tr key={a.id}>
                      <td>{a.appointment_date}</td>
                      <td>{a.appointment_time}</td>
                      <td>{a.technician_name}</td>
                      <td>{a.design_name || '-'}</td>
                      <td>
                        <span className={`badge badge-${a.status}`}>
                          {a.status === 'pending' && '待确认'}
                          {a.status === 'confirmed' && '已确认'}
                          {a.status === 'in_progress' && '进行中'}
                          {a.status === 'completed' && '已完成'}
                          {a.status === 'cancelled' && '已取消'}
                        </span>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="5"><div className="empty-state"><div className="icon">📅</div><p>暂无预约记录</p></div></td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showPref && (
        <div className="modal-overlay" onClick={() => setShowPref(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>编辑顾客偏好</h3>
              <button className="modal-close" onClick={() => setShowPref(false)}>×</button>
            </div>
            <div className="modal-body">
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
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setShowPref(false)}>取消</button>
              <button type="button" className="btn btn-primary" onClick={savePref}>保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>顾客档案</h2>
          <p className="text-gray">管理顾客信息、偏好设置和智能推荐</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ 新增顾客</button>
      </div>

      <div className="filter-bar">
        <input className="input" placeholder="搜索顾客姓名或手机号..." style={{ width: 280 }}
          value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>姓名</th>
            <th>手机号</th>
            <th>性别</th>
            <th>生日</th>
            <th>作品数</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {list.length > 0 ? list.map(c => (
            <tr key={c.id}>
              <td className="fw-500">{c.name}</td>
              <td>{c.phone}</td>
              <td>{c.gender === 'female' ? '女' : c.gender === 'male' ? '男' : '其他'}</td>
              <td>{c.birthday || '-'}</td>
              <td>{c.works_count || 0}</td>
              <td>{c.created_at ? c.created_at.slice(0, 10) : ''}</td>
              <td>
                <button className="btn btn-sm btn-primary" onClick={() => selectCustomer(c)}>查看详情</button>
              </td>
            </tr>
          )) : (
            <tr><td colSpan="7"><div className="empty-state"><div className="icon">👥</div><p>暂无顾客数据</p></div></td></tr>
          )}
        </tbody>
      </table>

      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>新增顾客</h3>
              <button className="modal-close" onClick={() => setShowAdd(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label>姓名 *</label>
                    <input className="input" required value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>手机号 *</label>
                    <input className="input" required value={form.phone}
                      onChange={e => setForm({ ...form, phone: e.target.value })} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>性别</label>
                    <select className="select" value={form.gender}
                      onChange={e => setForm({ ...form, gender: e.target.value })}>
                      <option value="female">女</option>
                      <option value="male">男</option>
                      <option value="other">其他</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>生日</label>
                    <input type="date" className="input" value={form.birthday}
                      onChange={e => setForm({ ...form, birthday: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>备注</label>
                  <textarea className="textarea" rows="3" value={form.notes}
                    onChange={e => setForm({ ...form, notes: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>取消</button>
                <button type="submit" className="btn btn-primary">创建</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
