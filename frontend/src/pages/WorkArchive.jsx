import React, { useState, useEffect } from 'react'
import { worksAPI, appointmentsAPI, customersAPI, techniciansAPI, designsAPI, renderStars, NAIL_SHAPES } from '../utils/api.js'
import dayjs from 'dayjs'

const SATISFACTION_OPTIONS = [
  { value: 5, label: '非常满意' },
  { value: 4, label: '满意' },
  { value: 3, label: '一般' },
  { value: 2, label: '不满意' },
  { value: 1, label: '非常不满意' },
]

export default function WorkArchive() {
  const [list, setList] = useState([])
  const [customers, setCustomers] = useState([])
  const [techs, setTechs] = useState([])
  const [designs, setDesigns] = useState([])
  const [completedAppts, setCompletedAppts] = useState([])
  const [filters, setFilters] = useState({ customer: '', technician: '', date_from: '', date_to: '' })
  const [showModal, setShowModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({
    appointment: '', customer: '', technician: '', design: '', photo: null,
    actual_nail_shape: 'oval', actual_color: '', duration_days: 21,
    satisfaction: 5, customer_feedback: '',
    completed_at: dayjs().format('YYYY-MM-DD')
  })

  useEffect(() => {
    loadData()
    customersAPI.list().then(r => setCustomers(r.data.results || r.data))
    techniciansAPI.list().then(r => setTechs(r.data.results || r.data))
    designsAPI.list().then(r => setDesigns(r.data.results || r.data))
    appointmentsAPI.list({ status: 'completed' }).then(r => setCompletedAppts(r.data.results || r.data))
  }, [])

  useEffect(() => { loadData() }, [filters])

  const loadData = () => {
    const params = {}
    if (filters.customer) params.customer = filters.customer
    if (filters.technician) params.technician = filters.technician
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    worksAPI.list(params).then(r => setList(r.data.results || r.data))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => {
      if (v !== null && v !== '' && v !== undefined) fd.append(k, v)
    })
    const action = selected ? worksAPI.update(selected.id, fd) : worksAPI.create(fd)
    action.then(() => {
      loadData()
      setShowModal(false)
    })
  }

  const deleteItem = (id) => {
    if (confirm('确认删除该作品存档？')) {
      worksAPI.delete(id).then(() => loadData())
    }
  }

  const onApptChange = (apptId) => {
    const appt = completedAppts.find(a => a.id === Number(apptId))
    if (appt) {
      setForm({
        ...form,
        appointment: apptId,
        customer: appt.customer,
        technician: appt.technician,
        design: appt.design || '',
        completed_at: appt.appointment_date
      })
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>作品存档</h2>
          <p className="text-gray">记录美甲完成作品，拍照存档并跟踪维持时长和满意度</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setSelected(null)
          setForm({
            appointment: '', customer: '', technician: '', design: '', photo: null,
            actual_nail_shape: 'oval', actual_color: '', duration_days: 21,
            satisfaction: 5, customer_feedback: '',
            completed_at: dayjs().format('YYYY-MM-DD')
          })
          setShowModal(true)
        }}>+ 新增作品</button>
      </div>

      <div className="filter-bar">
        <select className="select" value={filters.customer}
          onChange={e => setFilters({ ...filters, customer: e.target.value })}>
          <option value="">全部顾客</option>
          {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="select" value={filters.technician}
          onChange={e => setFilters({ ...filters, technician: e.target.value })}>
          <option value="">全部美甲师</option>
          {techs.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <input type="date" className="input" value={filters.date_from}
          onChange={e => setFilters({ ...filters, date_from: e.target.value })} />
        <span className="text-gray">至</span>
        <input type="date" className="input" value={filters.date_to}
          onChange={e => setFilters({ ...filters, date_to: e.target.value })} />
        {(filters.customer || filters.technician || filters.date_from || filters.date_to) && (
          <button className="btn btn-secondary btn-sm"
            onClick={() => setFilters({ customer: '', technician: '', date_from: '', date_to: '' })}>清除</button>
        )}
      </div>

      <div className="grid grid-3">
        {list.length > 0 ? list.map(w => (
          <div key={w.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="design-image" style={{ height: 160 }}>💅</div>
            <div style={{ padding: 16 }}>
              <div className="flex justify-between items-center mb-8">
                <h4 className="fs-15">{w.customer_name}</h4>
                <span className="stars">{renderStars(w.satisfaction)}</span>
              </div>
              <div className="fs-13 text-gray mb-4">美甲师：{w.technician_name}</div>
              <div className="fs-13 text-gray mb-4">{w.design_name || '自定义款式'} · {w.actual_color || '-'}</div>
              <div className="fs-13 text-gray mb-10">维持：{w.duration_days} 天 · 完成：{w.completed_at}</div>
              {w.customer_feedback && (
                <div className="fs-12 text-gray pad-8 bg-lightpink radius-6 mb-10">💬 {w.customer_feedback}</div>
              )}
              <div className="flex gap-6">
                <button className="btn btn-sm btn-danger" onClick={() => deleteItem(w.id)}>删除</button>
              </div>
            </div>
          </div>
        )) : (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <div className="icon">📸</div>
            <p>暂无作品存档</p>
          </div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selected ? '编辑作品' : '新增作品存档'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>关联预约（已完成）</label>
                  <select className="select" value={form.appointment}
                    onChange={e => onApptChange(e.target.value)}>
                    <option value="">不关联预约</option>
                    {completedAppts.map(a => (
                      <option key={a.id} value={a.id}>
                        {a.customer_name} - {a.appointment_date} ({a.design_name || '自定义'})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>顾客 *</label>
                    <select className="select" required value={form.customer}
                      onChange={e => setForm({ ...form, customer: e.target.value })}>
                      <option value="">请选择</option>
                      {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>操作美甲师 *</label>
                    <select className="select" required value={form.technician}
                      onChange={e => setForm({ ...form, technician: e.target.value })}>
                      <option value="">请选择</option>
                      {techs.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label>参考款式</label>
                  <select className="select" value={form.design}
                    onChange={e => setForm({ ...form, design: e.target.value })}>
                    <option value="">自定义款式</option>
                    {designs.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>完成照片</label>
                  <input type="file" className="input" accept="image/*"
                    onChange={e => setForm({ ...form, photo: e.target.files[0] })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>实际甲型</label>
                    <select className="select" value={form.actual_nail_shape}
                      onChange={e => setForm({ ...form, actual_nail_shape: e.target.value })}>
                      {NAIL_SHAPES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>实际色系</label>
                    <input className="input" placeholder="如：粉色系" value={form.actual_color}
                      onChange={e => setForm({ ...form, actual_color: e.target.value })} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>维持天数</label>
                    <input type="number" className="input" value={form.duration_days}
                      onChange={e => setForm({ ...form, duration_days: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>完成日期</label>
                    <input type="date" className="input" value={form.completed_at}
                      onChange={e => setForm({ ...form, completed_at: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>顾客满意度</label>
                  <select className="select" value={form.satisfaction}
                    onChange={e => setForm({ ...form, satisfaction: Number(e.target.value) })}>
                    {SATISFACTION_OPTIONS.map(s => <option key={s.value} value={s.value}>{renderStars(s.value)} {s.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>顾客反馈</label>
                  <textarea className="textarea" rows="3" value={form.customer_feedback}
                    onChange={e => setForm({ ...form, customer_feedback: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary">{selected ? '保存' : '创建'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
