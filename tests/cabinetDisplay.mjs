import assert from 'node:assert/strict'
import { normalizeCabinet, updateCabinet, cabinetDoorLabel } from '../src/utils/cabinetDisplay.js'
let checks = 0
function check(value, name) { assert.ok(value, name); checks++; console.log('PASS: ' + name) }
let row = normalizeCabinet({ isOnline: false, status: 'Mất kết nối', doorCondition: 'Chưa có dữ liệu cảm biến', isDoorOpen: true, lockStatus: 'UNLOCKED', borrower: '---' })
check(row.doorCondition === 'Đóng' && !row.isDoorOpen, 'Missing sensor data defaults closed without inferring door from latch')
check(row.status === 'Trống' && !row.isOnline, 'Availability and connection stay independent')
row = normalizeCabinet({ isOnline: false, status: 'Đang mượn', health: { metrics: { doorOpen: true } }, lockStatus: 'LOCKED' })
check(row.doorCondition === 'Mở' && row.status === 'Đang mượn', 'Offline rows retain their recorded open/borrowed state')
updateCabinet(row, { isOnline: false })
check(row.doorCondition === 'Mở' && row.status === 'Đang mượn', 'Disconnect-only update preserves door and borrowing state')
updateCabinet(row, { isOpen: false, qrPhase: 'RECEIVE_CLOSED' })
check(row.doorCondition === 'Mở' && !row.isOnline, 'QR latch/session state is not a physical door measurement or proof of connectivity')
updateCabinet(row, { doorCondition: 'Đóng', lockStatus: 'UNLOCKED', isOnline: true })
check(row.doorCondition === 'Đóng' && row.lockStatus === 'UNLOCKED', 'Physical door and latch status update separately')
updateCabinet(row, { health: { metrics: { doorOpen: true } } })
check(row.doorCondition === 'Mở', 'Explicit physical telemetry updates the door')
updateCabinet(row, { health: { metrics: { doorOpen: null } }, status: 'Mất kết nối' })
check(row.doorCondition === 'Mở' && row.status === 'Đang mượn', 'Unknown sensor update does not erase remembered state')
check(cabinetDoorLabel({doorCondition:'Đóng',health:{metrics:{doorOpen:true}}}) === 'Đóng', 'Explicit current presentation wins over an older attached health snapshot')
console.log('PASS: ' + checks + ' cabinet UI checks')
