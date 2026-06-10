import React, { useState, useEffect } from 'react'
import FilterBar from '../components/stats/FilterBar'
import SummaryCards from '../components/stats/SummaryCards'
import CompletionTrendChart from '../components/stats/CompletionTrendChart'
import BacklogChart from '../components/stats/BacklogChart'
import TimeoutRateChart from '../components/stats/TimeoutRateChart'
import SlaViolationsTable from '../components/stats/SlaViolationsTable'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useLocale } from '../i18n/LocaleContext'

export default function StatisticsDashboard() {
  const { t } = useLocale()
  const [definitions, setDefinitions] = useState([])
  const [filters, setFilters] = useState({
    process_definition_id: null,
    assignee: null,
    start_date: null,
    end_date: null,
  })
  const [granularity, setGranularity] = useState('day')
  const [avgDuration, setAvgDuration] = useState(null)
  const [timeoutRate, setTimeoutRate] = useState(null)
  const [completionTrend, setCompletionTrend] = useState([])
  const [backlog, setBacklog] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch('/api/processes/definitions').then(r => r.json()).then(setDefinitions)
    fetchAllData()
  }, [])

  function buildParams(extra = {}) {
    const params = new URLSearchParams()
    if (filters.process_definition_id) params.set('process_definition_id', filters.process_definition_id)
    if (filters.assignee) params.set('assignee', filters.assignee)
    if (filters.start_date) params.set('start_date', filters.start_date)
    if (filters.end_date) params.set('end_date', filters.end_date)
    Object.entries(extra).forEach(([k, v]) => { if (v != null) params.set(k, v) })
    return params.toString()
  }

  async function fetchAllData() {
    setLoading(true)
    try {
      const [dur, timeout, trend, back] = await Promise.all([
        fetch(`/api/statistics/avg-duration?${buildParams()}`).then(r => r.json()),
        fetch(`/api/statistics/timeout-rate?${buildParams()}`).then(r => r.json()),
        fetch(`/api/statistics/completion-trend?${buildParams({ granularity })}`).then(r => r.json()),
        fetch(`/api/statistics/backlog?${buildParams()}`).then(r => r.json()),
      ])
      setAvgDuration(dur)
      setTimeoutRate(timeout)
      setCompletionTrend(trend.data_points || [])
      setBacklog(back)
    } catch (e) {
      console.error('Failed to fetch statistics:', e)
    }
    setLoading(false)
  }

  function handleGranularityChange(g) {
    setGranularity(g)
    fetch(`/api/statistics/completion-trend?${buildParams({ granularity: g })}`)
      .then(r => r.json())
      .then(data => setCompletionTrend(data.data_points || []))
  }

  return (
    <div className="stats-dashboard">
      <div className="stats-header">
        <h2>{t('stats.title')}</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <LanguageSwitcher />
          <a href="/process/start" className="btn btn-secondary">{t('stats.backToList')}</a>
        </div>
      </div>

      <FilterBar
        filters={filters}
        setFilters={setFilters}
        definitions={definitions}
        onSearch={fetchAllData}
      />

      {loading ? (
        <div className="stats-loading">{t('renderer.loading')}</div>
      ) : (
        <>
          <SummaryCards
            avgDuration={avgDuration}
            timeoutRate={timeoutRate}
            backlog={backlog}
          />

          <div className="stats-charts-row">
            <CompletionTrendChart
              data={completionTrend}
              granularity={granularity}
              onGranularityChange={handleGranularityChange}
            />
            <BacklogChart data={backlog} />
          </div>

          <SlaViolationsTable data={backlog} />

          <TimeoutRateChart data={timeoutRate} />
        </>
      )}
    </div>
  )
}
