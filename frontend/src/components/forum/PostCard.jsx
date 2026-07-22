import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageCircle, Eye, Pin, CheckCircle, Clock } from 'lucide-react'
import ReactionButton from './ReactionButton'
import { getUserAvatar } from '../../utils/avatar'

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

export default function PostCard({ post, onReact, onCourseClick }) {
  const images = [post.image_1, post.image_2, post.image_3, post.image_4].filter(Boolean)
  const [lightboxImg, setLightboxImg] = useState(null)
  const authorAvatar = getUserAvatar(post.author)

  return (
    <div className="group relative">
      <div className="relative rounded-2xl border border-white/10 bg-slate-950/45 p-4 backdrop-blur-md transition-colors hover:border-white/20 hover:bg-slate-950/55 sm:p-5">
        {/* Top row: author + category + time */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            {authorAvatar ? (
              <img src={authorAvatar} alt="" className="h-10 w-10 flex-shrink-0 rounded-full object-cover" referrerPolicy="no-referrer" />
            ) : (
              <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-200 font-bold text-sm flex-shrink-0">{post.author?.full_name?.charAt(0) || 'U'}</div>
            )}
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
          </div>
        </div>

        {/* Title */}
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Link to={`/forum/${post.id}`} className="min-w-0">
            <h3 className="line-clamp-2 text-lg font-bold text-white transition-colors hover:text-orange-300">{post.title}</h3>
          </Link>
          {post.course && (
            <button type="button" onClick={() => onCourseClick?.(post.course.slug)} title={post.course.title} className="max-w-full shrink-0 truncate rounded-full border border-orange-400/30 bg-orange-500/10 px-2.5 py-1 text-xs font-semibold text-orange-300 transition-colors hover:border-orange-400/60 hover:bg-orange-500/20 hover:text-orange-200">#{post.course.slug}</button>
          )}
        </div>

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
              <button key={idx} type="button" onClick={() => setLightboxImg(img)} className={`w-full overflow-hidden rounded-xl border border-white/10 text-left ${
                images.length === 1 ? 'h-52 sm:h-72' :
                images.length === 3 && idx === 0 ? 'row-span-2 h-full min-h-52 max-h-72' : 'h-32 sm:h-40'
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
