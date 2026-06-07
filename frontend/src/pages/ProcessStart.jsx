import React, { useState, useEffect } from 'react'

export default function ProcessStart() {
  const [forms, setForms] = useState([])
  const [processes, setProcesses] = useState([])

  useEffect(() => {
    fetch('/api/forms/').then(r => r.json()).then(setForms)
    fetch('/api/processes/definitions').then(r => r.json()).then(setProcesses)
  }, [])

  return (
    <div className="render-page">
      <h2>发起流程</h2>

      <h3 style={{ marginTop: '16px', marginBottom: '8px' }}>已保存表单</h3>
      {forms.length === 0 && <p style={{ color: '#999' }}>暂无表单，请先在设计器中创建</p>}
      <ul>
        {forms.map(f => (
          <li key={f.id} style={{ marginBottom: '8px' }}>
            <a href={`/render/${f.id}`}>{f.name} (v{f.version})</a>
          </li>
        ))}
      </ul>

      <h3 style={{ marginTop: '16px', marginBottom: '8px' }}>流程定义</h3>
      {processes.length === 0 && <p style={{ color: '#999' }}>暂无流程定义</p>}
      <ul>
        {processes.map(p => (
          <li key={p.id} style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>{p.name} (v{p.version})</span>
            <a href={`/process/simulate?id=${p.id}`} className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 10px', textDecoration: 'none' }}>模拟运行</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
