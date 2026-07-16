export const getDefaultAuthenticatedPath = (user) => {
  if (user?.role === 'teacher' || user?.role === 'admin') {
    return '/teacher/upload'
  }
  return '/dashboard'
}

export const getPostLoginPath = (user, requestedPath) => {
  const isSafeInternalPath = (
    typeof requestedPath === 'string'
    && requestedPath.startsWith('/')
    && !requestedPath.startsWith('//')
    && requestedPath !== '/login'
    && requestedPath !== '/teacher/login'
    && requestedPath !== '/register'
  )
  return isSafeInternalPath ? requestedPath : getDefaultAuthenticatedPath(user)
}
