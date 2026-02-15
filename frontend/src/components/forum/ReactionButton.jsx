import { useState, useRef, useEffect } from 'react'

const REACTIONS = [
  { type: 'like', emoji: '👍', label: 'Thích' },
  { type: 'love', emoji: '❤️', label: 'Yêu thích' },
  { type: 'haha', emoji: '😂', label: 'Haha' },
  { type: 'wow', emoji: '😮', label: 'Wow' },
  { type: 'sad', emoji: '😢', label: 'Buồn' },
  { type: 'angry', emoji: '😡', label: 'Phẫn nộ' },
]

export default function ReactionButton({ reactions = {}, onReact }) {
  const [showPicker, setShowPicker] = useState(false)
  const pickerRef = useRef(null)
  const timerRef = useRef(null)

  // reactions = { counts: { like: 5, love: 2 }, total: 7, user_reaction: 'like' }
  const counts = reactions.counts || {}
  const total = reactions.total || 0
  const userReaction = reactions.user_reaction

  useEffect(() => {
    return () => clearTimeout(timerRef.current)
  }, [])

  const handleMouseEnter = () => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setShowPicker(true), 300)
  }

  const handleMouseLeave = () => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setShowPicker(false), 400)
  }

  const handleReact = (type) => {
    onReact?.(type)
    setShowPicker(false)
  }

  // Get top 3 reactions by count
  const topReactions = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([type]) => REACTIONS.find(r => r.type === type))
    .filter(Boolean)

  const activeReaction = REACTIONS.find(r => r.type === userReaction)

  return (
    <div
      className="relative flex items-center"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      ref={pickerRef}
    >
      {/* Main button */}
      <button
        onClick={() => handleReact(userReaction || 'like')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
          userReaction
            ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
            : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70 border border-white/5'
        }`}
      >
        {/* Show top reaction emojis */}
        {topReactions.length > 0 ? (
          <span className="flex -space-x-1">
            {topReactions.map((r) => (
              <span key={r.type} className="text-sm">{r.emoji}</span>
            ))}
          </span>
        ) : (
          <span className="text-sm">👍</span>
        )}
        {total > 0 && <span>{total}</span>}
        {!total && !userReaction && <span>Thích</span>}
      </button>

      {/* Reaction picker popup */}
      {showPicker && (
        <div className="absolute bottom-full left-0 mb-2 z-50">
          <div className="bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-full px-2 py-1.5 flex items-center gap-0.5 shadow-2xl shadow-black/50">
            {REACTIONS.map((r) => (
              <button
                key={r.type}
                onClick={() => handleReact(r.type)}
                className={`group/emoji relative p-1.5 rounded-full transition-all duration-200 hover:scale-125 hover:bg-white/10 ${
                  userReaction === r.type ? 'bg-orange-500/20 scale-110' : ''
                }`}
                title={r.label}
              >
                <span className="text-xl">{r.emoji}</span>
                {/* Tooltip */}
                <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-0.5 bg-black/90 text-white/80 text-[10px] rounded whitespace-nowrap opacity-0 group-hover/emoji:opacity-100 transition-opacity pointer-events-none">
                  {r.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
