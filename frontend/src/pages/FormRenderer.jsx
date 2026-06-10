import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useLocale } from '../i18n/LocaleContext'
import { resolveLocalized, resolveOptions } from '../i18n/resolveI18n'
import LanguageSwitcher from '../components/LanguageSwitcher'

function validateField(value, validations, locale) {
  for (const v of validations) {
    switch (v.rule) {
      case 'required':
        if (!value && value !== 0 || (typeof value === 'string' && value.trim() === '')) {
          return resolveLocalized(v.message || '此项为必填', v.message_i18n, locale)
        }
        break
      case 'maxLength':
        if (typeof value === 'string' && value.length > v.value) {
          return resolveLocalized(v.message || `最大长度为${v.value}`, v.message_i18n, locale)
        }
        break
      case 'regex':
        if (typeof value === 'string' && !new RegExp(v.value).test(value)) {
          return resolveLocalized(v.message || '格式不正确', v.message_i18n, locale)
        }
        break
      case 'min': {
        const num = typeof value === 'number' ? value : parseFloat(value)
        if (!isNaN(num) && num < v.value) {
          return resolveLocalized(v.message || `最小值为${v.value}`, v.message_i18n, locale)
        }
        break
      }
      case 'max': {
        const num = typeof value === 'number' ? value : parseFloat(value)
        if (!isNaN(num) && num > v.value) {
          return resolveLocalized(v.message || `最大值为${v.value}`, v.message_i18n, locale)
        }
        break
      }
    }
  }
  return null
}

export default function FormRenderer() {
  const { formId } = useParams()
  const [searchParams] = useSearchParams()
  const processDefId = searchParams.get('processId') || 1
  const { locale, t } = useLocale()
  const [schema, setSchema] = useState(null)
  const [formData, setFormData] = useState({})
  const [errors, setErrors] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/forms/schema/${formId}`)
      .then(res => res.json())
      .then(data => {
        setSchema(data)
        const initial = {}
        for (const field of data.fields) {
          initial[field.fieldId] = ''
        }
        setFormData(initial)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [formId])

  function handleChange(fieldId, value) {
    setFormData(prev => ({ ...prev, [fieldId]: value }))
    if (errors[fieldId]) {
      const field = schema.fields.find(f => f.fieldId === fieldId)
      const error = validateField(value, field.validations, locale)
      setErrors(prev => ({ ...prev, [fieldId]: error }))
    }
  }

  function handleBlur(fieldId) {
    const field = schema.fields.find(f => f.fieldId === fieldId)
    const error = validateField(formData[fieldId], field.validations, locale)
    setErrors(prev => ({ ...prev, [fieldId]: error }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const newErrors = {}
    let hasError = false
    for (const field of schema.fields) {
      const error = validateField(formData[field.fieldId], field.validations, locale)
      if (error) {
        newErrors[field.fieldId] = error
        hasError = true
      }
    }
    setErrors(newErrors)
    if (hasError) return

    const res = await fetch('/api/processes/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        process_definition_id: parseInt(processDefId),
        form_data: formData,
      }),
    })
    if (res.ok) {
      setSubmitted(true)
    } else {
      alert(t('renderer.submitFailed'))
    }
  }

  if (loading) return <div className="render-page"><p>{t('renderer.loading')}</p></div>
  if (!schema) return <div className="render-page"><p>{t('renderer.notFound')}</p></div>

  if (submitted) {
    return (
      <div className="render-page">
        <h2>{t('renderer.success.title')}</h2>
        <p className="success-msg">{t('renderer.success.message')}</p>
      </div>
    )
  }

  return (
    <div className="render-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ margin: 0 }}>{t('renderer.title')}</h2>
        <LanguageSwitcher />
      </div>
      <form onSubmit={handleSubmit}>
        {schema.fields.map(field => {
          const label = resolveLocalized(field.label, field.label_i18n, locale)
          const placeholder = resolveLocalized(field.placeholder, field.placeholder_i18n, locale)
          const options = field.options || []
          const displayOptions = resolveOptions(field.options, field.options_i18n, locale)

          return (
            <div className="form-field" key={field.fieldId}>
              <label>{label}</label>
              {field.type === 'text' && (
                <input
                  type="text"
                  className={errors[field.fieldId] ? 'invalid' : ''}
                  placeholder={placeholder}
                  value={formData[field.fieldId] || ''}
                  onChange={e => handleChange(field.fieldId, e.target.value)}
                  onBlur={() => handleBlur(field.fieldId)}
                />
              )}
              {field.type === 'dropdown' && (
                <select
                  className={errors[field.fieldId] ? 'invalid' : ''}
                  value={formData[field.fieldId] || ''}
                  onChange={e => handleChange(field.fieldId, e.target.value)}
                  onBlur={() => handleBlur(field.fieldId)}
                >
                  <option value="">{placeholder || t('renderer.dropdown.placeholder')}</option>
                  {options.map((opt, idx) => (
                    <option key={opt} value={opt}>{displayOptions[idx] || opt}</option>
                  ))}
                </select>
              )}
              {field.type === 'date' && (
                <input
                  type="date"
                  className={errors[field.fieldId] ? 'invalid' : ''}
                  value={formData[field.fieldId] || ''}
                  onChange={e => handleChange(field.fieldId, e.target.value)}
                  onBlur={() => handleBlur(field.fieldId)}
                />
              )}
              {field.type === 'number' && (
                <input
                  type="number"
                  className={errors[field.fieldId] ? 'invalid' : ''}
                  placeholder={placeholder}
                  value={formData[field.fieldId] ?? ''}
                  onChange={e => handleChange(field.fieldId, e.target.value)}
                  onBlur={() => handleBlur(field.fieldId)}
                />
              )}
              {errors[field.fieldId] && (
                <div className="error">{errors[field.fieldId]}</div>
              )}
            </div>
          )
        })}
        <button type="submit" className="btn btn-primary" style={{ marginTop: '16px' }}>
          {t('renderer.submit')}
        </button>
      </form>
    </div>
  )
}
