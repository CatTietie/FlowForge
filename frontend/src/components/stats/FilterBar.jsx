import React from 'react'
import { useLocale } from '../../i18n/LocaleContext'

export default function FilterBar({ filters, setFilters, definitions, onSearch }) {
  const { t } = useLocale()

  return (
    <div className="stats-filter-bar">
      <div className="stats-filter-item">
        <label>{t('stats.filter.definition')}</label>
        <select
          value={filters.process_definition_id || ''}
          onChange={e => setFilters(f => ({ ...f, process_definition_id: e.target.value || null }))}
        >
          <option value="">{t('stats.filter.all')}</option>
          {definitions.map(d => (
            <option key={d.id} value={d.id}>{d.name} (v{d.version})</option>
          ))}
        </select>
      </div>
      <div className="stats-filter-item">
        <label>{t('stats.filter.assignee')}</label>
        <input
          type="text"
          placeholder={t('stats.filter.assigneePlaceholder')}
          value={filters.assignee || ''}
          onChange={e => setFilters(f => ({ ...f, assignee: e.target.value || null }))}
        />
      </div>
      <div className="stats-filter-item">
        <label>{t('stats.filter.startDate')}</label>
        <input
          type="date"
          value={filters.start_date || ''}
          onChange={e => setFilters(f => ({ ...f, start_date: e.target.value || null }))}
        />
      </div>
      <div className="stats-filter-item">
        <label>{t('stats.filter.endDate')}</label>
        <input
          type="date"
          value={filters.end_date || ''}
          onChange={e => setFilters(f => ({ ...f, end_date: e.target.value || null }))}
        />
      </div>
      <button className="btn btn-primary stats-search-btn" onClick={onSearch}>{t('stats.filter.search')}</button>
    </div>
  )
}
