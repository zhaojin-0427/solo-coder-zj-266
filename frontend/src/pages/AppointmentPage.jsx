import React, { useState, useEffect } from 'react'
import { appointmentsAPI, customersAPI, techniciansAPI, designsAPI, getStatusMeta } from '../utils/api.js'
import dayjs from 'dayjs'
import { DataTable, FilterBar, ModalForm, StatusTag, useToast } from '../components'
import { useApiRequest } from '../hooks'

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待确认' },
  { value: 'confirmed', label: '已确认' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]

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

  const toast = useToast()
  const { loading: submitLoading, request: submitRequest } = useApiRequest()

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

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = { ...form }
    if (!payload.design) delete payload.design
    const action = selected ? appointmentsAPI.update(selected.id, payload) : appointmentsAPI.create(payload)
    const result = await submitRequest(action, {
      showSuccessToast: true,
      successMessage: selected ? '预约已更新' : '预约已创建',
    })
    if (result.success) {
      loadData()
      setShowModal(false)
    }
  }

  const updateStatus = async (id, newStatus) => {
    const result = await submitRequest(
      appointmentsAPI.partialUpdate(id, { status: newStatus }),
      { successMessage: `状态已更新为${getStatusMeta(newStatus).label}` }
    )
    if (result.success) loadData()
  }

  const deleteItem = async (id) => {
    if (!window.confirm('确认删除该预约？')) return
    const result = await submitRequest(
      appointmentsAPI.delete(id),
      { successMessage: '预约已删除' }
    )
    if (result.success) loadData()
  }

  const openModal = (item) => {
    setSelected(item || null)
    if (item) {
      setForm({ ...item })
    } else {
      setForm({
        customer: '', technician: '', design: '',
        appointment_date: dayjs().format('YYYY-MM-DD'), appointment_time: '14:00',
        status: 'pending', notes: ''
      })
    }
    setShowModal(true)
  }

  const columns = [
    { key: 'appointment_date', title: '日期' },
    { key: 'appointment_time', title: '时间' },
    {
      key: 'customer_name',
      title: '顾客',
      render: (val, row) => (
        <div>
          <div>{val}</div>
          <div className="fs-12 text-gray">{row.customer_phone}</div>
        </div>
      )
    },
    { key: 'technician_name', title: '美甲师' },
    { key: 'design_name', title: '款式', render: (v) => v || '-' },
    {
      key: 'status',
      title: '状态',
      render: (v) => {
        const meta = getStatusMeta(v)
        return <StatusTag label={meta.label} cls={meta.cls} />
      }
    },
    {
      key: 'notes',
      title: '备注',
      cellStyle: { maxWidth: 180 },
      render: (v) => <span className="fs-13">{v || '-'}</span>
    },
    {
      key: 'actions',
      title: '操作',
      render: (_, row) => (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {row.status === 'pending' && (
            <button className="btn btn-sm btn-primary" onClick={() => updateStatus(row.id, 'confirmed')}>确认</button>
          )}
          {row.status === 'confirmed' && (
            <button className="btn btn-sm btn-primary" onClick={() => updateStatus(row.id, 'in_progress')}>开始</button>
          )}
          {row.status === 'in_progress' && (
            <button className="btn btn-sm btn-primary" onClick={() => updateStatus(row.id, 'completed')}>完成</button>
          )}
          {!['completed', 'cancelled'].includes(row.status) && (
            <button className="btn btn-sm btn-danger" onClick={() => updateStatus(row.id, 'cancelled')}>取消</button>
          )}
          <button className="btn btn-sm btn-secondary" onClick={() => openModal(row)}>编辑</button>
          <button className="btn btn-sm btn-danger" onClick={() => deleteItem(row.id)}>删除</button>
        </div>
      )
    },
  ]

  const hasFilter = filters.date_from || filters.date_to || filters.status

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>预约管理</h2>
          <p className="text-gray">查看和管理所有顾客预约</p>
        </div>
        <button className="btn btn-primary" onClick={() => openModal(null)}>+ 新建预约</button>
      </div>

      <FilterBar>
        <select
          className="select"
          value={filters.status}
          onChange={e => setFilters({ ...filters, status: e.target.value })}
        >
          {STATUS_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <input
          type="date"
          className="input"
          value={filters.date_from}
          onChange={e => setFilters({ ...filters, date_from: e.target.value })}
        />
        <span className="text-gray">至</span>
        <input
          type="date"
          className="input"
          value={filters.date_to}
          onChange={e => setFilters({ ...filters, date_to: e.target.value })}
        />
        {hasFilter && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setFilters({ status: '', date_from: '', date_to: '' })}
          >
            清除筛选
          </button>
        )}
      </FilterBar>

      <div className="card">
        <DataTable
          columns={columns}
          data={list}
          emptyIcon="📅"
          emptyText="暂无预约数据"
        />
      </div>

      <ModalForm
        open={showModal}
        onClose={() => setShowModal(false)}
        title={selected ? '编辑预约' : '新建预约'}
        onSubmit={handleSubmit}
        submitText={selected ? '保存' : '创建'}
        submitDisabled={submitLoading}
      >
        <div className="form-row">
          <div className="form-group">
            <label>顾客 *</label>
            <select
              className="select"
              required
              value={form.customer}
              onChange={e => setForm({ ...form, customer: e.target.value })}
            >
              <option value="">请选择</option>
              {customers.map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.phone})</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>美甲师 *</label>
            <select
              className="select"
              required
              value={form.technician}
              onChange={e => setForm({ ...form, technician: e.target.value })}
            >
              <option value="">请选择</option>
              {techs.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
        </div>
        <div className="form-group">
          <label>款式</label>
          <select
            className="select"
            value={form.design}
            onChange={e => setForm({ ...form, design: e.target.value })}
          >
            <option value="">不指定款式</option>
            {designs.map(d => <option key={d.id} value={d.id}>{d.name} - ¥{d.price}</option>)}
          </select>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>预约日期 *</label>
            <input
              type="date"
              className="input"
              required
              value={form.appointment_date}
              onChange={e => setForm({ ...form, appointment_date: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>预约时间 *</label>
            <input
              type="time"
              className="input"
              required
              value={form.appointment_time}
              onChange={e => setForm({ ...form, appointment_time: e.target.value })}
            />
          </div>
        </div>
        <div className="form-group">
          <label>状态</label>
          <select
            className="select"
            value={form.status}
            onChange={e => setForm({ ...form, status: e.target.value })}
          >
            {STATUS_OPTIONS.filter(o => o.value !== '').map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
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
