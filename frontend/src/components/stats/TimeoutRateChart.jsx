import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useLocale } from '../../i18n/LocaleContext'

export default function TimeoutRateChart({ data }) {
  const { t } = useLocale()

  const chartData = (data?.by_node || []).map(item => ({
    name: item.node_id,
    rate: item.rate_percent,
    total: item.total,
    exceeded: item.exceeded,
  }))

  return (
    <div className="stats-chart-section">
      <h3>{t('stats.chart.timeoutRate')}</h3>
      {chartData.length === 0 ? (
        <div className="stats-empty">{t('stats.noTimeoutData')}</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis fontSize={12} unit="%" />
            <Tooltip formatter={(value) => [`${value}%`, t('stats.card.timeoutRate')]} />
            <Bar dataKey="rate" name={t('stats.card.timeoutRate')}>
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
