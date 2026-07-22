import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Clock, Eye, Pin, CheckCircle, Lock,
  MoreHorizontal, Trash2, Flag, Share2, Bookmark
} from 'lucide-react'
import CommentSection from '../components/forum/CommentSection'
import ReactionButton from '../components/forum/ReactionButton'
import ReportModal from '../components/forum/ReportModal'
import UserProfileCard from '../components/forum/UserProfileCard'
import { forumService } from '../services/forumService'
import { useAuthStore } from '../store/authStore'
import { getUserAvatar } from '../utils/avatar'

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

export default function ForumPost() {
  const { id } = useParams()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [lightboxImg, setLightboxImg] = useState(null)

  // Report
  const [reportOpen, setReportOpen] = useState(false)
  const [reportType, setReportType] = useState('post')
  const [reportTargetId, setReportTargetId] = useState(null)

  const fetchPost = useCallback(async () => {
    try {
      const res = await forumService.getPost(id)
      setPost(res.data)
    } catch (err) {
      console.error('Failed to fetch post:', err)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { fetchPost() }, [fetchPost])

  const handleReact = async (type) => {
    try {
      await forumService.reactToPost(id, type)
      fetchPost()
    } catch {}
  }

  const handleMarkSolved = async () => {
    try {
      await forumService.markSolved(id)
      fetchPost()
    } catch {}
  }

  const handleDelete = async () => {
    if (!confirm('Xóa bài viết này?')) return
    try {
      await forumService.deletePost(id)
      navigate('/forum')
    } catch {}
  }

  const handlePin = async () => {
    try {
      await forumService.pinPost(id)
      fetchPost()
    } catch {}
  }

  const handleClose = async () => {
    try {
      await forumService.closePost(id)
      fetchPost()
    } catch {}
  }

  const openReport = (type, targetId) => {
    setReportType(type)
    setReportTargetId(targetId)
    setReportOpen(true)
  }

  const handleReport = async ({ reason, description }) => {
    try {
      if (reportType === 'post') {
        await forumService.reportPost(reportTargetId, { reason, description })
      } else {
        await forumService.reportComment(reportTargetId, { reason, description })
      }
    } catch {}
    setReportOpen(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="flex items-center gap-3 text-white/40">
          <div className="w-6 h-6 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
          Đang tải...
        </div>
      </div>
    )
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center gap-4">
        <div className="text-5xl">😕</div>
        <h2 className="text-white text-xl font-bold">Không tìm thấy bài viết</h2>
        <Link to="/forum" className="text-orange-400 hover:text-orange-300 text-sm">← Quay lại diễn đàn</Link>
      </div>
    )
  }

  const images = [post.image_1, post.image_2, post.image_3, post.image_4].filter(Boolean)
  const authorAvatar = getUserAvatar(post.author)
  const isAuthor = user?.id === post.author?.id
  const isAdmin = user?.role === 'admin'
  const isTeacher = user?.role === 'teacher'

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Background effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-orange-500/3 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-20 right-1/3 w-72 h-72 bg-red-500/3 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Post card */}
            <div className="bg-white/[0.07] backdrop-blur-md border border-white/10 rounded-2xl p-6 mb-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {authorAvatar ? (
                    <img src={authorAvatar} alt="" className="h-12 w-12 rounded-full object-cover" referrerPolicy="no-referrer" />
                  ) : (
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-500/20 font-bold text-orange-200">{post.author?.full_name?.charAt(0) || 'U'}</div>
                  )}
                  <div>
                    <p className="text-white font-medium">{post.author?.full_name}</p>
                    <div className="flex items-center gap-2 text-white/40 text-xs">
                      <Clock className="w-3 h-3" />
                      <span>{timeAgo(post.created_at)}</span>
                      <span>•</span>
                      <Eye className="w-3 h-3" />
                      <span>{post.views_count || 0} người đã xem</span>
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
                  {post.is_closed && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-xs">
                      <Lock className="w-3 h-3" /> Đã đóng
                    </span>
                  )}
                  {post.course && (
                    <Link to={`/forum?course=${encodeURIComponent(post.course.slug)}`} title={post.course.title} className="max-w-48 truncate rounded-full border border-orange-400/30 bg-orange-500/10 px-2.5 py-1 text-xs font-semibold text-orange-300 transition-colors hover:border-orange-400/60 hover:bg-orange-500/20 hover:text-orange-200">
                      #{post.course.slug}
                    </Link>
                  )}

                  {/* Actions menu */}
                  {user && (
                    <div className="relative">
                      <button
                        onClick={() => setShowMenu(!showMenu)}
                        className="p-2 rounded-lg hover:bg-white/10 text-white/30 hover:text-white/60 transition-all"
                      >
                        <MoreHorizontal className="w-5 h-5" />
                      </button>

                      {showMenu && (
                        <div className="absolute right-0 top-full mt-1 bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-xl py-1.5 z-20 min-w-[180px] shadow-2xl">
                          {isAuthor && !post.is_solved && (
                            <button
                              onClick={() => { handleMarkSolved(); setShowMenu(false) }}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-green-400 hover:bg-white/5"
                            >
                              <CheckCircle className="w-4 h-4" /> Đánh dấu đã giải
                            </button>
                          )}
                          {(isAdmin || isTeacher) && (
                            <>
                              <button
                                onClick={() => { handlePin(); setShowMenu(false) }}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-yellow-400 hover:bg-white/5"
                              >
                                <Pin className="w-4 h-4" /> {post.is_pinned ? 'Bỏ ghim' : 'Ghim bài'}
                              </button>
                              <button
                                onClick={() => { handleClose(); setShowMenu(false) }}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-orange-400 hover:bg-white/5"
                              >
                                <Lock className="w-4 h-4" /> {post.is_closed ? 'Mở lại' : 'Đóng bài'}
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => { openReport('post', post.id); setShowMenu(false) }}
                            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-yellow-400 hover:bg-white/5"
                          >
                            <Flag className="w-4 h-4" /> Báo cáo
                          </button>
                          {isAuthor && (
                            <button
                              onClick={() => { handleDelete(); setShowMenu(false) }}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-white/5"
                            >
                              <Trash2 className="w-4 h-4" /> Xóa bài viết
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Title */}
              <h1 className="text-2xl font-bold text-white mb-4">{post.title}</h1>

              {/* Content */}
              <div className="text-white/70 text-sm leading-relaxed whitespace-pre-wrap mb-4">
                {post.content}
              </div>

              {/* Images */}
              {images.length > 0 && (
                <div className={`grid gap-2 mb-4 ${
                  images.length === 1 ? 'grid-cols-1' :
                  images.length === 2 ? 'grid-cols-2' : 'grid-cols-2'
                }`}>
                  {images.map((img, idx) => (
                    <div
                      key={idx}
                      className={`rounded-xl overflow-hidden border border-white/10 cursor-pointer ${
                        images.length === 1 ? 'max-h-96' :
                        images.length === 3 && idx === 0 ? 'row-span-2 max-h-80' : 'max-h-48'
                      }`}
                      onClick={() => setLightboxImg(img)}
                    >
                      <img src={img} alt="" className="w-full h-full object-cover hover:scale-105 transition-transform duration-300" />
                    </div>
                  ))}
                </div>
              )}

              {/* Reactions bar */}
              <div className="flex items-center justify-between pt-4 border-t border-white/5">
                <ReactionButton
                  reactions={post.reactions_summary}
                  onReact={handleReact}
                />
                <div className="flex items-center gap-3">
                  <button className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/5 transition-all">
                    <Bookmark className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => navigator.clipboard.writeText(window.location.href)}
                    className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/5 transition-all"
                    title="Copy link"
                  >
                    <Share2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Comments */}
            <div className="bg-white/[0.07] backdrop-blur-md border border-white/10 rounded-2xl p-6">
              <CommentSection
                postId={post.id}
                comments={post.comments || []}
                currentUser={user}
                isPostAuthor={isAuthor}
                onRefresh={fetchPost}
                onReport={openReport}
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="hidden lg:block w-72 flex-shrink-0 space-y-4">
            {/* Author card */}
            <UserProfileCard user={post.author} currentUserId={user?.id} />

          </div>
        </div>
      </div>

      {/* Image lightbox */}
      {lightboxImg && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8 cursor-pointer"
          onClick={() => setLightboxImg(null)}
        >
          <img src={lightboxImg} alt="" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}

      {/* Report Modal */}
      <ReportModal
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
        onSubmit={handleReport}
        targetType={reportType}
      />
    </div>
  )
}
