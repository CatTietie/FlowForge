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

const CONTROL_TYPES = [
  { type: 'text', label: '文本框' },
  { type: 'number', label: '数字输入' },
  { type: 'dropdown', label: '下拉选择' },
  { type: 'date', label: '日期选择器' },
]

let fieldCounter = 0

function generateFieldId() {
  fieldCounter += 1
  return `field_${Date.now()}_${fieldCounter}`
}

export default function FormDesigner() {
  const [fields, setFields] = useState([])
  const [selectedFieldId, setSelectedFieldId] = useState(null)
  const [formName, setFormName] = useState('未命名表单')
  const [savedId, setSavedId] = useState(null)
  const [dragOver, setDragOver] = useState(false)

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
        label: CONTROL_TYPES.find(c => c.type === controlType)?.label || controlType,
        placeholder: '',
        options: controlType === 'dropdown' ? ['选项1', '选项2'] : undefined,
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

  async function saveSchema() {
    const schema = { fields }
    const res = await fetch('/api/forms/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: formName, schema_json: schema }),
    })
    if (res.ok) {
      const data = await res.json()
      setSavedId(data.id)
      alert(`保存成功! 表单ID: ${data.id}, 版本: ${data.version}`)
    } else {
      alert('保存失败')
    }
  }

  function exportSchema() {
    const schema = { fields }
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
          <h3>控件面板</h3>
          {CONTROL_TYPES.map(c => (
            <DraggablePaletteItem key={c.type} type={c.type} label={c.label} />
          ))}
        </div>

        <div className="canvas">
          <div className="toolbar">
            <input
              value={formName}
              onChange={e => setFormName(e.target.value)}
              style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            />
            <button className="btn btn-primary" onClick={saveSchema}>保存</button>
            <button className="btn btn-secondary" onClick={exportSchema}>导出JSON</button>
            {savedId && (
              <a className="btn btn-secondary" href={`/render/${savedId}`} style={{ textDecoration: 'none' }}>
                预览
              </a>
            )}
          </div>

          <div className={`canvas-drop-zone ${dragOver ? 'drag-over' : ''}`} id="canvas-drop">
            {fields.length === 0 && (
              <p style={{ color: '#999', textAlign: 'center', marginTop: '40px' }}>
                从左侧拖拽控件到此处
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
                />
              ))}
            </SortableContext>
          </div>
        </div>

        <PropertiesPanel
          field={selectedField}
          onUpdate={(updates) => selectedField && updateField(selectedField.fieldId, updates)}
        />
      </div>
    </DndContext>
  )
}
