import { API_BASE_URL } from '@/config/runtime.js'
import { ApiError } from '@/services/apiError.js'
import { getToken } from '@/services/authSession.js'

let unauthorizedHandler = null

function buildUrl(path) {
  if (/^https?:\/\//i.test(path)) return path
  return `${API_BASE_URL}/${String(path).replace(/^\/+/, '')}`
}

async function parseResponse(response) {
  if (response.status === 204 || response.status === 205) return null

  const text = await response.text()
  if (!text) return null

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('json')) {
    try {
      return JSON.parse(text)
    } catch {
      throw new ApiError('Phản hồi JSON từ máy chủ không hợp lệ.', {
        status: response.status,
        response,
      })
    }
  }

  return text
}

function getErrorMessage(data, response) {
  if (typeof data === 'string' && data.trim()) return data
  if (data && typeof data === 'object') {
    return data.message || data.error || data.title || response.statusText
  }
  return response.statusText || 'Yêu cầu không thành công.'
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = typeof handler === 'function' ? handler : null
}

export async function request(path, options = {}) {
  const {
    auth = true,
    body,
    headers: customHeaders,
    ...fetchOptions
  } = options

  const headers = new Headers(customHeaders)
  const token = auth ? getToken() : null

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let requestBody = body
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData
  if (body != null && !isFormData && typeof body !== 'string') {
    headers.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(buildUrl(path), {
      ...fetchOptions,
      headers,
      body: requestBody,
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError('Không thể kết nối đến máy chủ.', { data: error })
  }

  const data = await parseResponse(response)

  if (!response.ok) {
    const error = new ApiError(getErrorMessage(data, response), {
      status: response.status,
      data,
      response,
    })

    if (auth && response.status === 401 && unauthorizedHandler) {
      unauthorizedHandler(error)
    }

    throw error
  }

  return data
}

export const api = {
  get(path, options = {}) {
    return request(path, { ...options, method: 'GET' })
  },
  post(path, body, options = {}) {
    return request(path, { ...options, method: 'POST', body })
  },
  put(path, body, options = {}) {
    return request(path, { ...options, method: 'PUT', body })
  },
  patch(path, body, options = {}) {
    return request(path, { ...options, method: 'PATCH', body })
  },
  delete(path, options = {}) {
    return request(path, { ...options, method: 'DELETE' })
  },
}
