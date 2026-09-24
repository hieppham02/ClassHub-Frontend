const TOKEN_STORAGE_KEY = 'classhub-token'
const USER_STORAGE_KEY = 'classhub-user'

function getStorage() {
  return typeof window === 'undefined' ? null : window.sessionStorage
}

function normalizeUser(user) {
  if (!user || typeof user !== 'object' || Array.isArray(user)) return null

  const role = typeof user.role === 'string'
    ? user.role.trim().toUpperCase()
    : ''

  return { ...user, role }
}

export function clearSession() {
  const storage = getStorage()
  if (!storage) return

  storage.removeItem(TOKEN_STORAGE_KEY)
  storage.removeItem(USER_STORAGE_KEY)
}

export function getToken() {
  const token = getStorage()?.getItem(TOKEN_STORAGE_KEY)
  return token?.trim() || null
}

export function getUser() {
  const storedUser = getStorage()?.getItem(USER_STORAGE_KEY)
  if (!storedUser) return null

  try {
    const user = normalizeUser(JSON.parse(storedUser))
    if (!user || !user.role) {
      clearSession()
      return null
    }
    return user
  } catch {
    clearSession()
    return null
  }
}

export function isAuthenticated() {
  return Boolean(getToken() && getUser())
}

export function hasRole(role) {
  const expectedRole = typeof role === 'string' ? role.trim().toUpperCase() : ''
  return Boolean(expectedRole && getUser()?.role === expectedRole)
}

export function saveSession(token, user) {
  const normalizedToken = typeof token === 'string' ? token.trim() : ''
  const normalizedUser = normalizeUser(user)

  if (!normalizedToken || !normalizedUser?.role) {
    throw new TypeError('Thông tin phiên đăng nhập không hợp lệ.')
  }

  const storage = getStorage()
  if (!storage) return

  storage.setItem(TOKEN_STORAGE_KEY, normalizedToken)
  storage.setItem(USER_STORAGE_KEY, JSON.stringify(normalizedUser))
}
