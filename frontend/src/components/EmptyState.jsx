import React from 'react'

export default function EmptyState({ icon = '📭', text = '暂无数据', children }) {
  return (
    <div className="empty-state">
      <div className="icon">{icon}</div>
      <p>{text}</p>
      {children}
    </div>
  )
}
