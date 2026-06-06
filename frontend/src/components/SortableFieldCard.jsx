import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function SortableFieldCard({ field, selected, onClick, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: field.fieldId,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const typeLabels = { text: '文本框', dropdown: '下拉选择', date: '日期选择器' }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`field-card ${selected ? 'selected' : ''}`}
      onClick={onClick}
      {...attributes}
      {...listeners}
    >
      <span className="field-info">{field.label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className="field-type">{typeLabels[field.type] || field.type}</span>
        <button
          className="btn btn-danger"
          style={{ padding: '2px 8px', fontSize: '11px' }}
          onClick={e => { e.stopPropagation(); onDelete() }}
        >
          删除
        </button>
      </div>
    </div>
  )
}
