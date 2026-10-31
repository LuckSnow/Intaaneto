import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, BookOpen, Clock3, Edit3, FileUp, Loader2, Pencil, Search, Users } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { analyticsService } from '../services/analyticsService'
import { assessmentService } from '../services/assessmentService'
import { courseService } from '../services/courseService'

const clampPercent = (value) => Math.min(100, Math.max(0, Number(value || 0)))

export default function TeacherCourseDetail() {
  const { courseId } = useParams()
  const [course, setCourse] = useState(null)
  const [lessons, setLessons] = useState([])
  const [roster, setRoster] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    courseService.getManagedCourses()
      .then(async (managedCourses) => {
        const ownedCourse = managedCourses.find((item) => String(item.id) === String(courseId))
        if (!ownedCourse) throw new Error('NOT_OWNED')
        if (!active) return
        setCourse(ownedCourse)
        const [lessonData, rosterData] = await Promise.all([
          assessmentService.getManagedLessons(courseId),
          analyticsService.getProgressReport({ course_id: courseId }),
        ])
        if (!active) return
        setLessons(lessonData)
        setRoster(rosterData)
      })
      .catch((requestError) => {
        if (!active) return
        setError(requestError.message === 'NOT_OWNED'
          ? 'Không tìm thấy khóa học trong danh sách bạn được quyền quản lý.'
          : 'Không thể tải chi tiết khóa học lúc này.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [courseId])

  const learners = roster?.learners || []
  const averageProgress = useMemo(() => learners.length && roster?.pagination?.count === learners.length
    ? learners.reduce((sum, learner) => sum + clampPercent(learner.progress_percentage), 0) / learners.length
    : null, [learners, roster?.pagination?.count])

  if (loading) {
    return <div className="mx-auto flex min-h-[50vh] max-w-6xl items-center justify-center gap-2 px-4 text-white/70" role="status"><Loader2 className="h-5 w-5 animate-spin" />Đang tải chi tiết khóa học…</div>
  }

  if (error || !course) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-white">
        <div className="rounded-2xl border border-white/15 bg-white/10 p-6">
          <h1 className="text-xl font-bold">Không thể mở khóa học</h1>
          <p className="mt-2 text-white/65">{error}</p>
          <Link to="/teacher/courses" className="mt-5 inline-flex min-h-11 items-center font-semibold text-orange-300"><ArrowLeft className="mr-2 h-4 w-4" />Quay lại quản lý khóa học</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] py-6 text-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Link to="/teacher/courses" className="inline-flex min-h-11 items-center rounded-lg text-sm font-semibold text-white/65 hover:text-orange-300"><ArrowLeft className="mr-2 h-4 w-4" />Quản lý khóa học</Link>

        <header className="mt-3 rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur-md sm:p-7">
          {course.thumbnail && <img src={course.thumbnail} alt="" className="mb-5 aspect-video w-full max-w-lg rounded-xl bg-slate-100 object-cover" />}
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-orange-500/15 px-2.5 py-1 text-xs font-semibold text-orange-200">{course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}</span>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${course.is_published ? 'bg-emerald-400/15 text-emerald-200' : 'bg-white/10 text-white/65'}`}>{course.is_published ? 'Đã xuất bản' : 'Bản nháp'}</span>
              </div>
              <h1 className="mt-4 text-2xl font-bold sm:text-3xl">{course.title}</h1>
              <p className="mt-3 leading-7 text-white/65">{course.description}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link to={`/teacher/courses?course=${course.id}`} className="inline-flex min-h-11 items-center rounded-lg border border-white/15 px-4 text-sm font-semibold hover:bg-white/10"><Edit3 className="mr-2 h-4 w-4" />Chỉnh sửa</Link>
              <Link to={`/teacher/upload?course=${course.id}`} className="inline-flex min-h-11 items-center rounded-lg bg-orange-600 px-4 text-sm font-semibold hover:bg-orange-700"><FileUp className="mr-2 h-4 w-4" />Thêm học liệu</Link>
            </div>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-white/10 bg-black/10 p-4"><BookOpen className="h-5 w-5 text-orange-300" /><p className="mt-3 text-xs text-white/50">Bài học</p><p className="mt-1 text-lg font-bold">{course.lessons_count || lessons.length}</p></div>
            <Link to={`/teacher/courses/${course.id}/students`} className="group rounded-xl border border-white/10 bg-black/10 p-4 transition hover:border-orange-300/50 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400">
              <div className="flex items-center justify-between"><Users className="h-5 w-5 text-orange-300" /><ArrowRight className="h-4 w-4 text-white/35 transition group-hover:translate-x-0.5 group-hover:text-orange-300" /></div>
              <p className="mt-3 text-xs text-white/50">Học viên</p><p className="mt-1 text-lg font-bold">{roster?.pagination?.count ?? course.total_students ?? 0}</p><span className="mt-1 block text-xs font-semibold text-orange-300">Xem danh sách</span>
            </Link>
            <div className="rounded-xl border border-white/10 bg-black/10 p-4"><Clock3 className="h-5 w-5 text-orange-300" /><p className="mt-3 text-xs text-white/50">Thời lượng</p><p className="mt-1 text-lg font-bold">{course.duration_hours || 0} giờ</p></div>
            <div className="rounded-xl border border-white/10 bg-black/10 p-4"><Users className="h-5 w-5 text-orange-300" /><p className="mt-3 text-xs text-white/50">Tiến độ trung bình</p><p className="mt-1 text-lg font-bold">{averageProgress === null ? '—' : `${averageProgress.toFixed(0)}%`}</p></div>
          </div>
        </header>

        <div className="mt-6">
          <section className="rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur-md">
            <div className="flex items-center justify-between gap-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Nội dung khóa học</p><h2 className="mt-1 text-lg font-bold">Danh sách bài học</h2></div>
              <span className="text-sm text-white/60">{lessons.length} bài</span>
            </div>
            {lessons.length === 0 ? (
              <div className="mt-5 rounded-xl border border-white/10 p-5 text-sm text-white/65"><p>Khóa học này chưa có bài học.</p><Link to={`/teacher/upload?course=${course.id}`} className="mt-3 inline-flex min-h-11 items-center font-semibold text-orange-300">Tải học liệu</Link></div>
            ) : (
              <div className="mt-4 divide-y divide-white/10">
                {lessons.map((lesson, index) => (
                  <article key={lesson.id} className="grid grid-cols-[32px_minmax(0,1fr)_auto] items-center gap-3 py-3">
                    <span className="text-xs font-bold text-white/40">{String(index + 1).padStart(2, '0')}</span>
                    <div className="min-w-0"><h3 className="truncate text-sm font-semibold">{lesson.title}</h3><p className="mt-1 text-xs text-white/55">{lesson.duration_minutes || 0} phút · {lesson.is_published ? 'Công khai' : 'Bản nháp'}</p></div>
                    <div className="flex items-center gap-2">
                      <Link title="Xem nội dung bài học" aria-label={`Xem nội dung bài học ${lesson.title}`} to={`/lessons/${lesson.id}`} className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-orange-300 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"><Search className="h-5 w-5" /></Link>
                      <Link title="Quản lý bài đánh giá" aria-label={`Quản lý bài đánh giá của ${lesson.title}`} to={`/teacher/courses/${course.id}/lessons/${lesson.id}/assessment`} className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-orange-300 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"><Pencil className="h-5 w-5" /></Link>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
