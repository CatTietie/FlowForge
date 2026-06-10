import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import SimulationFlowChart from '../components/SimulationFlowChart'
import SimulationStepLog from '../components/SimulationStepLog'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useLocale } from '../i18n/LocaleContext'
import { resolveNodeName } from '../i18n/resolveI18n'
import { SUPPORTED_LOCALES } from '../i18n/index'

export default function ProcessSimulator() {
  const [searchParams] = useSearchParams()
  const preselectedId = searchParams.get('id')
  const { t, locale } = useLocale()

  const [processes, setProcesses] = useState([])
  const [selectedProcId, setSelectedProcId] = useState(preselectedId || '')
  const [jsonInput, setJsonInput] = useState('')
  const [useJson, setUseJson] = useState(false)

  const [formFields, setFormFields] = useState([{ key: '', value: '' }])
  const [mode, setMode] = useState('step')

  const [definition, setDefinition] = useState(null)
  const [steps, setSteps] = useState([])
  const [decisions, setDecisions] = useState([])
  const [finalStatus, setFinalStatus] = useState(null)
  const [visitedNodeIds, setVisitedNodeIds] = useState([])
  const [allNodeIds, setAllNodeIds] = useState([])
  const [unvisitedNodeIds, setUnvisitedNodeIds] = useState([])
  const [coveragePercent, setCoveragePercent] = useState(0)
  const [waitingNodeId, setWaitingNodeId] = useState(null)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    fetch('/api/processes/definitions').then(r => r.json()).then(list => {
      setProcesses(list)
      if (preselectedId && list.find(p => p.id === Number(preselectedId))) {
        loadDefinition(Number(preselectedId), list)
      }
    })
  }, [])

  function loadDefinition(procId, list) {
    const proc = (list || processes).find(p => p.id === Number(procId))
    if (proc) {
      setDefinition(proc.definition_json)
      setJsonInput(JSON.stringify(proc.definition_json, null, 2))
    }
  }

  function handleSelectProcess(e) {
    const id = e.target.value
    setSelectedProcId(id)
    if (id) loadDefinition(Number(id))
    resetSimulation()
  }

  function handleJsonChange(e) {
    setJsonInput(e.target.value)
    try {
      const parsed = JSON.parse(e.target.value)
      setDefinition(parsed)
      setError(null)
    } catch {
      setDefinition(null)
    }
  }

  function addFormField() {
    setFormFields([...formFields, { key: '', value: '' }])
  }

  function removeFormField(idx) {
    setFormFields(formFields.filter((_, i) => i !== idx))
  }

  function updateFormField(idx, field, value) {
    const updated = [...formFields]
    updated[idx] = { ...updated[idx], [field]: value }
    setFormFields(updated)
  }

  function getFormData() {
    const data = {}
    formFields.forEach(f => {
      if (f.key.trim()) {
        const num = Number(f.value)
        data[f.key.trim()] = isNaN(num) || f.value.trim() === '' ? f.value : num
      }
    })
    return data
  }

  function resetSimulation() {
    setSteps([])
    setDecisions([])
    setFinalStatus(null)
    setVisitedNodeIds([])
    setAllNodeIds([])
    setUnvisitedNodeIds([])
    setCoveragePercent(0)
    setWaitingNodeId(null)
    setError(null)
    setRunning(false)
  }

  async function runSimulation(extraDecisions = []) {
    if (!definition) {
      setError(t('simulator.error.noDefinition') || '请先选择或输入流程定义')
      return
    }
    setError(null)
    setRunning(true)

    const allDecisions = [...decisions, ...extraDecisions]
    const formData = getFormData()

    try {
      const resp = await fetch('/api/processes/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          definition,
          form_data: formData,
          decisions: allDecisions,
          auto_approve: mode === 'auto',
        }),
      })
      if (!resp.ok) {
        const err = await resp.json()
        setError(err.detail || t('simulator.error.failed') || '模拟失败')
        setRunning(false)
        return
      }
      const data = await resp.json()
      setSteps(data.steps)
      setFinalStatus(data.final_status)
      setVisitedNodeIds(data.visited_node_ids)
      setAllNodeIds(data.all_node_ids)
      setUnvisitedNodeIds(data.unvisited_node_ids)
      setCoveragePercent(data.coverage_percent)
      setDecisions(allDecisions)

      if (data.final_status === 'waiting_for_decision') {
        const waitStep = data.steps[data.steps.length - 1]
        setWaitingNodeId(waitStep.node_id)
      } else {
        setWaitingNodeId(null)
      }
    } catch (e) {
      setError('Network error: ' + e.message)
    }
    setRunning(false)
  }

  function handleDecision(decision) {
    if (!waitingNodeId) return
    const newDecision = { node_id: waitingNodeId, decision }
    setWaitingNodeId(null)
    runSimulation([newDecision])
  }

  function handleStart() {
    resetSimulation()
    runSimulation([])
  }

  function getApprovalNodes() {
    if (!definition || !definition.nodes) return []
    return definition.nodes.filter(n => n.type === 'approval')
  }

  function updateNodeSla(nodeId, value) {
    const updated = {
      ...definition,
      nodes: definition.nodes.map(n =>
        n.id === nodeId ? { ...n, sla_hours: value === '' ? undefined : parseFloat(value) } : n
      ),
    }
    setDefinition(updated)
    setJsonInput(JSON.stringify(updated, null, 2))
  }

  function updateNodeName(nodeId, value) {
    const updated = {
      ...definition,
      nodes: definition.nodes.map(n =>
        n.id === nodeId ? { ...n, name: value || undefined } : n
      ),
    }
    setDefinition(updated)
    setJsonInput(JSON.stringify(updated, null, 2))
  }

  function updateNodeNameI18n(nodeId, localeCode, value) {
    const updated = {
      ...definition,
      nodes: definition.nodes.map(n => {
        if (n.id !== nodeId) return n
        const i18n = { ...(n.name_i18n || {}) }
        if (value) {
          i18n[localeCode] = value
        } else {
          delete i18n[localeCode]
        }
        return { ...n, name_i18n: Object.keys(i18n).length > 0 ? i18n : undefined }
      }),
    }
    setDefinition(updated)
    setJsonInput(JSON.stringify(updated, null, 2))
  }

  const isFinished = finalStatus && finalStatus !== 'waiting_for_decision'

  return (
    <div className="sim-layout">
      <div className="sim-config-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>{t('simulator.title')}</h2>
          <LanguageSwitcher />
        </div>

        <div className="sim-section">
          <label className="sim-section-label">{t('simulator.source') || '流程定义来源'}</label>
          <div className="sim-toggle-row">
            <button
              className={`btn ${!useJson ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setUseJson(false)}
            >{t('simulator.selectExisting') || '选择已有'}</button>
            <button
              className={`btn ${useJson ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setUseJson(true)}
            >{t('simulator.pasteJson') || '粘贴JSON'}</button>
          </div>
        </div>

        {!useJson ? (
          <div className="sim-section">
            <select value={selectedProcId} onChange={handleSelectProcess} className="sim-select">
              <option value="">-- {t('simulator.selectPlaceholder') || '选择流程定义'} --</option>
              {processes.map(p => (
                <option key={p.id} value={p.id}>{p.name} (v{p.version})</option>
              ))}
            </select>
          </div>
        ) : (
          <div className="sim-section">
            <textarea
              className="sim-json-input"
              rows={8}
              value={jsonInput}
              onChange={handleJsonChange}
              placeholder='{"nodes": [...], "edges": [...]}'
            />
          </div>
        )}

        <div className="sim-section">
          <label className="sim-section-label">{t('simulator.formData') || '虚拟表单数据'}</label>
          {formFields.map((f, idx) => (
            <div key={idx} className="sim-field-row">
              <input
                placeholder={t('simulator.fieldName') || '字段名'}
                value={f.key}
                onChange={e => updateFormField(idx, 'key', e.target.value)}
              />
              <input
                placeholder={t('simulator.fieldValue') || '值'}
                value={f.value}
                onChange={e => updateFormField(idx, 'value', e.target.value)}
              />
              <button className="btn btn-danger sim-btn-sm" onClick={() => removeFormField(idx)}>×</button>
            </div>
          ))}
          <button className="btn btn-secondary sim-btn-sm" onClick={addFormField}>+ {t('simulator.addField') || '添加字段'}</button>
        </div>

        <div className="sim-section">
          <label className="sim-section-label">{t('simulator.runMode') || '运行模式'}</label>
          <div className="sim-toggle-row">
            <button
              className={`btn ${mode === 'step' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setMode('step')}
            >{t('simulator.stepMode') || '单步执行'}</button>
            <button
              className={`btn ${mode === 'auto' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setMode('auto')}
            >{t('simulator.autoMode') || '自动运行'}</button>
          </div>
        </div>

        {definition && getApprovalNodes().length > 0 && (
          <div className="sim-section">
            <label className="sim-section-label">{t('simulator.sla.title')}</label>
            {getApprovalNodes().map(node => (
              <div key={node.id} style={{ marginBottom: '12px' }}>
                <div className="sim-field-row">
                  <input
                    value={node.name || node.id}
                    onChange={e => updateNodeName(node.id, e.target.value)}
                    style={{ flex: '0 0 120px' }}
                    placeholder={t('simulator.nodeName')}
                  />
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    placeholder="SLA"
                    value={node.sla_hours ?? ''}
                    onChange={e => updateNodeSla(node.id, e.target.value)}
                  />
                </div>
                {SUPPORTED_LOCALES.filter(l => l.code !== 'zh').map(l => (
                  <div key={l.code} className="sim-field-row" style={{ marginTop: '4px', paddingLeft: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#888', minWidth: '50px' }}>{l.label}:</span>
                    <input
                      value={(node.name_i18n && node.name_i18n[l.code]) || ''}
                      onChange={e => updateNodeNameI18n(node.id, l.code, e.target.value)}
                      placeholder={`${t('simulator.nodeName')} (${l.label})`}
                      style={{ fontSize: '12px' }}
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        <button className="btn btn-primary sim-start-btn" onClick={handleStart} disabled={running}>
          {running ? (t('simulator.running') || '模拟中...') : (t('simulator.start') || '开始模拟')}
        </button>
        {steps.length > 0 && (
          <button className="btn btn-secondary sim-start-btn" onClick={resetSimulation}>{t('simulator.reset') || '重置'}</button>
        )}

        {error && <div className="sim-error">{error}</div>}
      </div>

      <div className="sim-result-panel">
        <div className="sim-flow-section">
          <h3>{t('simulator.flowPath') || '流程路径'}</h3>
          <SimulationFlowChart
            definition={definition}
            steps={steps}
            visitedNodeIds={visitedNodeIds}
            waitingNodeId={waitingNodeId}
          />
          {waitingNodeId && (
            <div className="sim-decision-panel">
              <p>{t('simulator.waiting').replace('{nodeId}', resolveNodeName(
                definition.nodes.find(n => n.id === waitingNodeId) || { id: waitingNodeId },
                locale
              ))}</p>
              <div className="sim-decision-buttons">
                <button className="btn btn-primary" onClick={() => handleDecision('approve')}>{t('simulator.approve')}</button>
                <button className="btn btn-danger" onClick={() => handleDecision('reject')}>{t('simulator.reject')}</button>
                <button className="btn btn-secondary" onClick={() => handleDecision('return')}>{t('simulator.return')}</button>
              </div>
            </div>
          )}
          {isFinished && (
            <div className={`sim-final-status sim-final-${finalStatus}`}>
              {t('simulator.finished') || '模拟结束'} — {t('simulator.finalStatus') || '最终状态'}: <strong>{finalStatus}</strong>
            </div>
          )}
        </div>

        <div className="sim-log-section">
          <SimulationStepLog
            steps={steps}
            visitedNodeIds={visitedNodeIds}
            allNodeIds={allNodeIds}
            unvisitedNodeIds={unvisitedNodeIds}
            coveragePercent={coveragePercent}
            nodes={definition?.nodes}
          />
        </div>
      </div>
    </div>
  )
}
