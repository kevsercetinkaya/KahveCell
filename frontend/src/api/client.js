export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

const SESSION_KEY = 'kahvecell.session'
let refreshInProgress

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function getAuthSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) ?? 'null')
  } catch {
    return null
  }
}

export function saveAuthSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearAuthSession() {
  localStorage.removeItem(SESSION_KEY)
}

async function renewSession() {
  const session = getAuthSession()
  if (!session?.refresh_token) return false
  if (refreshInProgress) return refreshInProgress

  refreshInProgress = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: session.refresh_token }),
      })
      if (!response.ok) {
        clearAuthSession()
        return false
      }
      saveAuthSession(await response.json())
      return true
    } catch {
      return false
    } finally {
      refreshInProgress = undefined
    }
  })()

  return refreshInProgress
}

async function readResponse(response) {
  if (response.status === 204) return null
  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) return response.json()
  return response.text()
}

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    body,
    headers: inputHeaders,
    auth = true,
    retry = true,
    ...fetchOptions
  } = options
  const headers = new Headers(inputHeaders)
  const session = getAuthSession()

  if (body !== undefined && !(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth && session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchOptions,
    method,
    headers,
    body: body === undefined
      ? undefined
      : body instanceof FormData
        ? body
        : JSON.stringify(body),
  })

  if (response.status === 401 && auth && retry && await renewSession()) {
    return apiRequest(path, { ...options, retry: false })
  }

  const result = await readResponse(response)
  if (!response.ok) {
    const message = typeof result?.detail === 'string'
      ? result.detail
      : 'İstek tamamlanamadı. Lütfen tekrar dene.'
    throw new ApiError(message, response.status, result)
  }
  return result
}