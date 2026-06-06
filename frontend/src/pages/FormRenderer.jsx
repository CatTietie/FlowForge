import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

function validateField(value, validations) {
  for (const v of validations) {
    switch (v.rule) {
      case 'required':
        if (!value || (typeof value === 'string' && value.trim() === '')) {
          return v.message || '此项为必填'
        }
        break
      case 'maxLength':
        if (typeof value === 'string' && value.length > v.value) {
          return v.message || `最大长度为${v.value}`
        }
        break
      case 'regex':
        if (typeof value === 'string' && !new RegExp(v.value).test(value)) {
          return v.message || '格式不正确'
        }
        break
    }
  }
  return null
}

export default function FormRenderer() {
  const { formId } = useParams()
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
      const error = validateField(value, field.validations)
      setErrors(prev => ({ ...prev, [fieldId]: error }))
    }
  }

  function handleBlur(fieldId) {
    const field = schema.fields.find(f => f.fieldId === fieldId)
    const error = validateField(formData[fieldId], field.validations)
    setErrors(prev => ({ ...prev, [fieldId]: error }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const newErrors = {}
    let hasError = false
    for (const field of schema.fields) {
      const error = validateField(formData[field.fieldId], field.validations)
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
        process_definition_id: 1,
        form_data: formData,
      }),
    })
    if (res.ok) {
      setSubmitted(true)
    } else {
      alert('提交失败')
    }
  }

  if (loading) return <div className="render-page"><p>加载中...</p></div>
  if (!schema) return <div className="render-page"><p>表单不存在</p></div>

  if (submitted) {
    return (
      <div className="render-page">
        <h2>提交成功</h2>
        <p className="success-msg">表单已提交，流程已启动。</p>
      </div>
    )
  }

  return (
    <div className="render-page">
      <h2>填写表单</h2>
      <form onSubmit={handleSubmit}>
        {schema.fields.map(field => (
          <div className="form-field" key={field.fieldId}>
            <label>{field.label}</label>
            {field.type === 'text' && (
              <input
                type="text"
                className={errors[field.fieldId] ? 'invalid' : ''}
                placeholder={field.placeholder}
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
                <option value="">{field.placeholder || '请选择'}</option>
                {(field.options || []).map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
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
            {errors[field.fieldId] && (
              <div className="error">{errors[field.fieldId]}</div>
            )}
          </div>
        ))}
        <button type="submit" className="btn btn-primary" style={{ marginTop: '16px' }}>
          提交
        </button>
      </form>
    </div>
  )
}
