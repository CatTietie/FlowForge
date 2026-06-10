import React, { useState } from 'react'
import I18nFieldInput from './I18nFieldInput'
import { useLocale } from '../i18n/LocaleContext'
import { SUPPORTED_LOCALES } from '../i18n/index'

export default function PropertiesPanel({ field, onUpdate, supportedLocales }) {
  const { t } = useLocale()

  if (!field) {
    return (
      <div className="properties-panel">
        <h3>{t('designer.properties.panel')}</h3>
        <p style={{ color: '#999', fontSize: '13px' }}>{t('designer.properties.empty')}</p>
      </div>
    )
  }

  const hasRequired = field.validations.some(v => v.rule === 'required')
  const maxLenValidation = field.validations.find(v => v.rule === 'maxLength')
  const minValidation = field.validations.find(v => v.rule === 'min')
  const maxValidation = field.validations.find(v => v.rule === 'max')

  function toggleRequired() {
    if (hasRequired) {
      onUpdate({ validations: field.validations.filter(v => v.rule !== 'required') })
    } else {
      onUpdate({ validations: [...field.validations, { rule: 'required', message: '此项为必填', message_i18n: null }] })
    }
  }

  function updateMaxLength(value) {
    const filtered = field.validations.filter(v => v.rule !== 'maxLength')
    if (value) {
      filtered.push({ rule: 'maxLength', value: parseInt(value), message: `最大长度为${value}`, message_i18n: null })
    }
    onUpdate({ validations: filtered })
  }

  function updateOptions(optionsStr) {
    onUpdate({ options: optionsStr.split(',').map(s => s.trim()).filter(Boolean) })
  }

  function updateMin(value) {
    const filtered = field.validations.filter(v => v.rule !== 'min')
    if (value !== '') {
      filtered.push({ rule: 'min', value: parseFloat(value), message: `最小值为${value}`, message_i18n: null })
    }
    onUpdate({ validations: filtered })
  }

  function updateMax(value) {
    const filtered = field.validations.filter(v => v.rule !== 'max')
    if (value !== '') {
      filtered.push({ rule: 'max', value: parseFloat(value), message: `最大值为${value}`, message_i18n: null })
    }
    onUpdate({ validations: filtered })
  }

  function updateValidationI18n(rule, i18nMap) {
    const updated = field.validations.map(v =>
      v.rule === rule ? { ...v, message_i18n: i18nMap } : v
    )
    onUpdate({ validations: updated })
  }

  function updateOptionsI18n(i18nMap) {
    onUpdate({ options_i18n: i18nMap })
  }

  const otherLocales = (supportedLocales || []).filter(code => code !== 'zh')

  return (
    <div className="properties-panel">
      <h3>{t('designer.properties.title')}</h3>

      <div className="prop-group">
        <label>{t('props.fieldId')}</label>
        <input value={field.fieldId} disabled />
      </div>

      <div className="prop-group">
        <label>{t('props.label')}</label>
        <input
          value={field.label}
          onChange={e => onUpdate({ label: e.target.value })}
        />
        <I18nFieldInput
          value={field.label}
          i18nMap={field.label_i18n}
          supportedLocales={supportedLocales}
          onChange={i18nMap => onUpdate({ label_i18n: i18nMap })}
          placeholder={t('props.label')}
        />
      </div>

      <div className="prop-group">
        <label>{t('props.placeholder')}</label>
        <input
          value={field.placeholder || ''}
          onChange={e => onUpdate({ placeholder: e.target.value })}
        />
        <I18nFieldInput
          value={field.placeholder || ''}
          i18nMap={field.placeholder_i18n}
          supportedLocales={supportedLocales}
          onChange={i18nMap => onUpdate({ placeholder_i18n: i18nMap })}
          placeholder={t('props.placeholder')}
        />
      </div>

      {field.type === 'dropdown' && (
        <div className="prop-group">
          <label>{t('props.options')}</label>
          <input
            value={(field.options || []).join(', ')}
            onChange={e => updateOptions(e.target.value)}
          />
          {otherLocales.length > 0 && (
            <OptionsI18nEditor
              options={field.options || []}
              optionsI18n={field.options_i18n}
              supportedLocales={supportedLocales}
              onChange={updateOptionsI18n}
              t={t}
            />
          )}
        </div>
      )}

      <h3 style={{ marginTop: '16px' }}>{t('props.validations')}</h3>

      <div className="prop-group">
        <label>
          <input type="checkbox" checked={hasRequired} onChange={toggleRequired} />
          {t('props.required')}
        </label>
        {hasRequired && (
          <I18nFieldInput
            value={field.validations.find(v => v.rule === 'required')?.message || ''}
            i18nMap={field.validations.find(v => v.rule === 'required')?.message_i18n}
            supportedLocales={supportedLocales}
            onChange={i18nMap => updateValidationI18n('required', i18nMap)}
            placeholder="e.g. This field is required"
          />
        )}
      </div>

      {field.type === 'text' && (
        <div className="prop-group">
          <label>{t('props.maxLength')}</label>
          <input
            type="number"
            value={maxLenValidation?.value || ''}
            onChange={e => updateMaxLength(e.target.value)}
          />
          {maxLenValidation && (
            <I18nFieldInput
              value={maxLenValidation.message || ''}
              i18nMap={maxLenValidation.message_i18n}
              supportedLocales={supportedLocales}
              onChange={i18nMap => updateValidationI18n('maxLength', i18nMap)}
              placeholder="e.g. Max length is {value}"
            />
          )}
        </div>
      )}

      {field.type === 'number' && (
        <>
          <div className="prop-group">
            <label>{t('props.min')}</label>
            <input
              type="number"
              value={minValidation?.value ?? ''}
              onChange={e => updateMin(e.target.value)}
            />
            {minValidation && (
              <I18nFieldInput
                value={minValidation.message || ''}
                i18nMap={minValidation.message_i18n}
                supportedLocales={supportedLocales}
                onChange={i18nMap => updateValidationI18n('min', i18nMap)}
                placeholder="e.g. Min value is {value}"
              />
            )}
          </div>
          <div className="prop-group">
            <label>{t('props.max')}</label>
            <input
              type="number"
              value={maxValidation?.value ?? ''}
              onChange={e => updateMax(e.target.value)}
            />
            {maxValidation && (
              <I18nFieldInput
                value={maxValidation.message || ''}
                i18nMap={maxValidation.message_i18n}
                supportedLocales={supportedLocales}
                onChange={i18nMap => updateValidationI18n('max', i18nMap)}
                placeholder="e.g. Max value is {value}"
              />
            )}
          </div>
        </>
      )}
    </div>
  )
}

function OptionsI18nEditor({ options, optionsI18n, supportedLocales, onChange, t }) {
  const [expanded, setExpanded] = useState(false)
  const baseLocale = (supportedLocales && supportedLocales[0]) || 'zh'
  const otherLocales = supportedLocales.filter(code => code !== baseLocale)

  function handleOptionChange(localeCode, index, newValue) {
    const current = { ...(optionsI18n || {}) }
    if (!current[localeCode]) {
      current[localeCode] = options.map(() => '')
    }
    const localeOpts = [...current[localeCode]]
    localeOpts[index] = newValue
    current[localeCode] = localeOpts
    onChange(current)
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
              <div key={code} style={{ marginBottom: '8px' }}>
                <label style={{ fontSize: '11px', color: '#888', fontWeight: 'bold' }}>{loc?.label || code}</label>
                {options.map((opt, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                    <span style={{ fontSize: '11px', color: '#aaa', minWidth: '60px' }}>{opt}:</span>
                    <input
                      value={(optionsI18n && optionsI18n[code] && optionsI18n[code][idx]) || ''}
                      onChange={e => handleOptionChange(code, idx, e.target.value)}
                      style={{ flex: 1, padding: '3px 6px', fontSize: '12px', borderRadius: '3px', border: '1px solid #ddd' }}
                    />
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
