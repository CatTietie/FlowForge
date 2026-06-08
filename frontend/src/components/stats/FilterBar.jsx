import React from 'react'

export default function FilterBar({ filters, setFilters, definitions, onSearch }) {
  return (
    <div className="stats-filter-bar">
      <div className="stats-filter-item">
        <label>流程定义</label>
        <select
          value={filters.process_definition_id || ''}
          onChange={e => setFilters(f => ({ ...f, process_definition_id: e.target.value || null }))}
        >
          <option value="">全部</option>
          {definitions.map(d => (
            <option key={d.id} value={d.id}>{d.name} (v{d.version})</option>
          ))}
        </select>
      </div>
      <div className="stats-filter-item">
        <label>审批人</label>
        <input
          type="text"
          placeholder="输入审批人"
          value={filters.assignee || ''}
          onChange={e => setFilters(f => ({ ...f, assignee: e.target.value || null }))}
        />
      </div>
      <div className="stats-filter-item">
        <label>开始日期</label>
        <input
          type="date"
          value={filters.start_date || ''}
          onChange={e => setFilters(f => ({ ...f, start_date: e.target.value || null }))}
        />
      </div>
      <div className="stats-filter-item">
        <label>结束日期</label>
        <input
          type="date"
          value={filters.end_date || ''}
          onChange={e => setFilters(f => ({ ...f, end_date: e.target.value || null }))}
        />
      </div>
      <button className="btn btn-primary stats-search-btn" onClick={onSearch}>查询</button>
    </div>
  )
}
