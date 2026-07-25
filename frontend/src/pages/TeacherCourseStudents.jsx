import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, ChevronLeft, ChevronRight, Loader2, Search, SlidersHorizontal, UserRound, X } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { analyticsService } from '../services/analyticsService'
import { courseService } from '../services/courseService'

const clampPercent = (value) => Math.min(100, Math.max(0, Number(value || 0)))
const formatDate = (value) => value
  ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium' }).format(new Date(value))
  : 'Chưa có'

export default function TeacherCourseStudents() {
  const { courseId } = useParams()
  const [course, setCourse] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState('name')
  const [pageSize, setPageSize] = useState(20)
  const [page, setPage] = useState(1)
  const [selectedLearner, setSelectedLearner] = useState(null)

  useEffect(() => {
    let active = true
    const offset = (page - 1) * pageSize
    Promise.all([
      courseService.getManagedCourses(),
      analyticsService.getProgressReport({ course_id: courseId, limit: pageSize, offset }),
    ])
      .then(([managedCourses, data]) => {
        if (!active) return
        const ownedCourse = managedCourses.find((item) => String(item.id) === String(courseId))
        if (!ownedCourse) throw new Error('NOT_OWNED')
        setCourse(ownedCourse)
        setReport(data)
      })
      .catch((requestError) => {
        if (!active) return
        setError(requestError.message === 'NOT_OWNED'
          ? 'Không tìm thấy khóa học trong danh sách bạn được quyền quản lý.'
          : 'Không thể tải danh sách học viên lúc này.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [courseId, page, pageSize])

  const learners = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('vi')
    return [...(report?.learners || [])]
      .filter((learner) => {
        const progress = clampPercent(learner.progress_percentage)
        const matchesQuery = !normalized
          || (learner.full_name || '').toLocaleLowerCase('vi').includes(normalized)
          || String(learner.user_id).includes(normalized)
        const matchesFilter = filter === 'all'
          || (filter === 'not_started' && progress === 0)
          || (filter === 'in_progress' && progress > 0 && progress < 100)
          || (filter === 'completed' && (progress >= 100 || learner.completed_at))
          || (filter === 'no_assessment' && Number(learner.assessments_attempted || 0) === 0)
        return matchesQuery && matchesFilter
      })
      .sort((first, second) => {
        if (sort === 'progress_asc') return clampPercent(first.progress_percentage) - clampPercent(second.progress_percentage)
        if (sort === 'progress_desc') return clampPercent(second.progress_percentage) - clampPercent(first.progress_percentage)
        if (sort === 'recent') return new Date(second.latest_assessment_at || 0) - new Date(first.latest_assessment_at || 0)
        return (first.full_name || '').localeCompare(second.full_name || '', 'vi')
      })
  }, [filter, query, report?.learners, sort])

  const total = report?.pagination?.count || 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const changePageSize = (value) => {
    setPageSize(Number(value))
    setPage(1)
    setLoading(true)
  }

  const changePage = (nextPage) => {
    setPage(nextPage)
    setLoading(true)
  }

  if (loading && !report) {
    return <div className="mx-auto flex min-h-[50vh] max-w-6xl items-center justify-center gap-2 px-4 text-white/70" role="status"><Loader2 className="h-5 w-5 animate-spin" />Đang tải danh sách học viên…</div>
  }

  if (error || !course) {
    return <div className="mx-auto max-w-3xl px-4 py-12 text-white"><div className="rounded-2xl border border-white/15 bg-white/10 p-6"><h1 className="text-xl font-bold">Không thể mở danh sách học viên</h1><p className="mt-2 text-white/65">{error}</p><Link to="/teacher/courses" className="mt-5 inline-flex min-h-11 items-center font-semibold text-orange-300"><ArrowLeft className="mr-2 h-4 w-4" />Quay lại quản lý khóa học</Link></div></div>
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] py-6 text-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <nav aria-label="Breadcrumb" className="mb-2 overflow-x-auto text-sm text-white/55">
          <ol className="flex min-h-11 items-center gap-2 whitespace-nowrap">
            <li><Link to="/" className="hover:text-orange-300">Trang chủ</Link></li>
            <li aria-hidden="true">/</li>
            <li><Link to="/teacher/courses" className="hover:text-orange-300">Quản lý khóa học</Link></li>
            <li aria-hidden="true">/</li>
            <li><Link to={`/teacher/courses/${course.id}`} className="max-w-64 truncate hover:text-orange-300">{course.title}</Link></li>
            <li aria-hidden="true">/</li>
            <li className="font-semibold text-white" aria-current="page">Quản lý học viên</li>
          </ol>
        </nav>
        <Link to={`/teacher/courses/${course.id}`} className="inline-flex min-h-11 items-center rounded-lg text-sm font-semibold text-white/65 hover:text-orange-300"><ArrowLeft className="mr-2 h-4 w-4" />Quay lại chi tiết khóa học</Link>
        <header className="mt-3">
          <div className="flex items-center gap-3"><UserRound className="h-7 w-7 text-orange-300" /><h1 className="text-2xl font-bold">Danh sách học viên</h1></div>
          <p className="mt-2 text-white/65">{total} học viên đã đăng ký khóa học {course.title}.</p>
        </header>

        <section className="mt-6 overflow-hidden rounded-2xl border border-white/15 bg-[#2d1c2e]/80 backdrop-blur-md">
          <div className="grid gap-3 border-b border-white/10 p-4 lg:grid-cols-[minmax(260px,1fr)_220px_190px]">
            <label className="relative"><span className="sr-only">Tìm theo tên hoặc mã học viên</span><Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-white/45" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm theo tên hoặc mã học viên..." className="min-h-11 w-full rounded-lg border border-white/15 bg-black/20 pl-10 pr-3 text-sm outline-none placeholder:text-white/40 focus:border-orange-400" /></label>
            <label className="relative"><span className="sr-only">Lọc trạng thái</span><SlidersHorizontal className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-white/45" /><select value={filter} onChange={(event) => setFilter(event.target.value)} className="min-h-11 w-full rounded-lg border border-white/15 bg-[#321c2d] pl-10 pr-3 text-sm outline-none focus:border-orange-400"><option value="all">Tất cả trạng thái</option><option value="not_started">Chưa bắt đầu</option><option value="in_progress">Đang học</option><option value="completed">Đã hoàn thành</option><option value="no_assessment">Chưa làm bài kiểm tra</option></select></label>
            <label><span className="sr-only">Sắp xếp</span><select value={sort} onChange={(event) => setSort(event.target.value)} className="min-h-11 w-full rounded-lg border border-white/15 bg-[#321c2d] px-3 text-sm outline-none focus:border-orange-400"><option value="name">Tên A–Z</option><option value="progress_asc">Tiến độ thấp nhất</option><option value="progress_desc">Tiến độ cao nhất</option><option value="recent">Đánh giá gần nhất</option></select></label>
          </div>

          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-white/50"><tr><th className="px-4 py-3">Học viên</th><th className="px-4 py-3">Mã học viên</th><th className="px-4 py-3">Bài gần nhất</th><th className="px-4 py-3">Tiến độ</th><th className="px-4 py-3">Nắm vững</th><th className="px-4 py-3">Bài kiểm tra</th><th className="px-4 py-3">Hoạt động gần nhất</th><th className="px-4 py-3 text-right">Hành động</th></tr></thead>
              <tbody className="divide-y divide-white/10">
                {learners.map((learner) => {
                  const progress = clampPercent(learner.progress_percentage)
                  return <tr key={learner.user_id} className="hover:bg-white/5"><td className="px-4 py-3"><div className="flex items-center gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-orange-500/20 font-bold text-orange-200">{learner.full_name?.charAt(0) || 'H'}</span><strong className="max-w-48 truncate">{learner.full_name || 'Học viên'}</strong></div></td><td className="px-4 py-3 text-white/60">#{learner.user_id}</td><td className="max-w-52 truncate px-4 py-3 text-white/65">{learner.last_accessed_lesson?.title || 'Chưa bắt đầu'}</td><td className="px-4 py-3"><div className="flex min-w-32 items-center gap-2"><div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/15"><div className="h-full bg-orange-500" style={{ width: `${progress}%` }} /></div><strong className="text-xs text-orange-300">{progress.toFixed(0)}%</strong></div></td><td className="px-4 py-3">{clampPercent(learner.mastery_percentage).toFixed(0)}%</td><td className="px-4 py-3">{learner.assessments_attempted || 0}</td><td className="px-4 py-3 text-white/60">{formatDate(learner.latest_assessment_at)}</td><td className="px-4 py-3 text-right"><button type="button" onClick={() => setSelectedLearner(learner)} className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-orange-300 hover:bg-white/10" aria-label={`Xem chi tiết ${learner.full_name}`} title="Xem chi tiết"><Search className="h-5 w-5" /></button></td></tr>
                })}
              </tbody>
            </table>
          </div>

          <div className="divide-y divide-white/10 md:hidden">
            {learners.map((learner) => <article key={learner.user_id} className="p-4"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20 font-bold text-orange-200">{learner.full_name?.charAt(0) || 'H'}</span><div className="min-w-0 flex-1"><h2 className="truncate font-semibold">{learner.full_name || 'Học viên'}</h2><p className="text-xs text-white/50">Mã #{learner.user_id}</p></div><button type="button" onClick={() => setSelectedLearner(learner)} className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-orange-300 hover:bg-white/10" aria-label={`Xem chi tiết ${learner.full_name}`}><Search className="h-5 w-5" /></button></div><div className="mt-4 flex justify-between text-xs"><span>Tiến độ {clampPercent(learner.progress_percentage).toFixed(0)}%</span><span>Nắm vững {clampPercent(learner.mastery_percentage).toFixed(0)}%</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/15"><div className="h-full bg-orange-500" style={{ width: `${clampPercent(learner.progress_percentage)}%` }} /></div></article>)}
          </div>

          {learners.length === 0 && <p className="p-8 text-center text-sm text-white/60">Không có học viên phù hợp trên trang này.</p>}

          <footer className="flex flex-col gap-3 border-t border-white/10 p-4 sm:flex-row sm:items-center sm:justify-between">
            <label className="text-sm text-white/60">Số dòng mỗi trang <select value={pageSize} onChange={(event) => changePageSize(event.target.value)} className="ml-2 min-h-11 rounded-lg border border-white/15 bg-[#321c2d] px-3 text-white"><option value="10">10</option><option value="20">20</option><option value="50">50</option></select></label>
            <div className="flex items-center gap-2"><button type="button" onClick={() => changePage(page - 1)} disabled={page <= 1 || loading} className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-white/15 disabled:opacity-40" aria-label="Trang trước"><ChevronLeft className="h-5 w-5" /></button><span className="px-2 text-sm">Trang <strong className="text-orange-300">{page}</strong> / {totalPages}</span><button type="button" onClick={() => changePage(page + 1)} disabled={page >= totalPages || loading} className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-white/15 disabled:opacity-40" aria-label="Trang sau"><ChevronRight className="h-5 w-5" /></button></div>
          </footer>
        </section>
      </div>

      {selectedLearner && <div className="fixed inset-0 z-[90] flex justify-end bg-slate-950/70" onMouseDown={(event) => event.target === event.currentTarget && setSelectedLearner(null)}><aside className="h-full w-full max-w-md overflow-y-auto border-l border-white/10 bg-[#2a192c] p-5 shadow-2xl sm:p-6" aria-label={`Chi tiết ${selectedLearner.full_name}`}><button type="button" onClick={() => setSelectedLearner(null)} className="ml-auto flex h-11 w-11 items-center justify-center rounded-lg text-white/70 hover:bg-white/10" aria-label="Đóng"><X className="h-5 w-5" /></button><div className="mt-5 flex items-center gap-4"><span className="flex h-14 w-14 items-center justify-center rounded-full bg-orange-500/20 text-xl font-bold text-orange-200">{selectedLearner.full_name?.charAt(0) || 'H'}</span><div><h2 className="text-xl font-bold">{selectedLearner.full_name || 'Học viên'}</h2><p className="text-sm text-white/50">Mã học viên #{selectedLearner.user_id}</p></div></div><dl className="mt-7 grid gap-3">{[['Bài học gần nhất', selectedLearner.last_accessed_lesson?.title || 'Chưa bắt đầu'], ['Tiến độ tổng thể', `${clampPercent(selectedLearner.progress_percentage).toFixed(0)}%`], ['Mức độ nắm vững', `${clampPercent(selectedLearner.mastery_percentage).toFixed(0)}%`], ['Số bài kiểm tra đã làm', selectedLearner.assessments_attempted || 0], ['Số bài kiểm tra đạt', selectedLearner.assessments_passed || 0], ['Hoạt động đánh giá gần nhất', formatDate(selectedLearner.latest_assessment_at)], ['Hoàn thành khóa học', formatDate(selectedLearner.completed_at)]].map(([label, value]) => <div key={label} className="rounded-xl border border-white/10 bg-white/5 p-4"><dt className="text-xs text-white/50">{label}</dt><dd className="mt-1 font-semibold">{value}</dd></div>)}</dl><p className="mt-5 rounded-xl border border-orange-300/20 bg-orange-500/10 p-4 text-sm leading-6 text-orange-100">API hiện tại không cung cấp email, ngày tham gia, điểm trung bình hoặc lịch sử theo từng bài học. Các thông tin đó không được dựng giả trên giao diện.</p></aside></div>}
    </div>
  )
}
