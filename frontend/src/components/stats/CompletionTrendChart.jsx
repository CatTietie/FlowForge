import React, { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function CompletionTrendChart({ data, granularity, onGranularityChange }) {
  return (
    <div className="stats-chart-section">
      <div className="stats-chart-header">
        <h3>完成率趋势</h3>
        <div className="stats-granularity-toggle">
          {['day', 'week', 'month'].map(g => (
            <button
              key={g}
              className={`btn ${granularity === g ? 'btn-primary' : 'btn-secondary'} sim-btn-sm`}
              onClick={() => onGranularityChange(g)}
            >
              {{ day: '日', week: '周', month: '月' }[g]}
            </button>
          ))}
        </div>
      </div>
      {data.length === 0 ? (
        <div className="stats-empty">暂无数据</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="completed" name="完成" stroke="#43a047" strokeWidth={2} />
            <Line type="monotone" dataKey="rejected" name="拒绝" stroke="#e53935" strokeWidth={2} />
            <Line type="monotone" dataKey="returned" name="退回" stroke="#ff9800" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
