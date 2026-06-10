import React from 'react'
import { useLocale } from '../i18n/LocaleContext'
import { resolveNodeName } from '../i18n/resolveI18n'

export default function SimulationStepLog({ steps, visitedNodeIds, allNodeIds, unvisitedNodeIds, coveragePercent, nodes }) {
  const { t, locale } = useLocale()

  function getNodeDisplayName(nodeId) {
    if (!nodes) return nodeId
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return nodeId
    return resolveNodeName(node, locale)
  }

  return (
    <div className="sim-step-log">
      <h4>{t('simulator.stepLog.title')}</h4>
      {(!steps || steps.length === 0) && (
        <p className="sim-empty-hint">{t('simulator.stepLog.empty')}</p>
      )}
      <div className="sim-steps-list">
        {steps && steps.map((step, idx) => (
          <div key={idx} className={`sim-step-item sim-step-${step.status}`}>
            <div className="sim-step-header">
              <span className="sim-step-index">#{step.step_index + 1}</span>
              <span className="sim-step-node">{getNodeDisplayName(step.node_id)}</span>
              <span className={`sim-step-status sim-status-${step.status}`}>{step.status}</span>
            </div>
            <div className="sim-step-details">
              <span className="sim-step-type">{step.node_type}</span>
              {step.assignee && <span className="sim-step-assignee">{t('stepLog.assignee')}: {step.assignee}</span>}
              {step.decision_made && <span className="sim-step-decision">{t('stepLog.decision')}: {step.decision_made}</span>}
            </div>

            {step.condition_evaluations && step.condition_evaluations.length > 0 && (
              <div className="sim-condition-details">
                <div className="sim-condition-title">{t('simulator.conditionEval')}:</div>
                {step.condition_evaluations.map((ev, i) => (
                  <div key={i} className={`sim-condition-eval ${ev.result ? 'sim-eval-true' : 'sim-eval-false'}`}>
                    <code>{ev.expression}</code>
                    <span className="sim-eval-breakdown">
                      {ev.field_name}={JSON.stringify(ev.field_value)} {ev.operator} {JSON.stringify(ev.compare_value)}
                    </span>
                    <span className="sim-eval-result">{ev.result ? '✓' : '✗'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {coveragePercent !== undefined && steps && steps.length > 0 && (
        <div className="sim-coverage">
          <h4>{t('simulator.coverage')}</h4>
          <div className="sim-coverage-bar-wrapper">
            <div className="sim-coverage-bar" style={{ width: `${coveragePercent}%` }}></div>
          </div>
          <div className="sim-coverage-text">{coveragePercent}% ({visitedNodeIds?.length || 0}/{allNodeIds?.length || 0})</div>
          {unvisitedNodeIds && unvisitedNodeIds.length > 0 && (
            <div className="sim-coverage-unvisited">
              <span>{t('simulator.unvisited')}: </span>
              {unvisitedNodeIds.map(id => <span key={id} className="sim-unvisited-tag">{getNodeDisplayName(id)}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
