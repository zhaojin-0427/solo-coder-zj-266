import React from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import DesignGallery from './pages/DesignGallery.jsx'
import AppointmentPage from './pages/AppointmentPage.jsx'
import CustomerPage from './pages/CustomerPage.jsx'
import WorkArchive from './pages/WorkArchive.jsx'
import StatisticsPage from './pages/StatisticsPage.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CustomerOpsPage from './pages/CustomerOpsPage.jsx'
import TryOnLab from './pages/TryOnLab.jsx'

export default function App() {
  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>💅 美甲管理系统</h1>
          <p>款式设计 · 偏好管理</p>
        </div>
        <ul className="nav-menu">
          <li>
            <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">🏠</span> 概览
            </NavLink>
          </li>
          <li>
            <NavLink to="/customer-ops" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">🎯</span> 客户运营
            </NavLink>
          </li>
          <li>
            <NavLink to="/try-on" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">✨</span> 试甲实验室
            </NavLink>
          </li>
          <li>
            <NavLink to="/designs" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">🎨</span> 款式图库
            </NavLink>
          </li>
          <li>
            <NavLink to="/appointments" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">📅</span> 预约管理
            </NavLink>
          </li>
          <li>
            <NavLink to="/customers" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">👥</span> 顾客档案
            </NavLink>
          </li>
          <li>
            <NavLink to="/works" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">📸</span> 作品存档
            </NavLink>
          </li>
          <li>
            <NavLink to="/statistics" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">📊</span> 统计分析
            </NavLink>
          </li>
        </ul>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/customer-ops" element={<CustomerOpsPage />} />
          <Route path="/try-on" element={<TryOnLab />} />
          <Route path="/designs" element={<DesignGallery />} />
          <Route path="/appointments" element={<AppointmentPage />} />
          <Route path="/customers" element={<CustomerPage />} />
          <Route path="/works" element={<WorkArchive />} />
          <Route path="/statistics" element={<StatisticsPage />} />
        </Routes>
      </main>
    </div>
  )
}
