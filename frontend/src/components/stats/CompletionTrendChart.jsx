import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useLocale } from '../../i18n/LocaleContext'

export default function CompletionTrendChart({ data, granularity, onGranularityChange }) {
  const { t } = useLocale()

  const granularityLabels = {
    day: t('stats.granularity.day'),
    week: t('stats.granularity.week'),
    month: t('stats.granularity.month'),
  }

  return (
    <div className="stats-chart-section">
      <div className="stats-chart-header">
        <h3>{t('stats.chart.completionTrend')}</h3>
        <div className="stats-granularity-toggle">
          {['day', 'week', 'month'].map(g => (
            <button
              key={g}
              className={`btn ${granularity === g ? 'btn-primary' : 'btn-secondary'} sim-btn-sm`}
              onClick={() => onGranularityChange(g)}
            >
              {granularityLabels[g]}
            </button>
          ))}
        </div>
      </div>
      {data.length === 0 ? (
        <div className="stats-empty">{t('stats.noData')}</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="completed" name={t('stats.legend.completed')} stroke="#43a047" strokeWidth={2} />
            <Line type="monotone" dataKey="rejected" name={t('stats.legend.rejected')} stroke="#e53935" strokeWidth={2} />
            <Line type="monotone" dataKey="returned" name={t('stats.legend.returned')} stroke="#ff9800" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
