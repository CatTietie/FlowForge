import React from 'react'

function formatElapsed(hours) {
  if (hours < 1) return `${Math.round(hours * 60)}分钟`
  return `${hours.toFixed(1)}小时`
}

export default function SlaViolationsTable({ data }) {
  const items = data?.sla_at_risk || []

  return (
    <div className="stats-chart-section">
      <h3>SLA 风险实例</h3>
      {items.length === 0 ? (
        <div className="stats-empty">无 SLA 风险实例</div>
      ) : (
        <div className="stats-table-wrapper">
          <table className="stats-table">
            <thead>
              <tr>
                <th>实例ID</th>
                <th>节点</th>
                <th>审批人</th>
                <th>进入时间</th>
                <th>SLA时限</th>
                <th>已用时</th>
                <th>状态</th>
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
                    <td>{item.enter_time ? new Date(item.enter_time).toLocaleString('zh-CN') : '--'}</td>
                    <td>{item.sla_hours}小时</td>
                    <td>{formatElapsed(item.elapsed_hours)}</td>
                    <td>
                      <span className={`stats-sla-badge ${exceeded ? 'stats-sla-exceeded' : 'stats-sla-warning'}`}>
                        {exceeded ? '已超时' : '即将超时'}
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
