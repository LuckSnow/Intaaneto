import { useState, useEffect } from 'react'
import { UserPlus, UserCheck, MessageCircle, BookOpen, Award } from 'lucide-react'
import { forumService } from '../../services/forumService'

export default function UserProfileCard({ user, currentUserId }) {
  const [isFollowing, setIsFollowing] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user?.id && currentUserId && user.id !== currentUserId) {
      forumService.checkFollow(user.id)
        .then(res => setIsFollowing(res.data.is_following))
        .catch(() => {})
    }
  }, [user?.id, currentUserId])

  const handleToggleFollow = async () => {
    if (!currentUserId || user.id === currentUserId) return
    setLoading(true)
    try {
      const res = await forumService.toggleFollow(user.id)
      setIsFollowing(res.data.status === 'followed')
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="bg-white/[0.07] backdrop-blur-md border border-white/10 rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white text-lg font-bold">
          {user.full_name?.charAt(0) || user.username?.charAt(0) || 'U'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-semibold truncate">{user.full_name || user.username}</p>
          <p className="text-white/40 text-xs">@{user.username}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="text-center p-2 bg-white/5 rounded-xl">
          <p className="text-white font-bold text-sm">{user.posts_count || 0}</p>
          <p className="text-white/30 text-[10px]">Bài viết</p>
        </div>
        <div className="text-center p-2 bg-white/5 rounded-xl">
          <p className="text-white font-bold text-sm">{user.followers_count || 0}</p>
          <p className="text-white/30 text-[10px]">Người theo</p>
        </div>
        <div className="text-center p-2 bg-white/5 rounded-xl">
          <p className="text-white font-bold text-sm">{user.following_count || 0}</p>
          <p className="text-white/30 text-[10px]">Đang theo</p>
        </div>
      </div>

      {/* Role badge */}
      {user.role && (
        <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium mb-3 ${
          user.role === 'teacher' ? 'bg-purple-500/20 text-purple-400' :
          user.role === 'admin' ? 'bg-red-500/20 text-red-400' :
          'bg-blue-500/20 text-blue-400'
        }`}>
          <Award className="w-2.5 h-2.5" />
          {user.role === 'teacher' ? 'Giảng viên' : user.role === 'admin' ? 'Admin' : 'Sinh viên'}
        </div>
      )}

      {/* Follow button */}
      {currentUserId && user.id !== currentUserId && (
        <button
          onClick={handleToggleFollow}
          disabled={loading}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            isFollowing
              ? 'bg-white/10 border border-white/10 text-white/70 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30'
              : 'bg-gradient-to-r from-orange-500 to-red-500 text-white hover:shadow-[0_0_15px_rgba(249,115,22,0.4)]'
          }`}
        >
          {isFollowing ? (
            <>
              <UserCheck className="w-4 h-4" /> Đang theo dõi
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4" /> Theo dõi
            </>
          )}
        </button>
      )}
    </div>
  )
}
