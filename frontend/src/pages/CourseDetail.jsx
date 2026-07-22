import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  BookOpen,
  Check,
  ChevronDown,
  Clock3,
  GraduationCap,
  ListChecks,
  LockKeyhole,
  Star,
  UnlockKeyhole,
  Users,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'

const difficultyLabels = {
  beginner: 'Cơ bản',
  intermediate: 'Trung bình',
  advanced: 'Nâng cao',
}

function toShortList(value, limit) {
  if (!value) return []

  return value
    .split(/\r?\n|;|•/)
    .map((item) => item.replace(/^[-–—*\d.)\s]+/, '').trim())
    .filter(Boolean)
    .slice(0, limit)
}

function formatDuration(minutes, fallbackHours = 0) {
  if (minutes > 0) {
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    if (!hours) return `${remainingMinutes} phút`
    return remainingMinutes ? `${hours} giờ ${remainingMinutes} phút` : `${hours} giờ`
  }

  return fallbackHours > 0 ? `${fallbackHours} giờ` : 'Linh hoạt'
}

export default function CourseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [enrolling, setEnrolling] = useState(false)
  const [isEnrolled, setIsEnrolled] = useState(false)
  const [enrollment, setEnrollment] = useState(null)
  const [curriculumOpen, setCurriculumOpen] = useState(true)

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        const response = await api.get(`/courses/${id}/`)
        setCourse(response.data)

        if (isAuthenticated) {
          try {
            const progressResponse = await api.get(`/courses/${id}/progress/`)
            setIsEnrolled(true)
            setEnrollment(progressResponse.data)
          } catch {
            setIsEnrolled(false)
            setEnrollment(null)
          }
        }
      } catch (error) {
        console.error('Failed to fetch course:', error)
        toast.error('Không thể tải thông tin khóa học')
      } finally {
        setLoading(false)
      }
    }

    fetchCourse()
  }, [id, isAuthenticated])

  const lessons = course?.lessons || []
  const totalMinutes = useMemo(
    () => lessons.reduce((total, lesson) => total + Number(lesson.duration_minutes || 0), 0),
    [lessons],
  )
  const durationLabel = formatDuration(totalMinutes, Number(course?.duration_hours || 0))
  const objectives = toShortList(course?.objectives, 6)
  const prerequisites = toShortList(course?.prerequisites, 5)

  const handleEnroll = async () => {
    if (!isAuthenticated) {
      toast('Vui lòng đăng nhập để bắt đầu học')
      navigate('/login')
      return
    }

    setEnrolling(true)
    try {
      await api.post(`/courses/${id}/enroll/`)
      setIsEnrolled(true)
      toast.success('Đăng ký khóa học thành công!')
      if (lessons.length > 0) navigate(`/lessons/${lessons[0].id}`)
    } catch (error) {
      toast.error(error.response?.data?.message || 'Đăng ký thất bại')
    } finally {
      setEnrolling(false)
    }
  }

  const handleStartLearning = () => {
    if (!isAuthenticated) {
      toast('Vui lòng đăng nhập để tiếp tục học')
      navigate('/login')
      return
    }

    if (lessons.length > 0) {
      navigate(`/lessons/${enrollment?.last_accessed_lesson || lessons[0].id}`)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center" role="status">
        <span className="h-11 w-11 animate-spin rounded-full border-2 border-white/30 border-b-orange-400" />
        <span className="sr-only">Đang tải khóa học</span>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4">
        <div className="text-center text-white">
          <h1 className="text-2xl font-bold">Không tìm thấy khóa học</h1>
          <Button onClick={() => navigate('/courses')} className="mt-5 bg-orange-600 text-white hover:bg-orange-700">
            Xem các khóa học
          </Button>
        </div>
      </div>
    )
  }

  const actionButton = isEnrolled ? (
    <Button
      onClick={handleStartLearning}
      disabled={lessons.length === 0}
      className="min-h-12 w-full bg-orange-600 font-bold text-white hover:bg-orange-700 focus-visible:ring-orange-400"
    >
      <BookOpen className="mr-2 h-5 w-5" aria-hidden="true" />
      Tiếp tục học
    </Button>
  ) : (
    <Button
      onClick={handleEnroll}
      disabled={enrolling || lessons.length === 0}
      className="min-h-12 w-full bg-orange-600 font-bold text-white hover:bg-orange-700 focus-visible:ring-orange-400"
    >
      <GraduationCap className="mr-2 h-5 w-5" aria-hidden="true" />
      {enrolling ? 'Đang xử lý...' : 'Đăng ký học'}
    </Button>
  )

  return (
    <div className="min-h-[calc(100vh-3.5rem)] px-4 pb-14 pt-8 text-white sm:px-6 sm:pt-10 lg:px-8 lg:pb-20">
      <div className="mx-auto max-w-7xl">
        <div className="grid items-start gap-10 lg:grid-cols-[minmax(0,1fr)_360px] xl:gap-14">
          <main className="min-w-0">
            <header className="border-b border-white/20 pb-8">
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-orange-300">
                {difficultyLabels[course.difficulty] || course.difficulty}
              </p>
              <h1 className="mt-3 max-w-4xl text-3xl font-bold leading-tight sm:text-4xl lg:text-5xl">
                {course.title}
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-slate-200 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2] overflow-hidden">
                {course.description}
              </p>

              <dl className="mt-6 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-200">
                {Number(course.average_rating) > 0 && (
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 fill-orange-400 text-orange-400" aria-hidden="true" />
                    <dt className="sr-only">Đánh giá</dt>
                    <dd>{Number(course.average_rating).toFixed(1)} / 5</dd>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-orange-300" aria-hidden="true" />
                  <dt className="sr-only">Học viên</dt>
                  <dd>{course.total_students || 0} học viên</dd>
                </div>
                <div className="flex items-center gap-2">
                  <ListChecks className="h-4 w-4 text-orange-300" aria-hidden="true" />
                  <dt className="sr-only">Số bài học</dt>
                  <dd>{lessons.length} bài học</dd>
                </div>
                <div className="flex items-center gap-2">
                  <Clock3 className="h-4 w-4 text-orange-300" aria-hidden="true" />
                  <dt className="sr-only">Thời lượng</dt>
                  <dd>{durationLabel}</dd>
                </div>
              </dl>
            </header>

            <div className="mt-6 lg:hidden">
              {actionButton}
              {!isAuthenticated && <p className="mt-2 text-center text-xs text-slate-300">Đăng nhập để bắt đầu học.</p>}
            </div>

            {objectives.length > 0 && (
              <section className="border-b border-white/20 py-9" aria-labelledby="objectives-title">
                <h2 id="objectives-title" className="text-2xl font-bold">Bạn sẽ học được gì?</h2>
                <ul className="mt-5 grid gap-x-8 gap-y-4 sm:grid-cols-2">
                  {objectives.map((objective) => (
                    <li key={objective} className="flex items-start gap-3 text-sm leading-6 text-slate-200">
                      <Check className="mt-1 h-4 w-4 shrink-0 text-orange-300" aria-hidden="true" />
                      <span>{objective}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section className="border-b border-white/20 py-9" aria-labelledby="curriculum-title">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 id="curriculum-title" className="text-2xl font-bold">Nội dung khóa học</h2>
                  <p className="mt-2 text-sm text-slate-300">{lessons.length} bài học · {durationLabel}</p>
                </div>
                {lessons.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setCurriculumOpen((open) => !open)}
                    className="min-h-11 rounded-md px-2 text-sm font-semibold text-orange-300 hover:text-orange-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
                    aria-expanded={curriculumOpen}
                    aria-controls="course-lessons"
                  >
                    {curriculumOpen ? 'Thu gọn' : 'Mở rộng tất cả'}
                  </button>
                )}
              </div>

              {lessons.length > 0 ? (
                <div className="mt-6 border-y border-white/20">
                  <button
                    type="button"
                    onClick={() => setCurriculumOpen((open) => !open)}
                    className="flex min-h-14 w-full items-center justify-between gap-4 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-400"
                    aria-expanded={curriculumOpen}
                    aria-controls="course-lessons"
                  >
                    <span>
                      <span className="block font-semibold text-white">Danh sách bài học</span>
                      <span className="mt-0.5 block text-xs text-slate-300">{lessons.length} bài</span>
                    </span>
                    <ChevronDown className={`h-5 w-5 shrink-0 text-orange-300 transition-transform ${curriculumOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
                  </button>

                  {curriculumOpen && (
                    <ol id="course-lessons" className="border-t border-white/15">
                      {lessons.map((lesson, index) => (
                        <li key={lesson.id} className="border-b border-white/10 last:border-0">
                          <button
                            type="button"
                            disabled={!isEnrolled}
                            onClick={() => navigate(`/lessons/${lesson.id}`)}
                            className="flex min-h-14 w-full items-center gap-3 py-3 text-left text-sm transition-colors enabled:hover:text-orange-200 enabled:focus-visible:outline-none enabled:focus-visible:ring-2 enabled:focus-visible:ring-inset enabled:focus-visible:ring-orange-400 disabled:cursor-not-allowed"
                          >
                            <span className="w-7 shrink-0 text-slate-400">{String(index + 1).padStart(2, '0')}</span>
                            <span className="min-w-0 flex-1 font-medium text-slate-100">{lesson.title}</span>
                            {lesson.duration_minutes > 0 && <span className="shrink-0 text-xs text-slate-400">{lesson.duration_minutes} phút</span>}
                            {isEnrolled
                              ? <UnlockKeyhole className="h-4 w-4 shrink-0 text-emerald-300" aria-label="Có thể truy cập" />
                              : <LockKeyhole className="h-4 w-4 shrink-0 text-slate-400" aria-label="Cần đăng ký" />}
                          </button>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>
              ) : (
                <p className="mt-6 border-y border-white/20 py-8 text-sm text-slate-300">Nội dung khóa học đang được cập nhật.</p>
              )}
            </section>

            {prerequisites.length > 0 && (
              <section className="py-9" aria-labelledby="requirements-title">
                <h2 id="requirements-title" className="text-2xl font-bold">Yêu cầu</h2>
                <ul className="mt-5 space-y-3">
                  {prerequisites.map((requirement) => (
                    <li key={requirement} className="flex items-start gap-3 text-sm leading-6 text-slate-200">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-orange-400" aria-hidden="true" />
                      <span>{requirement}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </main>

          <aside className="sticky top-24 hidden overflow-hidden rounded-2xl border border-white/20 bg-slate-950/55 shadow-xl backdrop-blur-md lg:block" aria-label="Đăng ký khóa học">
            <div className="aspect-video overflow-hidden bg-slate-900/70">
              {course.thumbnail ? (
                <img src={course.thumbnail} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <BookOpen className="h-14 w-14 text-orange-300" aria-hidden="true" />
                </div>
              )}
            </div>

            <div className="p-6">
              <p className="text-2xl font-bold">Miễn phí</p>
              <div className="mt-5">{actionButton}</div>
              {!isAuthenticated && <p className="mt-2 text-center text-xs text-slate-300">Đăng nhập để bắt đầu học.</p>}

              <dl className="mt-6 space-y-4 border-t border-white/20 pt-5 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-300">Trình độ</dt>
                  <dd className="font-medium">{difficultyLabels[course.difficulty] || course.difficulty}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-300">Bài học</dt>
                  <dd className="font-medium">{lessons.length}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-300">Thời lượng</dt>
                  <dd className="font-medium">{durationLabel}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-300">Hình thức</dt>
                  <dd className="font-medium">Học trực tuyến</dd>
                </div>
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
