import { useCallback, useEffect, useMemo, useState } from 'react'
import { Flame, Plus, Search } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import CreatePostModal from '../components/forum/CreatePostModal'
import PostCard from '../components/forum/PostCard'
import ReportModal from '../components/forum/ReportModal'
import { courseService } from '../services/courseService'
import { forumService } from '../services/forumService'
import { useAuthStore } from '../store/authStore'

export default function Forum() {
  const user = useAuthStore((state) => state.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const [posts, setPosts] = useState([])
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('-created_at')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [reportTarget, setReportTarget] = useState(null)
  const selectedCourse = searchParams.get('course') || ''

  const fetchPosts = useCallback(async () => {
    setLoading(true)
    try {
      const params = { ordering: sort, page }
      if (search.trim()) params.search = search.trim()
      if (selectedCourse) params.course = selectedCourse
      const response = await forumService.getPosts(params)
      const data = response.data
      setPosts(Array.isArray(data) ? data : data.results || [])
      setHasNext(!Array.isArray(data) && Boolean(data.next))
    } catch {
      setPosts([])
      setHasNext(false)
    } finally {
      setLoading(false)
    }
  }, [page, search, selectedCourse, sort])

  useEffect(() => {
    courseService.getCourses().then(setCourses).catch(() => setCourses([]))
  }, [])

  useEffect(() => {
    fetchPosts()
  }, [fetchPosts])

  const discussedCourses = useMemo(() => {
    const slugs = new Set(posts.map((post) => post.course?.slug).filter(Boolean))
    const active = courses.filter((course) => slugs.has(course.slug) || course.slug === selectedCourse)
    const remaining = courses.filter((course) => !slugs.has(course.slug) && course.slug !== selectedCourse)
    return [...active, ...remaining].slice(0, 12)
  }, [courses, posts, selectedCourse])
  const selectCourse = (slug) => {
    setPage(1)
    setSearchParams(slug ? { course: slug } : {})
  }

  const handleReact = async (postId, type) => {
    try {
      await forumService.reactToPost(postId, type)
      fetchPosts()
    } catch {
      // Existing reaction authorization and errors remain server-owned.
    }
  }

  const handleReport = async ({ reason, description }) => {
    if (!reportTarget) return
    try {
      await forumService.reportPost(reportTarget, { reason, description })
    } catch {
      // ReportModal remains responsible for the interaction; API owns validation.
    }
    setReportTarget(null)
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] px-4 pb-14 pt-5 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/15 pb-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold sm:text-4xl">Diễn đàn Intaaneto</h1>
              <p className="mt-2 text-sm text-white/70">Hỏi đáp, thảo luận và chia sẻ kiến thức cùng cộng đồng.</p>
            </div>
            {user && (
              <button type="button" onClick={() => setShowCreate(true)} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-orange-600 px-5 text-sm font-bold text-white hover:bg-orange-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400">
                <Plus className="h-4 w-4" aria-hidden="true" /> Tạo bài viết
              </button>
            )}
          </div>

          <div className="mt-6">
            <div className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/45" aria-hidden="true" />
              <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Tìm kiếm bài viết..." className="min-h-12 w-full rounded-xl border border-white/15 bg-slate-950/45 pl-12 pr-4 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button type="button" onClick={() => selectCourse('')} className={`min-h-10 rounded-full px-4 text-sm font-semibold transition-colors ${selectedCourse ? 'border border-white/15 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white' : 'bg-orange-600 text-white'}`}>Tất cả</button>
            <div className="inline-flex rounded-lg border border-white/10 bg-black/20 p-1" aria-label="Sắp xếp bài viết">
              <button type="button" onClick={() => { setSort('-created_at'); setPage(1) }} aria-pressed={sort === '-created_at'} className={`min-h-9 rounded-md px-3 text-xs font-semibold transition-colors ${sort === '-created_at' ? 'bg-orange-500/20 text-orange-300' : 'text-white/55 hover:text-white'}`}>Mới nhất</button>
              <button type="button" onClick={() => { setSort('-views_count'); setPage(1) }} aria-pressed={sort === '-views_count'} className={`min-h-9 rounded-md px-3 text-xs font-semibold transition-colors ${sort === '-views_count' ? 'bg-orange-500/20 text-orange-300' : 'text-white/55 hover:text-white'}`}>Phổ biến</button>
            </div>
          </div>

          {selectedCourse && (
            <p className="mt-4 text-sm text-white/70">
              Đang xem bài viết với tag: <strong className="text-orange-200">#{selectedCourse}</strong>
              <button type="button" onClick={() => selectCourse('')} className="ml-3 font-semibold text-orange-300 hover:text-orange-200">Xóa bộ lọc</button>
            </p>
          )}
        </header>

        <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,3fr)_280px]">
          <main className="min-w-0 space-y-4">
            {loading ? (
              Array.from({ length: 3 }).map((_, index) => <div key={index} className="h-48 animate-pulse rounded-2xl border border-white/10 bg-white/5" />)
            ) : posts.length === 0 ? (
              <div className="rounded-2xl border border-white/15 bg-slate-950/40 px-5 py-12 text-center">
                <h2 className="font-semibold">Chưa có bài viết phù hợp</h2>
                <p className="mt-2 text-sm text-white/60">Thử từ khóa khác hoặc xóa bộ lọc khóa học.</p>
              </div>
            ) : posts.map((post) => (
              <PostCard key={post.id} post={post} onReact={handleReact} onCourseClick={selectCourse} />
            ))}

            {(page > 1 || hasNext) && (
              <nav className="flex items-center justify-center gap-3 pt-3" aria-label="Phân trang diễn đàn">
                <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page <= 1} className="min-h-11 rounded-lg border border-white/15 px-4 text-sm text-white/70 hover:bg-white/10 disabled:opacity-40">Trước</button>
                <span className="text-sm text-white/60">Trang {page}</span>
                <button type="button" onClick={() => setPage((current) => current + 1)} disabled={!hasNext} className="min-h-11 rounded-lg border border-white/15 px-4 text-sm text-white/70 hover:bg-white/10 disabled:opacity-40">Tiếp</button>
              </nav>
            )}
          </main>

          <aside className="rounded-2xl border border-white/15 bg-slate-950/45 p-5 backdrop-blur-md lg:sticky lg:top-20" aria-labelledby="course-tags-title">
            <h2 id="course-tags-title" className="flex items-center gap-2 font-bold"><Flame className="h-4 w-4 text-orange-400" aria-hidden="true" /> Chủ đề nổi bật</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {discussedCourses.map((course) => (
                <button key={course.id} type="button" onClick={() => selectCourse(course.slug)} title={course.title} aria-pressed={selectedCourse === course.slug} className={`min-h-9 max-w-full shrink-0 truncate rounded-full border px-3 text-xs font-semibold transition-colors ${selectedCourse === course.slug ? 'border-transparent bg-orange-600 text-white' : 'border-orange-400/30 bg-orange-500/10 text-orange-300 hover:border-orange-400/60 hover:bg-orange-500/20 hover:text-orange-200'}`}>#{course.slug}</button>
              ))}
              {courses.length === 0 && <p className="text-sm text-white/50">Chưa có khóa học để chọn.</p>}
            </div>
          </aside>
        </div>
      </div>

      <CreatePostModal isOpen={showCreate} onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); fetchPosts() }} courses={courses} />
      <ReportModal isOpen={Boolean(reportTarget)} onClose={() => setReportTarget(null)} onSubmit={handleReport} targetType="post" />
    </div>
  )
}
