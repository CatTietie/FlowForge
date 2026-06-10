import React from 'react'
import { useLocale } from '../../i18n/LocaleContext'

function formatDuration(seconds, t) {
  if (seconds == null) return '--'
  if (seconds < 60) return `${Math.round(seconds)}${t('stats.unit.seconds')}`
  if (seconds < 3600) return `${Math.round(seconds / 60)}${t('stats.unit.minutes')}`
  return `${(seconds / 3600).toFixed(1)}${t('stats.unit.hours')}`
}

export default function SummaryCards({ avgDuration, timeoutRate, backlog }) {
  const { t } = useLocale()

  return (
    <div className="stats-cards-row">
      <div className="stats-card">
        <div className="stats-card-label">{t('stats.card.avgDuration')}</div>
        <div className="stats-card-value">{formatDuration(avgDuration?.overall_avg_seconds, t)}</div>
      </div>
      <div className="stats-card stats-card-warning">
        <div className="stats-card-label">{t('stats.card.timeoutRate')}</div>
        <div className="stats-card-value">{timeoutRate?.rate_percent ?? 0}%</div>
      </div>
      <div className="stats-card">
        <div className="stats-card-label">{t('stats.card.completedNodes')}</div>
        <div className="stats-card-value">{timeoutRate?.total_completed ?? 0}</div>
      </div>
      <div className="stats-card stats-card-danger">
        <div className="stats-card-label">{t('stats.card.backlog')}</div>
        <div className="stats-card-value">{backlog?.total_pending ?? 0}</div>
      </div>
    </div>
  )
}
