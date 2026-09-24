const DEFAULT_API_BASE_URL = 'http://localhost:5146/api'

function normalizeBaseUrl(value) {
  return value.trim().replace(/\/+$/, '')
}

export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_URL || DEFAULT_API_BASE_URL,
)

export const HUB_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_HUB_URL || API_BASE_URL.replace(/\/api$/, ''),
)
