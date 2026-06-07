import React, { useState, useEffect } from 'react'
import { statisticsAPI, renderStars, getMemberLevelMeta } from '../utils/api.js'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer, PieChart, Pie, Cell, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'

const COLORS = ['hotpink', 'rebeccapurple', 'darkcyan', 'mediumseagreen', 'darkorange', 'crimson', 'slateblue', 'chocolate']
const MEMBER_COLORS = ['#9ca3af', '#6b7280', '#f59e0b', '#8b5cf6']
const RISK_COLORS2 = ['#10b981', '#f59e0b', '#ef4444']

export default function StatisticsPage() {
  const [tab, setTab] = useState('color')
  const [colorRanking, setColorRanking] = useState([])
  const [lifecycle, setLifecycle] = useState([])
  const [trend, setTrend] = useState(null)
  const [efficiency, setEfficiency] = useState([])
  const [overview, setOverview] = useState(null)
  const [memberDist, setMemberDist] = useState([])
  const [repurchaseData, setRepurchaseData] = useState(null)
  const [churnTrend, setChurnTrend] = useState(null)

  useEffect(() => {
    statisticsAPI.colorRanking(6).then(r => setColorRanking(r.data))
    statisticsAPI.designLifecycle().then(r => setLifecycle(r.data))
    statisticsAPI.preferenceTrend(6).then(r => setTrend(r.data))
    statisticsAPI.technicianEfficiency(3).then(r => setEfficiency(r.data))
    statisticsAPI.overview().then(r => setOverview(r.data))
    statisticsAPI.memberLevelDistribution().then(r => setMemberDist(r.data))
    statisticsAPI.repurchaseInterval().then(r => setRepurchaseData(r.data))
    statisticsAPI.churnRiskTrend(6).then(r => setChurnTrend(r.data))
  }, [])

  const maxColor = colorRanking[0]?.count || 1

  const lifecycleChart = lifecycle.map(d => ({
    name: d.name.length > 8 ? d.name.slice(0, 8) + '...' : d.name,
    预约次数: d.appt_count,
    平均维持天数: d.avg_duration,
    平均满意度: d.avg_satisfaction * 20,
  }))

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>统计分析</h2>
          <p className="text-gray">全面了解店铺经营情况和顾客偏好变化</p>
        </div>
      </div>

      {overview && (
        <div className="grid grid-4 mb-24">
          <div className="stat-card">
            <h3>总顾客数</h3>
            <div className="value">{overview.total_customers}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: 'rebeccapurple' }}>
            <h3>款式总数</h3>
            <div className="value">{overview.total_designs}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: 'darkcyan' }}>
            <h3>作品存档</h3>
            <div className="value">{overview.total_works}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: 'mediumseagreen' }}>
            <h3>平均满意度</h3>
            <div className="value">{overview.avg_satisfaction.toFixed(2)}</div>
          </div>
        </div>
      )}

      {overview && (
        <div className="grid grid-3 mb-24">
          <div className="stat-card" style={{ borderLeftColor: '#ef4444' }}>
            <h3>🔴 高风险顾客</h3>
            <div className="value" style={{ color: '#ef4444' }}>{overview.high_risk_count || 0}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: '#f59e0b' }}>
            <h3>🟡 中风险顾客</h3>
            <div className="value" style={{ color: '#f59e0b' }}>{overview.medium_risk_count || 0}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: '#10b981' }}>
            <h3>🟢 低风险顾客</h3>
            <div className="value" style={{ color: '#10b981' }}>{overview.low_risk_count || 0}</div>
          </div>
        </div>
      )}

      <div className="tabs mb-24">
        <button className={`tab ${tab === 'color' ? 'active' : ''}`} onClick={() => setTab('color')}>🔥 热门色系排行</button>
        <button className={`tab ${tab === 'lifecycle' ? 'active' : ''}`} onClick={() => setTab('lifecycle')}>📊 款式生命周期</button>
        <button className={`tab ${tab === 'trend' ? 'active' : ''}`} onClick={() => setTab('trend')}>📈 顾客偏好变迁</button>
        <button className={`tab ${tab === 'efficiency' ? 'active' : ''}`} onClick={() => setTab('efficiency')}>👩‍💼 美甲师产出效率</button>
        <button className={`tab ${tab === 'member' ? 'active' : ''}`} onClick={() => setTab('member')}>👑 会员等级分布</button>
        <button className={`tab ${tab === 'repurchase' ? 'active' : ''}`} onClick={() => setTab('repurchase')}>🔄 复购间隔</button>
        <button className={`tab ${tab === 'churn' ? 'active' : ''}`} onClick={() => setTab('churn')}>⚠️ 流失风险趋势</button>
      </div>

      {tab === 'color' && (
        <div className="grid grid-2">
          <div className="chart-container">
            <h3 className="chart-title">🔥 热门色系排行 TOP 10</h3>
            {colorRanking.length > 0 ? (
              <ul className="ranking-list">
                {colorRanking.slice(0, 10).map((c, i) => (
                  <li key={i} className="ranking-item">
                    <span className="rank-num">{i + 1}</span>
                    <span className="rank-name">{c.color}</span>
                    <div className="rank-bar-wrap">
                      <div className="rank-bar" style={{ width: `${(c.count / maxColor) * 100}%` }}></div>
                    </div>
                    <span className="rank-count">{c.count}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>
            )}
          </div>
          <div className="chart-container">
            <h3 className="chart-title">色系分布</h3>
            <ResponsiveContainer width="100%" height={360}>
              <PieChart>
                <Pie
                  data={colorRanking.slice(0, 8)}
                  dataKey="count"
                  nameKey="color"
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  label={({ color, percent }) => `${color} ${(percent * 100).toFixed(0)}%`}
                >
                  {colorRanking.slice(0, 8).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {tab === 'lifecycle' && (
        <div>
          <div className="chart-container mb-24">
            <h3 className="chart-title">📊 款式表现对比（预约次数、维持天数、满意度）</h3>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={lifecycleChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="预约次数" fill="hotpink" radius={[4, 4, 0, 0]} />
                <Bar dataKey="平均维持天数" fill="rebeccapurple" radius={[4, 4, 0, 0]} />
                <Bar dataKey="平均满意度" fill="mediumseagreen" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3 className="chart-title">款式详细列表</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>款式名称</th>
                  <th>预约次数</th>
                  <th>平均维持天数</th>
                  <th>平均满意度</th>
                </tr>
              </thead>
              <tbody>
                {lifecycle.length > 0 ? lifecycle.map(d => (
                  <tr key={d.id}>
                    <td className="fw-500">{d.name}</td>
                    <td>{d.appt_count}</td>
                    <td>{d.avg_duration} 天</td>
                    <td><span className="stars">{renderStars(Math.round(d.avg_satisfaction))}</span> ({d.avg_satisfaction})</td>
                  </tr>
                )) : (
                  <tr><td colSpan="4"><div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'trend' && trend && (
        <div className="grid grid-2">
          <div className="chart-container">
            <h3 className="chart-title">📈 色系偏好变迁（近6个月）</h3>
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={trend.months.map((m, i) => {
                const row = { month: m }
                trend.color_trend.forEach(ct => { row[ct.name] = ct.data[i] || 0 })
                return row
              })}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                {trend.color_trend.map((ct, i) => (
                  <Line key={i} type="monotone" dataKey={ct.name} stroke={COLORS[i % COLORS.length]} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-container">
            <h3 className="chart-title">🎨 风格偏好变迁（近6个月）</h3>
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={trend.months.map((m, i) => {
                const row = { month: m }
                trend.style_trend.forEach(st => { row[st.name] = st.data[i] || 0 })
                return row
              })}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                {trend.style_trend.map((st, i) => (
                  <Line key={i} type="monotone" dataKey={st.name} stroke={COLORS[(i + 3) % COLORS.length]} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-container" style={{ gridColumn: '1 / -1' }}>
            <h3 className="chart-title">📅 月度作品完成趋势</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trend.total_monthly.map(m => ({
                月份: new Date(m.month).toLocaleDateString('zh-CN', { month: 'numeric' }) + '月',
                作品数: m.count
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="月份" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="作品数" fill="hotpink" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {tab === 'efficiency' && (
        <div className="grid grid-2">
          <div className="chart-container">
            <h3 className="chart-title">👩‍💼 美甲师作品数量对比</h3>
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={efficiency} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={80} />
                <Tooltip />
                <Bar dataKey="works_count" name="完成作品数" fill="hotpink" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-container">
            <h3 className="chart-title">⭐ 美甲师综合表现雷达图</h3>
            <ResponsiveContainer width="100%" height={360}>
              <RadarChart data={efficiency.map(t => ({
                subject: t.name,
                作品数: Math.min(t.works_count * 10, 100),
                满意度: (t.avg_satisfaction || 0) * 20,
                维持度: Math.min((t.avg_duration || 0) * 3, 100),
              }))}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar name="作品数" dataKey="作品数" stroke="hotpink" fill="hotpink" fillOpacity={0.5} />
                <Radar name="满意度" dataKey="满意度" stroke="mediumseagreen" fill="mediumseagreen" fillOpacity={0.5} />
                <Radar name="维持度" dataKey="维持度" stroke="rebeccapurple" fill="rebeccapurple" fillOpacity={0.5} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <h3 className="chart-title">美甲师产出效率明细（近3个月）</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>美甲师</th>
                  <th>完成作品数</th>
                  <th>完成预约数</th>
                  <th>平均满意度</th>
                  <th>平均维持天数</th>
                </tr>
              </thead>
              <tbody>
                {efficiency.length > 0 ? efficiency.map(t => (
                  <tr key={t.id}>
                    <td className="fw-500">{t.name}</td>
                    <td>{t.works_count}</td>
                    <td>{t.appointments_count}</td>
                    <td><span className="stars">{renderStars(Math.round(t.avg_satisfaction))}</span> ({t.avg_satisfaction})</td>
                    <td>{t.avg_duration} 天</td>
                  </tr>
                )) : (
                  <tr><td colSpan="5"><div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'member' && (
        <div className="grid grid-2">
          <div className="chart-container">
            <h3 className="chart-title">👑 会员等级分布</h3>
            {memberDist.length > 0 ? (
              <ResponsiveContainer width="100%" height={360}>
                <PieChart>
                  <Pie
                    data={memberDist}
                    dataKey="count"
                    nameKey="level_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={120}
                    label={({ level_name, percent }) => `${level_name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {memberDist.map((_, i) => (
                      <Cell key={i} fill={MEMBER_COLORS[i % MEMBER_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><div className="icon">👑</div><p>暂无数据</p></div>
            )}
          </div>
          <div className="chart-container">
            <h3 className="chart-title">📊 各等级会员数量对比</h3>
            {memberDist.length > 0 ? (
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={memberDist}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="level_name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" name="会员人数" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>
            )}
          </div>
        </div>
      )}

      {tab === 'repurchase' && repurchaseData && (
        <div className="grid grid-2">
          <div className="chart-container">
            <h3 className="chart-title">🔄 平均复购间隔</h3>
            <div className="text-center" style={{ padding: '40px 0' }}>
              <div className="fs-14 text-gray mb-8">顾客平均复购间隔</div>
              <div className="fs-48 fw-700" style={{ color: '#ec4899' }}>
                {repurchaseData.avg_interval || 0}
                <span className="fs-20" style={{ marginLeft: 8 }}>天</span>
              </div>
            </div>
          </div>
          <div className="chart-container">
            <h3 className="chart-title">📊 复购间隔分布</h3>
            {repurchaseData.distribution && repurchaseData.distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={repurchaseData.distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" name="顾客数" fill="hotpink" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>
            )}
          </div>
        </div>
      )}

      {tab === 'churn' && churnTrend && (
        <div>
          <div className="chart-container mb-24">
            <h3 className="chart-title">⚠️ 流失风险趋势（近6个月）</h3>
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={churnTrend.months.map((m, i) => {
                const row = { month: m }
                churnTrend.trend_data.forEach(ct => { row[ct.name] = ct.data[i] || 0 })
                return row
              })}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                {churnTrend.trend_data.map((ct, i) => (
                  <Line key={i} type="monotone" dataKey={ct.name} stroke={RISK_COLORS2[i % RISK_COLORS2.length]} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-container">
            <h3 className="chart-title">💡 说明</h3>
            <div className="fs-14 text-gray lh-20">
              <p className="mb-8"><span style={{ color: '#10b981', fontWeight: 600 }}>🟢 低风险（0-39分）</span>：顾客活跃度高，满意度良好，正常维护即可</p>
              <p className="mb-8"><span style={{ color: '#f59e0b', fontWeight: 600 }}>🟡 中风险（40-69分）</span>：顾客出现流失倾向，建议两周内联系，推送新款资讯和会员活动</p>
              <p><span style={{ color: '#ef4444', fontWeight: 600 }}>🔴 高风险（70-100分）</span>：顾客流失风险极高，需紧急回访，提供专属优惠或赠送小礼品</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
