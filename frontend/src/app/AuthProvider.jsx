import { useEffect, useState } from 'react'

import {
  apiRequest,
  clearAuthSession,
  getAuthSession,
  saveAuthSession,
} from '../api/client'
import { AuthContext } from './auth-context'

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(getAuthSession()?.access_token))

  useEffect(() => {
    let active = true
    if (!getAuthSession()?.access_token) return () => { active = false }

    apiRequest('/auth/me')
      .then((currentUser) => {
        if (active) setUser(currentUser)
      })
      .catch(() => {
        clearAuthSession()
        if (active) setUser(null)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => { active = false }
  }, [])

  async function requestLoginCode(phoneNumber) {
    return apiRequest('/auth/login', {
      method: 'POST',
      body: { phone_number: phoneNumber },
      auth: false,
    })
  }

  async function requestRegistrationCode(profile) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: profile,
      auth: false,
    })
  }

  async function verifyCode(phoneNumber, code) {
    const session = await apiRequest('/auth/verify-otp', {
      method: 'POST',
      body: { phone_number: phoneNumber, code },
      auth: false,
    })
    saveAuthSession(session)
    setUser(session.user)
    return session.user
  }

  async function signOut() {
    const session = getAuthSession()
    try {
      if (session?.refresh_token) {
        await apiRequest('/auth/logout', {
          method: 'POST',
          body: { refresh_token: session.refresh_token },
          auth: false,
          retry: false,
        })
      }
    } finally {
      clearAuthSession()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, requestLoginCode, requestRegistrationCode, verifyCode, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}