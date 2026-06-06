import React, { useState, useEffect } from 'react'
import { designsAPI, styleTagsAPI, techniciansAPI, NAIL_SHAPES, OCCASIONS, getShapeLabel, getOccasionLabel } from '../utils/api.js'

const TAG_COLORS = {
  '甜美': '#ec4899', '酷飒': '#6b7280', '简约': '#f59e0b',
  '奢华': '#a855f7', '艺术': '#10b981', '清新': '#06b6d4',
  '新娘': '#f43f5e', '节日': '#ef4444', '经典': '#6366f1',
}

export default function DesignGallery() {
  const [designs, setDesigns] = useState([])
  const [tags, setTags] = useState([])
  const [techs, setTechs] = useState([])
  const [filters, setFilters] = useState({ shape: '', occasion: '', tag: '', search: '' })
  const [showModal, setShowModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({
    name: '', nail_shape: 'oval', color_system: '', decoration: '',
    occasion: 'daily', description: '', technician: '', price: '', image: null
  })

  useEffect(() => {
    loadData()
    styleTagsAPI.list().then(r => setTags(r.data.results || r.data))
    techniciansAPI.list().then(r => setTechs(r.data.results || r.data))
  }, [])

  useEffect(() => { loadData() }, [filters])

  const loadData = () => {
    const params = {}
    if (filters.shape) params.shape = filters.shape
    if (filters.occasion) params.occasion = filters.occasion
    if (filters.tag) params.tag = filters.tag
    if (filters.search) params.search = filters.search
    designsAPI.list(params).then(r => setDesigns(r.data.results || r.data))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => {
      if (v !== null && v !== '') fd.append(k, v)
    })
    const action = selected ? designsAPI.update(selected.id, fd) : designsAPI.create(fd)
    action.then(() => {
      loadData()
      setShowModal(false)
      setSelected(null)
      resetForm()
    })
  }

  const resetForm = () => setForm({
    name: '', nail_shape: 'oval', color_system: '', decoration: '',
    occasion: 'daily', description: '', technician: '', price: '', image: null
  })

  const editDesign = (d) => {
    setSelected(d)
    setForm({
      name: d.name, nail_shape: d.nail_shape, color_system: d.color_system,
      decoration: d.decoration, occasion: d.occasion, description: d.description || '',
      technician: d.technician || '', price: d.price, image: null
    })
    setShowModal(true)
  }

  const deleteDesign = (id) => {
    if (confirm('确认删除该款式？')) {
      designsAPI.delete(id).then(() => loadData())
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>款式图库</h2>
          <p className="text-gray">管理所有美甲款式，上传时自动标注风格标签</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setSelected(null); resetForm(); setShowModal(true) }}>
          + 上传新款式
        </button>
      </div>

      <div className="filter-bar">
        <input className="input" placeholder="搜索款式名、色系、装饰..."
          style={{ width: 260 }}
          value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value })} />
        <select className="select" value={filters.shape}
          onChange={e => setFilters({ ...filters, shape: e.target.value })}>
          <option value="">全部甲型</option>
          {NAIL_SHAPES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select className="select" value={filters.occasion}
          onChange={e => setFilters({ ...filters, occasion: e.target.value })}>
          <option value="">全部场合</option>
          {OCCASIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select className="select" value={filters.tag}
          onChange={e => setFilters({ ...filters, tag: e.target.value })}>
          <option value="">全部风格</option>
          {tags.map(t => <option key={t.id} value={t.name}>{t.name}</option>)}
        </select>
      </div>

      {designs.length > 0 ? (
        <div className="design-grid">
          {designs.map(d => (
            <div key={d.id} className="design-card" onClick={() => editDesign(d)}>
              <div className="design-image">💅</div>
              <div className="design-info">
                <h4>{d.name}</h4>
                <div className="design-meta">
                  {(d.style_tags_data || []).map(t => (
                    <span key={t.id} className="tag-chip" style={{ background: t.color }}>{t.name}</span>
                  ))}
                </div>
                <div className="fs-12 text-gray mb-4">
                  {getShapeLabel(d.nail_shape)} · {d.color_system} · {getOccasionLabel(d.occasion)}
                </div>
                <div className="fs-12 text-gray mb-8">装饰：{d.decoration}</div>
                <div className="design-footer">
                  <span className="price">¥{d.price}</span>
                  <span className="tech-name">{d.technician_name || '未指定'}</span>
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
                  <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); editDesign(d) }}>编辑</button>
                  <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); deleteDesign(d.id) }}>删除</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="icon">🎨</div>
          <p>暂无款式，点击"上传新款式"添加</p>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selected ? '编辑款式' : '上传新款式'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>款式图片</label>
                  <input type="file" className="input" accept="image/*"
                    onChange={e => setForm({ ...form, image: e.target.files[0] })} />
                  <p className="fs-12 text-gray mt-4">上传后系统将根据信息自动归类风格标签</p>
                </div>
                <div className="form-group">
                  <label>款式名称 *</label>
                  <input className="input" required value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>甲型</label>
                    <select className="select" value={form.nail_shape}
                      onChange={e => setForm({ ...form, nail_shape: e.target.value })}>
                      {NAIL_SHAPES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>适用场合</label>
                    <select className="select" value={form.occasion}
                      onChange={e => setForm({ ...form, occasion: e.target.value })}>
                      {OCCASIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>色系 *</label>
                    <input className="input" required placeholder="如：粉色系、蓝色系、奶茶色" value={form.color_system}
                      onChange={e => setForm({ ...form, color_system: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>参考价格</label>
                    <input type="number" className="input" value={form.price}
                      onChange={e => setForm({ ...form, price: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>装饰元素 *</label>
                  <input className="input" required placeholder="如：闪钻、手绘、珍珠、金箔等" value={form.decoration}
                    onChange={e => setForm({ ...form, decoration: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>上传美甲师</label>
                  <select className="select" value={form.technician}
                    onChange={e => setForm({ ...form, technician: e.target.value })}>
                    <option value="">请选择</option>
                    {techs.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>描述</label>
                  <textarea className="textarea" rows="3" value={form.description}
                    onChange={e => setForm({ ...form, description: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary">{selected ? '保存修改' : '上传款式'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
