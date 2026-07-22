const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

const getSessionStorage = () => (
  localStorage.getItem(ACCESS_TOKEN_KEY) ? localStorage : window.sessionStorage
)

export const getStoredAccessToken = () => (
  localStorage.getItem(ACCESS_TOKEN_KEY) || window.sessionStorage.getItem(ACCESS_TOKEN_KEY)
)
export const getStoredRefreshToken = () => (
  localStorage.getItem(REFRESH_TOKEN_KEY) || window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
)

export const getStoredUser = () => {
  const storage = getSessionStorage()
  const rawUser = storage.getItem(USER_KEY)
  if (!rawUser) return null
  try {
    return JSON.parse(rawUser)
  } catch {
    storage.removeItem(USER_KEY)
    return null
  }
}

export const storeAuthSession = ({ user, tokens, remember = true }) => {
  clearAuthSession()
  const storage = remember ? localStorage : window.sessionStorage
  storage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
  storage.setItem(USER_KEY, JSON.stringify(user))
}

export const storeRefreshedTokens = ({ access, refresh }) => {
  const storage = getSessionStorage()
  storage.setItem(ACCESS_TOKEN_KEY, access)
  if (refresh) {
    storage.setItem(REFRESH_TOKEN_KEY, refresh)
  }
}

export const storeCurrentUser = (user) => {
  getSessionStorage().setItem(USER_KEY, JSON.stringify(user))
}

export const clearAuthSession = () => {
  for (const storage of [localStorage, window.sessionStorage]) {
    storage.removeItem(ACCESS_TOKEN_KEY)
    storage.removeItem(REFRESH_TOKEN_KEY)
    storage.removeItem(USER_KEY)
  }
}
