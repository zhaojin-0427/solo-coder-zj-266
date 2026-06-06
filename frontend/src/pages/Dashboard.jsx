import React, { useState, useEffect } from 'react'
import { statisticsAPI, appointmentsAPI } from '../utils/api.js'
import dayjs from 'dayjs'

export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [todayAppts, setTodayAppts] = useState([])

  useEffect(() => {
    statisticsAPI.overview().then(r => setOverview(r.data))
    const today = dayjs().format('YYYY-MM-DD')
    appointmentsAPI.list({ date_from: today, date_to: today }).then(r => setTodayAppts(r.data.results || r.data))
  }, [])

  if (!overview) return null

  const stats = [
    { label: '总顾客数', value: overview.total_customers, icon: '👥', sub: '注册会员' },
    { label: '款式总数', value: overview.total_designs, icon: '🎨', sub: '款式图库' },
    { label: '作品存档', value: overview.total_works, icon: '📸', sub: '历史作品' },
    { label: '待确认预约', value: overview.pending_appointments, icon: '⏰', sub: '待处理' },
    { label: '今日预约', value: overview.today_appointments, icon: '📅', sub: '今日安排' },
    { label: '本月作品', value: overview.month_works, icon: '✨', sub: '本月完成' },
    { label: '平均满意度', value: overview.avg_satisfaction.toFixed(2), icon: '⭐', sub: '5分满分' },
  ]

  const statusLabel = (s) => {
    const map = { pending: '待确认', confirmed: '已确认', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }
    return map[s] || s
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>概览</h2>
          <p className="text-gray">欢迎回来，查看今日工作情况</p>
        </div>
      </div>

      <div className="grid grid-4 mb-24">
        {stats.map(s => (
          <div key={s.label} className="stat-card">
            <div className="flex items-start gap-10">
              <div>
                <h3>{s.icon} {s.label}</h3>
                <div className="value">{s.value}</div>
                <div className="sub">{s.sub}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 className="fs-16 mb-14 text-dark">📅 今日预约</h3>
        {todayAppts.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>时间</th>
                <th>顾客</th>
                <th>美甲师</th>
                <th>款式</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {todayAppts.map(a => (
                <tr key={a.id}>
                  <td>{a.appointment_time}</td>
                  <td>{a.customer_name} ({a.customer_phone})</td>
                  <td>{a.technician_name}</td>
                  <td>{a.design_name || '-'}</td>
                  <td><span className={`badge badge-${a.status}`}>{statusLabel(a.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <div className="icon">📭</div>
            <p>今日暂无预约</p>
          </div>
        )}
      </div>
    </div>
  )
}
