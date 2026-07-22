function addVersion(url, version) {
  if (!url || !version) return url
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}v=${encodeURIComponent(version)}`
}

export function getUserAvatar(user) {
  if (user?.avatar) return addVersion(user.avatar, user.updated_at)
  return user?.google_avatar || null
}
