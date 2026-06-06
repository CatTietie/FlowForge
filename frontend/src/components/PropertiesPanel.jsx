import React, { useState } from 'react'

export default function PropertiesPanel({ field, onUpdate }) {
  if (!field) {
    return (
      <div className="properties-panel">
        <h3>属性面板</h3>
        <p style={{ color: '#999', fontSize: '13px' }}>选择一个控件以编辑属性</p>
      </div>
    )
  }

  const hasRequired = field.validations.some(v => v.rule === 'required')
  const maxLenValidation = field.validations.find(v => v.rule === 'maxLength')

  function toggleRequired() {
    if (hasRequired) {
      onUpdate({ validations: field.validations.filter(v => v.rule !== 'required') })
    } else {
      onUpdate({ validations: [...field.validations, { rule: 'required', message: '此项为必填' }] })
    }
  }

  function updateMaxLength(value) {
    const filtered = field.validations.filter(v => v.rule !== 'maxLength')
    if (value) {
      filtered.push({ rule: 'maxLength', value: parseInt(value), message: `最大长度为${value}` })
    }
    onUpdate({ validations: filtered })
  }

  function updateOptions(optionsStr) {
    onUpdate({ options: optionsStr.split(',').map(s => s.trim()).filter(Boolean) })
  }

  return (
    <div className="properties-panel">
      <h3>属性配置</h3>

      <div className="prop-group">
        <label>字段ID</label>
        <input value={field.fieldId} disabled />
      </div>

      <div className="prop-group">
        <label>显示标签</label>
        <input
          value={field.label}
          onChange={e => onUpdate({ label: e.target.value })}
        />
      </div>

      <div className="prop-group">
        <label>占位提示</label>
        <input
          value={field.placeholder || ''}
          onChange={e => onUpdate({ placeholder: e.target.value })}
        />
      </div>

      {field.type === 'dropdown' && (
        <div className="prop-group">
          <label>选项（逗号分隔）</label>
          <input
            value={(field.options || []).join(', ')}
            onChange={e => updateOptions(e.target.value)}
          />
        </div>
      )}

      <h3 style={{ marginTop: '16px' }}>校验规则</h3>

      <div className="prop-group">
        <label>
          <input type="checkbox" checked={hasRequired} onChange={toggleRequired} />
          必填
        </label>
      </div>

      {field.type === 'text' && (
        <div className="prop-group">
          <label>最大长度</label>
          <input
            type="number"
            value={maxLenValidation?.value || ''}
            onChange={e => updateMaxLength(e.target.value)}
          />
        </div>
      )}
    </div>
  )
}
