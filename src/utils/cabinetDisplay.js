// Door presentation is independent of latch commands and connection freshness.
export function cabinetDoorLabel(value, previous) {
  if (value?.doorCondition === 'Mở' || value?.doorCondition === 'Đóng') return value.doorCondition
  const measured = value?.health?.metrics?.doorOpen
  if (typeof measured === 'boolean') return measured ? 'Mở' : 'Đóng'
  if (value?.doorCondition == null && typeof value?.isDoorOpen === 'boolean') return value.isDoorOpen ? 'Mở' : 'Đóng'
  if (previous?.doorCondition === 'Mở' || previous?.doorCondition === 'Đóng') return previous.doorCondition
  return 'Đóng'
}

export function normalizeCabinet(value) {
  const doorCondition = cabinetDoorLabel(value)
  let status = value.status
  if (!status || status === 'Mất kết nối') {
    status = value.borrowingStatus === 'RETURNING' ? 'Đang xác nhận trả' : value.borrower && value.borrower !== '---' ? 'Đang mượn' : 'Trống'
  }
  return { ...value, status, doorCondition, isDoorOpen: doorCondition === 'Mở' }
}

export function updateCabinet(target, delta) {
  target.doorCondition = cabinetDoorLabel(delta, target)
  target.isDoorOpen = target.doorCondition === 'Mở'
  if (typeof delta.isOnline === 'boolean') target.isOnline = delta.isOnline
  if (delta.health !== undefined) target.health = delta.health
  if (delta.status && delta.status !== 'Mất kết nối') target.status = delta.status
  if (delta.borrower !== undefined) target.borrower = delta.borrower
  if (delta.lastOnline) target.lastOnline = delta.lastOnline
  if (['LOCKED', 'UNLOCKED', 'ERROR'].includes(delta.lockStatus)) target.lockStatus = delta.lockStatus
}
