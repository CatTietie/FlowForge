import React, { useState, useEffect } from 'react'
import { useLocale } from '../i18n/LocaleContext'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function ProcessStart() {
  const { t } = useLocale()
  const [forms, setForms] = useState([])
  const [processes, setProcesses] = useState([])

  useEffect(() => {
    fetch('/api/forms/').then(r => r.json()).then(setForms)
    fetch('/api/processes/definitions').then(r => r.json()).then(setProcesses)
  }, [])

  return (
    <div className="render-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>{t('processStart.title')}</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <LanguageSwitcher />
          <a href="/statistics" className="btn btn-primary">{t('processStart.statistics')}</a>
        </div>
      </div>

      <h3 style={{ marginTop: '16px', marginBottom: '8px' }}>{t('processStart.savedForms')}</h3>
      {forms.length === 0 && <p style={{ color: '#999' }}>{t('processStart.noForms')}</p>}
      <ul>
        {forms.map(f => (
          <li key={f.id} style={{ marginBottom: '8px' }}>
            <a href={`/render/${f.id}`}>{f.name} (v{f.version})</a>
          </li>
        ))}
      </ul>

      <h3 style={{ marginTop: '16px', marginBottom: '8px' }}>{t('processStart.processDefinitions')}</h3>
      {processes.length === 0 && <p style={{ color: '#999' }}>{t('processStart.noProcesses')}</p>}
      <ul>
        {processes.map(p => (
          <li key={p.id} style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>{p.name} (v{p.version})</span>
            <a href={`/process/simulate?id=${p.id}`} className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 10px', textDecoration: 'none' }}>{t('processStart.simulate')}</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
