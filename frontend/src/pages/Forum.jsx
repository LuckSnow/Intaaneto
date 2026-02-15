import { useState, useEffect, useCallback } from 'react'
import { Search, Plus, Filter, TrendingUp, Flame, Clock, CheckCircle } from 'lucide-react'
import PostCard from '../components/forum/PostCard'
import CreatePostModal from '../components/forum/CreatePostModal'
import TagBadge from '../components/forum/TagBadge'
import ReportModal from '../components/forum/ReportModal'
import { forumService } from '../services/forumService'
import { useAuthStore } from '../store/authStore'

const CATEGORIES = [
  { value: '', label: 'Tất cả', icon: <Flame className="w-4 h-4" /> },
  { value: 'question', label: 'Câu hỏi', icon: '❓' },
  { value: 'discussion', label: 'Thảo luận', icon: '💬' },
  { value: 'showcase', label: 'Chia sẻ', icon: '🚀' },
  { value: 'announcement', label: 'Thông báo', icon: '📢' },
]

const SORT_OPTIONS = [
  { value: '-created_at', label: 'Mới nhất', icon: <Clock className="w-3.5 h-3.5" /> },
  { value: '-views_count', label: 'Phổ biến', icon: <TrendingUp className="w-3.5 h-3.5" /> },
  { value: 'is_solved', label: 'Chưa giải', icon: <CheckCircle className="w-3.5 h-3.5" /> },
]

export default function Forum() {
  const user = useAuthStore((s) => s.user)
  const [posts, setPosts] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)

  // Filters
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [selectedTag, setSelectedTag] = useState(null)
  const [sort, setSort] = useState('-created_at')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)

  // Modals
  const [showCreate, setShowCreate] = useState(false)
  const [reportTarget, setReportTarget] = useState(null)

  const fetchPosts = useCallback(async () => {
    setLoading(true)
    try {
      const params = { ordering: sort, page }
      if (search) params.search = search
      if (category) params.category = category
      if (selectedTag) params.tag = selectedTag
      const res = await forumService.getPosts(params)
      const data = res.data
      // handle paginated or plain array
      if (Array.isArray(data)) {
        setPosts(data)
        setHasNext(false)
      } else {
        setPosts(data.results || [])
        setHasNext(!!data.next)
      }
    } catch (err) {
      console.error('Failed to fetch posts:', err)
    } finally {
      setLoading(false)
    }
  }, [search, category, selectedTag, sort, page])

  const fetchTags = async () => {
    try {
      const res = await forumService.getTags()
      setTags(Array.isArray(res.data) ? res.data : res.data.results || [])
    } catch {}
  }

  useEffect(() => { fetchTags() }, [])
  useEffect(() => { fetchPosts() }, [fetchPosts])

  const handleReact = async (postId, type) => {
    try {
      await forumService.reactToPost(postId, type)
      fetchPosts()
    } catch {}
  }

  const handleReport = async ({ reason, description }) => {
    if (!reportTarget) return
    try {
      await forumService.reportPost(reportTarget, { reason, description })
    } catch {}
    setReportTarget(null)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    // fetchPosts will fire via useEffect
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Hero / Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-orange-500/5 via-transparent to-transparent" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl" />
        <div className="absolute top-10 right-1/4 w-72 h-72 bg-red-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 pt-8 pb-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                Diễn đàn <span className="bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">Intaaneto</span>
              </h1>
              <p className="text-white/40 text-sm">Hỏi đáp, thảo luận và chia sẻ kiến thức cùng cộng đồng</p>
            </div>

            {user && (
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 text-white font-medium text-sm hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] transition-all"
              >
                <Plus className="w-4 h-4" /> Tạo bài viết
              </button>
            )}
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="relative mb-4">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm kiếm bài viết..."
              className="w-full bg-white/[0.05] backdrop-blur-sm border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white text-sm focus:outline-none focus:border-orange-500/30 placeholder:text-white/20 transition-colors"
            />
          </form>

          {/* Category tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {CATEGORIES.map(cat => (
              <button
                key={cat.value}
                onClick={() => { setCategory(cat.value); setPage(1) }}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  category === cat.value
                    ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-[0_0_15px_rgba(249,115,22,0.3)]'
                    : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70 border border-white/5'
                }`}
              >
                {typeof cat.icon === 'string' ? <span>{cat.icon}</span> : cat.icon}
                {cat.label}
              </button>
            ))}

            {/* Sort */}
            <div className="ml-auto flex items-center gap-1.5">
              {SORT_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => { setSort(opt.value); setPage(1) }}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    sort === opt.value
                      ? 'bg-white/10 text-orange-400'
                      : 'text-white/30 hover:text-white/50'
                  }`}
                >
                  {opt.icon} {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 pb-12">
        <div className="flex gap-6">
          {/* Posts feed */}
          <div className="flex-1 min-w-0 space-y-4">
            {loading ? (
              // Skeleton loading
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="bg-white/[0.05] rounded-2xl p-5 animate-pulse">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-white/10" />
                    <div className="space-y-2">
                      <div className="w-24 h-3 bg-white/10 rounded" />
                      <div className="w-16 h-2 bg-white/5 rounded" />
                    </div>
                  </div>
                  <div className="w-3/4 h-5 bg-white/10 rounded mb-2" />
                  <div className="w-full h-3 bg-white/5 rounded mb-1" />
                  <div className="w-2/3 h-3 bg-white/5 rounded" />
                </div>
              ))
            ) : posts.length === 0 ? (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">📭</div>
                <h3 className="text-white/50 text-lg font-medium mb-2">Chưa có bài viết nào</h3>
                <p className="text-white/30 text-sm">Hãy là người đầu tiên đăng bài!</p>
              </div>
            ) : (
              posts.map(post => (
                <PostCard key={post.id} post={post} onReact={handleReact} />
              ))
            )}

            {/* Pagination */}
            {(page > 1 || hasNext) && (
              <div className="flex justify-center gap-3 pt-4">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/50 text-sm disabled:opacity-30 hover:bg-white/10 transition-all"
                >
                  ← Trước
                </button>
                <span className="px-4 py-2 text-white/30 text-sm">Trang {page}</span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={!hasNext}
                  className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/50 text-sm disabled:opacity-30 hover:bg-white/10 transition-all"
                >
                  Tiếp →
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="hidden lg:block w-72 flex-shrink-0 space-y-4">
            {/* Tags */}
            <div className="bg-white/[0.05] backdrop-blur-md border border-white/10 rounded-2xl p-4">
              <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
                🏷️ Chủ đề nổi bật
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {tags.map(tag => (
                  <TagBadge
                    key={tag.id}
                    tag={tag}
                    selected={selectedTag === tag.slug}
                    onClick={() => {
                      setSelectedTag(selectedTag === tag.slug ? null : tag.slug)
                      setPage(1)
                    }}
                    size="xs"
                  />
                ))}
                {tags.length === 0 && (
                  <p className="text-white/20 text-xs">Chưa có tag nào</p>
                )}
              </div>
            </div>

            {/* Quick stats */}
            <div className="bg-white/[0.05] backdrop-blur-md border border-white/10 rounded-2xl p-4">
              <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
                📊 Thống kê
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-white/40">Tổng bài viết</span>
                  <span className="text-white/70 font-medium">{posts.length}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-white/40">Đã giải quyết</span>
                  <span className="text-green-400 font-medium">{posts.filter(p => p.is_solved).length}</span>
                </div>
              </div>
            </div>

            {/* Rules */}
            <div className="bg-white/[0.05] backdrop-blur-md border border-white/10 rounded-2xl p-4">
              <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
                📋 Quy tắc
              </h3>
              <ul className="space-y-1.5 text-white/40 text-xs">
                <li>• Tôn trọng mọi thành viên</li>
                <li>• Không spam hay quảng cáo</li>
                <li>• Đặt tiêu đề rõ ràng, cụ thể</li>
                <li>• Đánh dấu "Đã giải" khi có câu trả lời</li>
                <li>• Sử dụng tag phù hợp</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Create Post Modal */}
      <CreatePostModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={() => { fetchPosts(); setShowCreate(false) }}
        tags={tags}
      />

      {/* Report Modal */}
      <ReportModal
        isOpen={!!reportTarget}
        onClose={() => setReportTarget(null)}
        onSubmit={handleReport}
        targetType="post"
      />
    </div>
  )
}
