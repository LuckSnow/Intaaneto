export const VIDEO_SCRIPT_MAX_CHARS = 4800
export const VIDEO_SCRIPT_MAX_SEGMENTS = 50
export const VIDEO_SCRIPT_SEGMENT_MAX_CHARS = 180
export const VIDEO_SCRIPT_TARGET_MIN_CHARS = 3800
export const VIDEO_SCRIPT_TARGET_MAX_CHARS = 4600

const splitLongPart = (text) => {
  const chunks = []
  let current = []

  text.split(/\s+/).filter(Boolean).forEach((word) => {
    const candidate = [...current, word].join(' ')
    if (current.length > 0 && candidate.length > VIDEO_SCRIPT_SEGMENT_MAX_CHARS) {
      chunks.push(current.join(' '))
      current = [word]
    } else {
      current.push(word)
    }
  })

  if (current.length > 0) chunks.push(current.join(' '))
  return chunks
}

export const getVideoScriptMetrics = (value, limits = {}) => {
  const maxChars = limits.maxChars || VIDEO_SCRIPT_MAX_CHARS
  const maxSegments = limits.maxSegments || VIDEO_SCRIPT_MAX_SEGMENTS
  const normalized = (value || '')
    .replace(/\r/g, '')
    .replace(/[ \t]+/g, ' ')
    .trim()
  const parts = normalized
    ? normalized.replace(/([.!?])\s+/g, '$1\n').split(/\n+/)
      .map((part) => part.replace(/^[\s•-]+|[\s•-]+$/g, ''))
      .filter(Boolean)
    : []
  const segmentCount = parts.reduce(
    (count, part) => count + splitLongPart(part).length,
    0,
  )

  return {
    characterCount: normalized.length,
    segmentCount,
    slideCount: Math.ceil(segmentCount / 2),
    isReady: (
      normalized.length > 0
      && normalized.length <= maxChars
      && segmentCount > 0
      && segmentCount <= maxSegments
    ),
  }
}
