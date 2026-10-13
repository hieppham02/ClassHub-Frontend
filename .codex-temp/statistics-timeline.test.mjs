import assert from 'node:assert/strict'
import { buildStatisticsTimeline, timelineTicks } from '../src/utils/statisticsTimeline.js'

const input = [
  ...Array.from({ length: 100 }, () => ({ date: '2026-05-10' })),
  ...Array.from({ length: 12 }, () => ({ date: '2026-06-10' })),
  ...Array.from({ length: 18 }, () => ({ date: '2026-07-10' })),
  ...Array.from({ length: 100 }, () => ({ date: '2026-08-10' }))
]
const monthly = buildStatisticsTimeline(input)
assert.equal(monthly.granularity, 'month')
assert.deepEqual(monthly.series.map(item => item.count), [100, 12, 18, 100])
assert.equal(monthly.series.reduce((sum, item) => sum + item.count, 0), input.length)
const daily = buildStatisticsTimeline(input, { from: '2026-06-01', to: '2026-06-30' })
assert.equal(daily.granularity, 'day')
assert.equal(daily.series.length, 30)
assert.equal(daily.series[9].count, 12)
assert.equal(daily.series[0].count, 0)
assert.equal(timelineTicks(daily.series).length, 5)
assert.equal(timelineTicks(daily.series).at(-1).index, 29)
const weekly = buildStatisticsTimeline([{ date: '2026-06-07' }, { date: '2026-06-08' }], { from: '2026-06-01', to: '2026-07-31' })
assert.equal(weekly.granularity, 'week')
assert.deepEqual(weekly.series.slice(0, 2).map(item => item.count), [1, 1])
assert.equal(weekly.series[0].date, '2026-06-01')
const zeros = buildStatisticsTimeline([], { from: '2025-12-01', to: '2026-02-28', granularity: 'month' })
assert.deepEqual(zeros.series.map(item => item.date), ['2025-12-01', '2026-01-01', '2026-02-01'])
assert.deepEqual(buildStatisticsTimeline([]).series, [])
assert.equal(buildStatisticsTimeline([{ date: '2026-10-12' }]).series.length, 1)
assert.equal(timelineTicks([{ date: '2026-10-12' }]).length, 1)
assert.deepEqual(buildStatisticsTimeline(input, { from: '2026-08-01', to: '2026-05-01' }).series, [])
console.log('PASS: automatic day/week/month aggregation, summer dip, zero periods, total counts, year boundaries and at most five axis labels.')
