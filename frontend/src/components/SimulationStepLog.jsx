import React from 'react'

export default function SimulationStepLog({ steps, visitedNodeIds, allNodeIds, unvisitedNodeIds, coveragePercent }) {
  return (
    <div className="sim-step-log">
      <h4>执行步骤</h4>
      {(!steps || steps.length === 0) && (
        <p className="sim-empty-hint">尚未开始模拟</p>
      )}
      <div className="sim-steps-list">
        {steps && steps.map((step, idx) => (
          <div key={idx} className={`sim-step-item sim-step-${step.status}`}>
            <div className="sim-step-header">
              <span className="sim-step-index">#{step.step_index + 1}</span>
              <span className="sim-step-node">{step.node_id}</span>
              <span className={`sim-step-status sim-status-${step.status}`}>{step.status}</span>
            </div>
            <div className="sim-step-details">
              <span className="sim-step-type">{step.node_type}</span>
              {step.assignee && <span className="sim-step-assignee">审批人: {step.assignee}</span>}
              {step.decision_made && <span className="sim-step-decision">决策: {step.decision_made}</span>}
            </div>

            {step.condition_evaluations && step.condition_evaluations.length > 0 && (
              <div className="sim-condition-details">
                <div className="sim-condition-title">条件求值:</div>
                {step.condition_evaluations.map((ev, i) => (
                  <div key={i} className={`sim-condition-eval ${ev.result ? 'sim-eval-true' : 'sim-eval-false'}`}>
                    <code>{ev.expression}</code>
                    <span className="sim-eval-breakdown">
                      {ev.field_name}={JSON.stringify(ev.field_value)} {ev.operator} {JSON.stringify(ev.compare_value)}
                    </span>
                    <span className="sim-eval-result">{ev.result ? '✓ 匹配' : '✗ 不匹配'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {coveragePercent !== undefined && steps && steps.length > 0 && (
        <div className="sim-coverage">
          <h4>覆盖率分析</h4>
          <div className="sim-coverage-bar-wrapper">
            <div className="sim-coverage-bar" style={{ width: `${coveragePercent}%` }}></div>
          </div>
          <div className="sim-coverage-text">{coveragePercent}% ({visitedNodeIds?.length || 0}/{allNodeIds?.length || 0} 节点)</div>
          {unvisitedNodeIds && unvisitedNodeIds.length > 0 && (
            <div className="sim-coverage-unvisited">
              <span>未覆盖节点: </span>
              {unvisitedNodeIds.map(id => <span key={id} className="sim-unvisited-tag">{id}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
