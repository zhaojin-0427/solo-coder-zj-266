import React, { useState, useEffect } from 'react'
import { appointmentsAPI, customersAPI, techniciansAPI, designsAPI, getStatusMeta } from '../utils/api.js'
import dayjs from 'dayjs'

export default function AppointmentPage() {
  const [list, setList] = useState([])
  const [customers, setCustomers] = useState([])
  const [techs, setTechs] = useState([])
  const [designs, setDesigns] = useState([])
  const [filters, setFilters] = useState({ status: '', date_from: '', date_to: '' })
  const [showModal, setShowModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({
    customer: '', technician: '', design: '',
    appointment_date: dayjs().format('YYYY-MM-DD'), appointment_time: '14:00',
    status: 'pending', notes: ''
  })

  useEffect(() => {
    loadData()
    customersAPI.list().then(r => setCustomers(r.data.results || r.data))
    techniciansAPI.list().then(r => setTechs(r.data.results || r.data))
    designsAPI.list().then(r => setDesigns(r.data.results || r.data))
  }, [])

  useEffect(() => { loadData() }, [filters])

  const loadData = () => {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    appointmentsAPI.list(params).then(r => setList(r.data.results || r.data))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = { ...form }
    if (!payload.design) delete payload.design
    const action = selected ? appointmentsAPI.update(selected.id, payload) : appointmentsAPI.create(payload)
    action.then(() => {
      loadData()
      setShowModal(false)
    })
  }

  const updateStatus = (id, status) => {
    appointmentsAPI.update(id, { status }).then(() => loadData())
  }

  const deleteItem = (id) => {
    if (confirm('确认删除该预约？')) {
      appointmentsAPI.delete(id).then(() => loadData())
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>预约管理</h2>
          <p className="text-gray">查看和管理所有顾客预约</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setSelected(null); setForm({
            customer: '', technician: '', design: '',
            appointment_date: dayjs().format('YYYY-MM-DD'), appointment_time: '14:00',
            status: 'pending', notes: ''
          }); setShowModal(true)
        }}>+ 新建预约</button>
      </div>

      <div className="filter-bar">
        <select className="select" value={filters.status}
          onChange={e => setFilters({ ...filters, status: e.target.value })}>
          <option value="">全部状态</option>
          <option value="pending">待确认</option>
          <option value="confirmed">已确认</option>
          <option value="in_progress">进行中</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <input type="date" className="input" value={filters.date_from}
          onChange={e => setFilters({ ...filters, date_from: e.target.value })} />
        <span className="text-gray">至</span>
        <input type="date" className="input" value={filters.date_to}
          onChange={e => setFilters({ ...filters, date_to: e.target.value })} />
        {(filters.date_from || filters.date_to || filters.status) && (
          <button className="btn btn-secondary btn-sm"
            onClick={() => setFilters({ status: '', date_from: '', date_to: '' })}>清除筛选</button>
        )}
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>日期</th>
            <th>时间</th>
            <th>顾客</th>
            <th>美甲师</th>
            <th>款式</th>
            <th>状态</th>
            <th>备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {list.length > 0 ? list.map(a => {
            const statusMeta = getStatusMeta(a.status)
            return (
              <tr key={a.id}>
                <td>{a.appointment_date}</td>
                <td>{a.appointment_time}</td>
                <td>{a.customer_name}<br /><span className="fs-12 text-gray">{a.customer_phone}</span></td>
                <td>{a.technician_name}</td>
                <td>{a.design_name || '-'}</td>
                <td><span className={`badge ${statusMeta.cls}`}>{statusMeta.label}</span></td>
                <td style={{ maxWidth: 180 }} className="fs-13">{a.notes || '-'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {a.status === 'pending' && (
                      <button className="btn btn-sm btn-primary" onClick={() => updateStatus(a.id, 'confirmed')}>确认</button>
                    )}
                    {a.status === 'confirmed' && (
                      <button className="btn btn-sm btn-primary" onClick={() => updateStatus(a.id, 'in_progress')}>开始</button>
                    )}
                    {a.status === 'in_progress' && (
                      <button className="btn btn-sm btn-primary" onClick={() => updateStatus(a.id, 'completed')}>完成</button>
                    )}
                    {!['completed', 'cancelled'].includes(a.status) && (
                      <button className="btn btn-sm btn-danger" onClick={() => updateStatus(a.id, 'cancelled')}>取消</button>
                    )}
                    <button className="btn btn-sm btn-secondary" onClick={() => { setSelected(a); setForm(a); setShowModal(true) }}>编辑</button>
                    <button className="btn btn-sm btn-danger" onClick={() => deleteItem(a.id)}>删除</button>
                  </div>
                </td>
              </tr>
            )
          }) : (
            <tr><td colSpan="8"><div className="empty-state"><div className="icon">📅</div><p>暂无预约数据</p></div></td></tr>
          )}
        </tbody>
      </table>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selected ? '编辑预约' : '新建预约'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label>顾客 *</label>
                    <select className="select" required value={form.customer}
                      onChange={e => setForm({ ...form, customer: e.target.value })}>
                      <option value="">请选择</option>
                      {customers.map(c => <option key={c.id} value={c.id}>{c.name} ({c.phone})</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>美甲师 *</label>
                    <select className="select" required value={form.technician}
                      onChange={e => setForm({ ...form, technician: e.target.value })}>
                      <option value="">请选择</option>
                      {techs.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label>款式</label>
                  <select className="select" value={form.design}
                    onChange={e => setForm({ ...form, design: e.target.value })}>
                    <option value="">不指定款式</option>
                    {designs.map(d => <option key={d.id} value={d.id}>{d.name} - ¥{d.price}</option>)}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>预约日期 *</label>
                    <input type="date" className="input" required value={form.appointment_date}
                      onChange={e => setForm({ ...form, appointment_date: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>预约时间 *</label>
                    <input type="time" className="input" required value={form.appointment_time}
                      onChange={e => setForm({ ...form, appointment_time: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>状态</label>
                  <select className="select" value={form.status}
                    onChange={e => setForm({ ...form, status: e.target.value })}>
                    <option value="pending">待确认</option>
                    <option value="confirmed">已确认</option>
                    <option value="in_progress">进行中</option>
                    <option value="completed">已完成</option>
                    <option value="cancelled">已取消</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>备注</label>
                  <textarea className="textarea" rows="3" value={form.notes}
                    onChange={e => setForm({ ...form, notes: e.target.value })} />
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
