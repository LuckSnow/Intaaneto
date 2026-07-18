import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageCircle, Eye, Pin, CheckCircle, Clock } from 'lucide-react'
import ReactionButton from './ReactionButton'

const CATEGORY_STYLES = {
  question: { label: 'Câu hỏi', icon: '❓', color: 'from-blue-500 to-cyan-500' },
  discussion: { label: 'Thảo luận', icon: '💬', color: 'from-purple-500 to-pink-500' },
  showcase: { label: 'Chia sẻ', icon: '🚀', color: 'from-orange-500 to-red-500' },
  announcement: { label: 'Thông báo', icon: '📢', color: 'from-yellow-500 to-orange-500' },
}

function timeAgo(dateStr) {
  const now = new Date()
  const date = new Date(dateStr)
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return 'vừa xong'
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`
  if (diff < 604800) return `${Math.floor(diff / 86400)} ngày trước`
  return date.toLocaleDateString('vi-VN')
}

export default function PostCard({ post, onReact }) {
  const cat = CATEGORY_STYLES[post.category] || CATEGORY_STYLES.question
  const images = [post.image_1, post.image_2, post.image_3, post.image_4].filter(Boolean)
  const [lightboxImg, setLightboxImg] = useState(null)

  return (
    <div className="group relative">
      {/* Glow on hover */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-500/0 to-red-500/0 group-hover:from-orange-500/20 group-hover:to-red-500/20 rounded-2xl blur transition-all duration-300" />

      <div className="relative bg-white/[0.07] backdrop-blur-md border border-white/10 rounded-2xl p-5 hover:bg-white/[0.1] transition-all duration-300">
        {/* Top row: author + category + time */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {post.author?.full_name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="text-white font-medium text-sm">{post.author?.full_name}</p>
              <div className="flex items-center gap-2 text-white/50 text-xs">
                <Clock className="w-3 h-3" />
                <span>{timeAgo(post.created_at)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {post.is_pinned && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">
                <Pin className="w-3 h-3" /> Ghim
              </span>
            )}
            {post.is_solved && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs">
                <CheckCircle className="w-3 h-3" /> Đã giải
              </span>
            )}
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r ${cat.color} text-white`}>
              {cat.icon} {cat.label}
            </span>
          </div>
        </div>

        {/* Title */}
        <Link to={`/forum/${post.id}`} className="block mb-2">
          <h3 className="text-lg font-bold text-white hover:text-orange-400 transition-colors line-clamp-2">
            {post.title}
          </h3>
        </Link>

        {/* Content preview */}
        <p className="text-white/60 text-sm line-clamp-3 mb-3">
          {post.content}
        </p>

        {/* Images grid */}
        {images.length > 0 && (
          <div className={`grid gap-2 mb-3 ${
            images.length === 1 ? 'grid-cols-1' :
            images.length === 2 ? 'grid-cols-2' :
            'grid-cols-2'
          }`}>
            {images.slice(0, 4).map((img, idx) => (
              <button key={idx} type="button" onClick={() => setLightboxImg(img)} className={`rounded-xl overflow-hidden border border-white/10 text-left ${
                images.length === 1 ? 'max-h-72' :
                images.length === 3 && idx === 0 ? 'row-span-2' : 'max-h-36'
              }`}>
                <img
                  src={img}
                  alt=""
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-300 cursor-zoom-in"
                />
              </button>
            ))}
          </div>
        )}

        {/* Tags */}
        {post.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {post.tags.map(tag => (
              <span
                key={tag.id}
                className="px-2 py-0.5 rounded-full text-[10px] font-medium text-white/90"
                style={{ backgroundColor: tag.color + '33', color: tag.color }}
              >
                #{tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Bottom: reactions + stats */}
        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          <ReactionButton
            reactions={post.reactions_summary}
            onReact={(type) => onReact?.(post.id, type)}
          />
          <div className="flex items-center gap-4 text-white/40 text-xs">
            <Link
              to={`/forum/${post.id}`}
              className="flex items-center gap-1 hover:text-white transition-colors"
              title="Xem bình luận"
            >
              <MessageCircle className="w-3.5 h-3.5" /> {post.comments_count || 0}
            </Link>
            <Link
              to={`/forum/${post.id}`}
              className="flex items-center gap-1 hover:text-white transition-colors"
              title="Xem bài viết"
            >
              <Eye className="w-3.5 h-3.5" /> {post.views_count || 0}
            </Link>
          </div>
        </div>
      </div>

      {lightboxImg && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8 cursor-pointer"
          onClick={() => setLightboxImg(null)}
        >
          <img src={lightboxImg} alt="" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}
    </div>
  )
}
