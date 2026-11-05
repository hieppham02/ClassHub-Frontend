// Assess the displayed measurement itself for both physical and test nodes.
export function createDemoStatuses(nodes, rooms, metrics) {
  const result = new Map()
  for (const node of nodes) {
    for (const metric of metrics) {
      const r = node.readings?.find(r => r.metric === metric.key && r.quality === 'GOOD' && Number.isFinite(r.value))
      if (!r || node.status !== 'ONLINE') continue
      let status = 'unknown'
      if (metric.key === 'temperature')
        status = r.value >= 40 ? 'critical' : r.value >= 35 || r.value <= 0 ? 'warning' : 'stable'
      else if (metric.key === 'humidity')
        status = r.value >= 85 || r.value < 15 ? 'critical' : r.value >= 75 || r.value < 30 ? 'warning' : 'stable'
      result.set(node.id + ':' + metric.key, status)
    }
  }
  return result
}
