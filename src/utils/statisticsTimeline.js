const DAY = 86400000
const dateKey = date => date.toISOString().slice(0, 10)
const toDate = value => new Date(`${value}T00:00:00Z`)

export function buildStatisticsTimeline(records, { from = '', to = '', granularity = 'auto' } = {}) {
  const dates = records.map(item => item.date).filter(value => /^\d{4}-\d{2}-\d{2}$/.test(value)).sort()
  const start = from || dates[0]
  const end = to || dates.at(-1)
  if (!start || !end || start > end) return { granularity: 'day', series: [] }
  const span = Math.round((toDate(end) - toDate(start)) / DAY) + 1
  const unit = granularity === 'auto' ? (span <= 31 ? 'day' : span <= 90 ? 'week' : 'month') : granularity

  function bucket(value) {
    if (unit === 'month') return value.slice(0, 7) + '-01'
    if (unit === 'week') {
      const date = toDate(value)
      date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 6) % 7)
      return dateKey(date)
    }
    return value
  }

  const counts = new Map()
  const finalBucket = bucket(end)
  for (const cursor = toDate(bucket(start)); dateKey(cursor) <= finalBucket;) {
    counts.set(dateKey(cursor), 0)
    if (unit === 'month') cursor.setUTCMonth(cursor.getUTCMonth() + 1)
    else cursor.setUTCDate(cursor.getUTCDate() + (unit === 'week' ? 7 : 1))
  }
  records.forEach(item => {
    if (item.date >= start && item.date <= end) {
      const key = bucket(item.date)
      if (counts.has(key)) counts.set(key, counts.get(key) + 1)
    }
  })
  const format = new Intl.DateTimeFormat('vi-VN', unit === 'month'
    ? { month: '2-digit', year: 'numeric', timeZone: 'UTC' }
    : { day: '2-digit', month: '2-digit', timeZone: 'UTC' })
  return {
    granularity: unit,
    series: [...counts].map(([date, count]) => ({ date, count, label: format.format(toDate(date)) }))
  }
}

export function timelineTicks(series, limit = 5) {
  if (series.length <= limit) return series.map((item, index) => ({ ...item, index }))
  return Array.from({ length: limit }, (_, i) => {
    const index = Math.round(i * (series.length - 1) / (limit - 1))
    return { ...series[index], index }
  })
}
