import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useLocale } from '../../i18n/LocaleContext'

export default function BacklogChart({ data }) {
  const { t } = useLocale()

  const chartData = (data?.by_node || []).map(item => ({
    name: `${item.node_id}${item.assignee ? ` (${item.assignee})` : ''}`,
    count: item.count,
  }))

  return (
    <div className="stats-chart-section">
      <h3>{t('stats.chart.backlogDistribution')}</h3>
      {chartData.length === 0 ? (
        <div className="stats-empty">{t('stats.noBacklog')}</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 20, left: 80, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" fontSize={12} />
            <YAxis type="category" dataKey="name" fontSize={12} width={70} />
            <Tooltip />
            <Bar dataKey="count" name={t('stats.legend.backlogCount')} fill="#4a7cff" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
