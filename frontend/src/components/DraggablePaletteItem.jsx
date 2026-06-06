import React from 'react'
import { useDraggable } from '@dnd-kit/core'

export default function DraggablePaletteItem({ type, label }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: `palette-${type}`,
    data: { fromPalette: true, controlType: type },
  })

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)`, opacity: 0.8 }
    : undefined

  return (
    <div
      ref={setNodeRef}
      className="palette-item"
      style={style}
      {...listeners}
      {...attributes}
    >
      {label}
    </div>
  )
}
