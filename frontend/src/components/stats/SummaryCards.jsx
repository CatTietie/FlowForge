import React from 'react'

function formatDuration(seconds) {
  if (seconds == null) return '--'
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
  return `${(seconds / 3600).toFixed(1)}小时`
}

export default function SummaryCards({ avgDuration, timeoutRate, backlog }) {
  return (
    <div className="stats-cards-row">
      <div className="stats-card">
        <div className="stats-card-label">平均审批时长</div>
        <div className="stats-card-value">{formatDuration(avgDuration?.overall_avg_seconds)}</div>
      </div>
      <div className="stats-card stats-card-warning">
        <div className="stats-card-label">超时率</div>
        <div className="stats-card-value">{timeoutRate?.rate_percent ?? 0}%</div>
      </div>
      <div className="stats-card">
        <div className="stats-card-label">已完成节点数</div>
        <div className="stats-card-value">{timeoutRate?.total_completed ?? 0}</div>
      </div>
      <div className="stats-card stats-card-danger">
        <div className="stats-card-label">待办积压</div>
        <div className="stats-card-value">{backlog?.total_pending ?? 0}</div>
      </div>
    </div>
  )
}
