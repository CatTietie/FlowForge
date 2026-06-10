import React from 'react'
import { useLocale } from '../../i18n/LocaleContext'

function formatElapsed(hours, t) {
  if (hours < 1) return `${Math.round(hours * 60)}${t('stats.unit.minutes')}`
  return `${hours.toFixed(1)}${t('stats.unit.hours')}`
}

export default function SlaViolationsTable({ data }) {
  const { t, locale } = useLocale()
  const items = data?.sla_at_risk || []

  return (
    <div className="stats-chart-section">
      <h3>{t('stats.sla.title')}</h3>
      {items.length === 0 ? (
        <div className="stats-empty">{t('stats.sla.noRisk')}</div>
      ) : (
        <div className="stats-table-wrapper">
          <table className="stats-table">
            <thead>
              <tr>
                <th>{t('stats.sla.instanceId')}</th>
                <th>{t('stats.sla.node')}</th>
                <th>{t('stats.sla.assignee')}</th>
                <th>{t('stats.sla.enterTime')}</th>
                <th>{t('stats.sla.slaLimit')}</th>
                <th>{t('stats.sla.elapsed')}</th>
                <th>{t('stats.sla.status')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const exceeded = item.elapsed_hours > item.sla_hours
                return (
                  <tr key={idx} className={exceeded ? 'stats-row-exceeded' : 'stats-row-warning'}>
                    <td>{item.process_instance_id}</td>
                    <td>{item.node_id}</td>
                    <td>{item.assignee || '--'}</td>
                    <td>{item.enter_time ? new Date(item.enter_time).toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US') : '--'}</td>
                    <td>{item.sla_hours}{t('stats.unit.hours')}</td>
                    <td>{formatElapsed(item.elapsed_hours, t)}</td>
                    <td>
                      <span className={`stats-sla-badge ${exceeded ? 'stats-sla-exceeded' : 'stats-sla-warning'}`}>
                        {exceeded ? t('stats.sla.exceeded') : t('stats.sla.atRisk')}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
