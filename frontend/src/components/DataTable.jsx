import React from 'react'
import EmptyState from './EmptyState.jsx'

export default function DataTable({ columns, data, rowKey = 'id', emptyIcon, emptyText, onRowClick, className = '' }) {
  if (!data || data.length === 0) {
    return (
      <table className={`table ${className}`}>
        <thead>
          <tr>
            {columns.map((col, i) => (
              <th key={col.key || i} style={col.style}>{col.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={columns.length}>
              <EmptyState icon={emptyIcon} text={emptyText || '暂无数据'} />
            </td>
          </tr>
        </tbody>
      </table>
    )
  }

  return (
    <table className={`table ${className}`}>
      <thead>
        <tr>
          {columns.map((col, i) => (
            <th key={col.key || i} style={col.style}>{col.title}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIdx) => (
          <tr
            key={row[rowKey] || rowIdx}
            onClick={onRowClick ? () => onRowClick(row, rowIdx) : undefined}
            style={onRowClick ? { cursor: 'pointer' } : undefined}
          >
            {columns.map((col, colIdx) => (
              <td key={col.key || colIdx} style={col.cellStyle}>
                {col.render ? col.render(row[col.key], row, rowIdx) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
