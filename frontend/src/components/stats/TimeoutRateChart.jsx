import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function TimeoutRateChart({ data }) {
  const chartData = (data?.by_node || []).map(item => ({
    name: item.node_id,
    rate: item.rate_percent,
    total: item.total,
    exceeded: item.exceeded,
  }))

  return (
    <div className="stats-chart-section">
      <h3>各节点超时率</h3>
      {chartData.length === 0 ? (
        <div className="stats-empty">暂无超时数据</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis fontSize={12} unit="%" />
            <Tooltip formatter={(value, name) => [`${value}%`, '超时率']} />
            <Bar dataKey="rate" name="超时率">
              {chartData.map((entry, idx) => (
                <Cell key={idx} fill={entry.rate > 50 ? '#e53935' : entry.rate > 20 ? '#ff9800' : '#43a047'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
