import React from 'react'
import { SUPPORTED_LOCALES } from '../i18n/index'
import { useLocale } from '../i18n/LocaleContext'

export default function LanguageSwitcher({ style }) {
  const { locale, setLocale } = useLocale()

  return (
    <select
      value={locale}
      onChange={e => setLocale(e.target.value)}
      style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '13px', ...style }}
    >
      {SUPPORTED_LOCALES.map(l => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  )
}
