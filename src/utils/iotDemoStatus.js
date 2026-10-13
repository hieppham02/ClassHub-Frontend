// Stable pseudo-random placement, biased toward the first rooms for demonstrations.
export function createDemoStatuses(nodes, rooms, metrics) {
  const candidates = []
  for (const node of nodes.filter(n => n.dataSource === 'MOCK')) {
    const roomIndex = rooms.findIndex(r => r.id === node.roomId)
    for (const metric of metrics) {
      if (!node.readings?.some(r => r.metric === metric.key && r.quality === 'GOOD' && Number.isFinite(r.value))) continue
      const key = `${node.id}:${metric.key}`
      let hash = 2166136261
      for (const character of key) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619) >>> 0
      candidates.push({ key, rank: Math.max(0, roomIndex) * 4 + hash / 4294967296 * 8 })
    }
  }
  candidates.sort((a, b) => a.rank - b.rank || a.key.localeCompare(b.key))
  const criticalCount = candidates.length ? Math.max(1, Math.round(candidates.length * 0.01)) : 0
  const warningCount = Math.min(candidates.length - criticalCount, Math.round(candidates.length * 0.1))
  return new Map(candidates.map((candidate, index) => [candidate.key,
    index < criticalCount ? 'critical' : index < criticalCount + warningCount ? 'warning' : 'stable']))
}
