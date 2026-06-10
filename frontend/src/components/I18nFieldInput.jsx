import React, { useState } from 'react'
import { SUPPORTED_LOCALES } from '../i18n/index'
import { useLocale } from '../i18n/LocaleContext'

export default function I18nFieldInput({ value, i18nMap, supportedLocales, onChange, placeholder }) {
  const { t } = useLocale()
  const [expanded, setExpanded] = useState(false)

  const baseLocale = (supportedLocales && supportedLocales[0]) || 'zh'
  const otherLocales = (supportedLocales || []).filter(code => code !== baseLocale)

  if (otherLocales.length === 0) return null

  function handleI18nChange(localeCode, newValue) {
    const updated = { ...(i18nMap || {}) }
    if (newValue) {
      updated[localeCode] = newValue
    } else {
      delete updated[localeCode]
    }
    onChange(Object.keys(updated).length > 0 ? updated : null)
  }

  return (
    <div style={{ marginTop: '4px' }}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        style={{
          background: 'none', border: 'none', color: '#1976d2', fontSize: '12px',
          cursor: 'pointer', padding: '2px 0', textDecoration: 'underline'
        }}
      >
        {expanded ? t('props.i18n.collapse') : t('props.i18n.expand')}
      </button>
      {expanded && (
        <div style={{ marginTop: '4px', paddingLeft: '8px', borderLeft: '2px solid #e0e0e0' }}>
          {otherLocales.map(code => {
            const loc = SUPPORTED_LOCALES.find(l => l.code === code)
            return (
              <div key={code} style={{ marginBottom: '4px' }}>
                <label style={{ fontSize: '11px', color: '#888' }}>{loc?.label || code}</label>
                <input
                  value={(i18nMap && i18nMap[code]) || ''}
                  onChange={e => handleI18nChange(code, e.target.value)}
                  placeholder={placeholder}
                  style={{ width: '100%', padding: '4px 6px', fontSize: '12px', borderRadius: '3px', border: '1px solid #ddd' }}
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
