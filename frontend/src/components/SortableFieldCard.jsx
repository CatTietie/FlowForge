import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { resolveLocalized } from '../i18n/resolveI18n'
import { useLocale } from '../i18n/LocaleContext'

export default function SortableFieldCard({ field, selected, onClick, onDelete, previewLocale }) {
  const { t } = useLocale()
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: field.fieldId,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const typeLabels = {
    text: t('field.type.text'),
    number: t('field.type.number'),
    dropdown: t('field.type.dropdown'),
    date: t('field.type.date'),
  }

  const displayLabel = resolveLocalized(field.label, field.label_i18n, previewLocale || 'zh')

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`field-card ${selected ? 'selected' : ''}`}
      onClick={onClick}
      {...attributes}
      {...listeners}
    >
      <span className="field-info">{displayLabel}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className="field-type">{typeLabels[field.type] || field.type}</span>
        <button
          className="btn btn-danger"
          style={{ padding: '2px 8px', fontSize: '11px' }}
          onClick={e => { e.stopPropagation(); onDelete() }}
        >
          {t('common.delete')}
        </button>
      </div>
    </div>
  )
}
