import React from 'react'

export default function StatusTag({ label, cls = '', color, style }) {
  const customStyle = color
    ? { background: color + '22', color, ...style }
    : style
  return (
    <span className={`badge ${cls}`} style={customStyle}>
      {label}
    </span>
  )
}
