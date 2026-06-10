import React, { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import DraggablePaletteItem from '../components/DraggablePaletteItem'
import SortableFieldCard from '../components/SortableFieldCard'
import PropertiesPanel from '../components/PropertiesPanel'
import { useLocale } from '../i18n/LocaleContext'
import { SUPPORTED_LOCALES } from '../i18n/index'

const CONTROL_TYPES = [
  { type: 'text', labelKey: 'field.type.text' },
  { type: 'number', labelKey: 'field.type.number' },
  { type: 'dropdown', labelKey: 'field.type.dropdown' },
  { type: 'date', labelKey: 'field.type.date' },
]

let fieldCounter = 0

function generateFieldId() {
  fieldCounter += 1
  return `field_${Date.now()}_${fieldCounter}`
}

export default function FormDesigner() {
  const { t } = useLocale()
  const [fields, setFields] = useState([])
  const [selectedFieldId, setSelectedFieldId] = useState(null)
  const [formName, setFormName] = useState(t('designer.formName.default'))
  const [savedId, setSavedId] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [supportedLocales, setSupportedLocales] = useState(['zh'])
  const [previewLocale, setPreviewLocale] = useState('zh')
  const [showLocaleConfig, setShowLocaleConfig] = useState(false)

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  const selectedField = fields.find(f => f.fieldId === selectedFieldId)

  function handleDragEnd(event) {
    const { active, over } = event
    setDragOver(false)

    if (active.data.current?.fromPalette) {
      const controlType = active.data.current.controlType
      const newField = {
        fieldId: generateFieldId(),
        type: controlType,
        label: t(`field.type.${controlType}`),
        label_i18n: null,
        placeholder: '',
        placeholder_i18n: null,
        options: controlType === 'dropdown' ? ['选项1', '选项2'] : undefined,
        options_i18n: null,
        validations: [],
      }
      setFields(prev => [...prev, newField])
      setSelectedFieldId(newField.fieldId)
      return
    }

    if (over && active.id !== over.id) {
      setFields(prev => {
        const oldIndex = prev.findIndex(f => f.fieldId === active.id)
        const newIndex = prev.findIndex(f => f.fieldId === over.id)
        return arrayMove(prev, oldIndex, newIndex)
      })
    }
  }

  function handleDragOver(event) {
    if (event.over?.id === 'canvas-drop') {
      setDragOver(true)
    } else {
      setDragOver(false)
    }
  }

  function updateField(fieldId, updates) {
    setFields(prev => prev.map(f => f.fieldId === fieldId ? { ...f, ...updates } : f))
  }

  function deleteField(fieldId) {
    setFields(prev => prev.filter(f => f.fieldId !== fieldId))
    if (selectedFieldId === fieldId) setSelectedFieldId(null)
  }

  function toggleLocale(code) {
    setSupportedLocales(prev => {
      if (prev.includes(code)) {
        if (prev.length <= 1) return prev
        const next = prev.filter(l => l !== code)
        if (previewLocale === code) setPreviewLocale(next[0])
        return next
      }
      return [...prev, code]
    })
  }

  async function saveSchema() {
    const schema = { fields, supported_locales: supportedLocales }
    const res = await fetch('/api/forms/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: formName, schema_json: schema }),
    })
    if (res.ok) {
      const data = await res.json()
      setSavedId(data.id)
      alert(`${t('common.save.success')}! ID: ${data.id}, v${data.version}`)
    } else {
      alert(t('common.save.failed'))
    }
  }

  function exportSchema() {
    const schema = { fields, supported_locales: supportedLocales }
    const blob = new Blob([JSON.stringify(schema, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formName}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd} onDragOver={handleDragOver}>
      <div className="designer-layout">
        <div className="palette">
          <h3>{t('designer.palette.title')}</h3>
          {CONTROL_TYPES.map(c => (
            <DraggablePaletteItem key={c.type} type={c.type} label={t(c.labelKey)} />
          ))}
        </div>

        <div className="canvas">
          <div className="toolbar">
            <input
              value={formName}
              onChange={e => setFormName(e.target.value)}
              style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            />
            <button className="btn btn-primary" onClick={saveSchema}>{t('designer.save')}</button>
            <button className="btn btn-secondary" onClick={exportSchema}>{t('designer.export')}</button>
            {savedId && (
              <a className="btn btn-secondary" href={`/render/${savedId}`} style={{ textDecoration: 'none' }}>
                {t('designer.preview')}
              </a>
            )}
          </div>

          <div className="toolbar" style={{ marginTop: '8px', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setShowLocaleConfig(!showLocaleConfig)}
                style={{ fontSize: '12px' }}
              >
                {t('designer.locales.title')} ({supportedLocales.join(', ')})
              </button>
              {showLocaleConfig && (
                <div style={{
                  position: 'absolute', top: '100%', left: 0, zIndex: 10,
                  background: '#fff', border: '1px solid #ddd', borderRadius: '4px',
                  padding: '8px', marginTop: '4px', minWidth: '140px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  {SUPPORTED_LOCALES.map(l => (
                    <label key={l.code} style={{ display: 'block', margin: '4px 0', fontSize: '13px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={supportedLocales.includes(l.code)}
                        onChange={() => toggleLocale(l.code)}
                        style={{ marginRight: '6px' }}
                      />
                      {l.label}
                    </label>
                  ))}
                </div>
              )}
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#666' }}>
              {t('designer.locales.preview')}:
              <select
                value={previewLocale}
                onChange={e => setPreviewLocale(e.target.value)}
                style={{ padding: '3px 6px', fontSize: '12px', borderRadius: '4px', border: '1px solid #ddd' }}
              >
                {supportedLocales.map(code => {
                  const loc = SUPPORTED_LOCALES.find(l => l.code === code)
                  return <option key={code} value={code}>{loc?.label || code}</option>
                })}
              </select>
            </label>
          </div>

          <div className={`canvas-drop-zone ${dragOver ? 'drag-over' : ''}`} id="canvas-drop">
            {fields.length === 0 && (
              <p style={{ color: '#999', textAlign: 'center', marginTop: '40px' }}>
                {t('designer.canvas.empty')}
              </p>
            )}
            <SortableContext items={fields.map(f => f.fieldId)} strategy={verticalListSortingStrategy}>
              {fields.map(field => (
                <SortableFieldCard
                  key={field.fieldId}
                  field={field}
                  selected={field.fieldId === selectedFieldId}
                  onClick={() => setSelectedFieldId(field.fieldId)}
                  onDelete={() => deleteField(field.fieldId)}
                  previewLocale={previewLocale}
                />
              ))}
            </SortableContext>
          </div>
        </div>

        <PropertiesPanel
          field={selectedField}
          onUpdate={(updates) => selectedField && updateField(selectedField.fieldId, updates)}
          supportedLocales={supportedLocales}
        />
      </div>
    </DndContext>
  )
}
