import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileUp,
  GraduationCap,
  LayoutDashboard,
  MessageSquare,
  Pencil,
  Users,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { analyticsService } from '../services/analyticsService'
import { courseService } from '../services/courseService'
import { useAuthStore } from '../store/authStore'
import { getUserAvatar } from '../utils/avatar'

const formatPercentage = (value) => `${Number(value || 0).toFixed(0)}%`
const formatScore = (value) => value == null ? 'Chưa có' : Number(value).toFixed(1)
const formatScoreChange = (value) => {
  if (value == null) return 'Chưa có'
  const score = Number(value)
  return `${score > 0 ? '+' : ''}${score.toFixed(1)}`
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
        <Icon className="h-4 w-4 text-orange-700" aria-hidden="true" />
        <span>{label}</span>
      </div>
      <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
    </div>
  )
}

const difficultyLabels = {
  beginner: 'Cơ bản',
  intermediate: 'Trung bình',
  advanced: 'Nâng cao',
}

function CourseThumbnail({ course, className = '' }) {
  return course?.thumbnail ? (
    <img src={course.thumbnail} alt="" className={`object-cover ${className}`} />
  ) : (
    <div className={`flex items-center justify-center bg-orange-500/15 text-orange-300 ${className}`}>
      <BookOpen className="h-6 w-6" aria-hidden="true" />
    </div>
  )
}

function StudentDashboard({ user, report, catalogCourses }) {
  const summary = report.summary
  const enrolledIds = new Set(report.courses.map((course) => course.course_id))
  const catalogById = new Map(catalogCourses.map((course) => [course.id, course]))
  const recommendations = catalogCourses.filter((course) => !enrolledIds.has(course.id)).slice(0, 3)
  const myCourses = report.courses.slice(0, 5)
  const avatar = getUserAvatar(user)

  return (
    <div className="space-y-7">
      <header>
        <h1 className="text-3xl font-bold text-white">Chào mừng trở lại, {user?.full_name || user?.username}</h1>
        <p className="mt-2 text-white/75">Tiếp tục khóa học gần nhất và theo dõi tiến độ của bạn.</p>
        <dl className="mt-5 flex flex-wrap gap-x-6 gap-y-3 border-y border-white/15 py-3 text-sm">
          <div className="flex items-center gap-2">
            <dt className="text-white/65">Đang học</dt>
            <dd className="font-bold text-white">{summary.courses_enrolled}</dd>
          </div>
          <div className="flex items-center gap-2">
            <dt className="text-white/65">Bài đã hoàn thành</dt>
            <dd className="font-bold text-white">{summary.lessons_completed}</dd>
          </div>
          <div className="flex items-center gap-2">
            <dt className="text-white/65">Tiến độ trung bình</dt>
            <dd className="font-bold text-orange-300">{formatPercentage(summary.average_progress_percentage)}</dd>
          </div>
        </dl>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(280px,3fr)]">
        <div className="min-w-0 space-y-8">
          <section aria-labelledby="discover-courses-title">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 id="discover-courses-title" className="text-xl font-bold text-white">Khám phá khóa học</h2>
              <Link to="/courses" className="text-sm font-semibold text-orange-300 hover:text-orange-200">Xem tất cả</Link>
            </div>

            {recommendations.length > 0 ? (
              <div className="flex snap-x gap-4 overflow-x-auto pb-2 md:grid md:grid-cols-3 md:overflow-visible">
                {recommendations.map((course) => (
                  <article key={course.id} className="w-[250px] shrink-0 snap-start overflow-hidden rounded-2xl border border-white/15 bg-slate-950/45 backdrop-blur-md md:w-auto">
                    <CourseThumbnail course={course} className="aspect-[16/9] w-full" />
                    <div className="p-4">
                      <h3 className="line-clamp-2 min-h-10 font-semibold leading-5 text-white">{course.title}</h3>
                      <p className="mt-2 text-xs text-white/60">
                        {course.lessons_count || 0} bài · {difficultyLabels[course.difficulty] || course.difficulty}
                      </p>
                      <Link to={`/courses/${course.id}`} className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-orange-300 hover:text-orange-200">
                        Xem khóa học <ArrowRight className="h-4 w-4" aria-hidden="true" />
                      </Link>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-white/15 bg-slate-950/40 p-5 text-sm text-white/70">
                Bạn đã đăng ký tất cả khóa học đang hiển thị. <Link to="/courses" className="font-semibold text-orange-300">Xem danh sách khóa học</Link>
              </div>
            )}
          </section>

          <section aria-labelledby="my-courses-title">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 id="my-courses-title" className="text-xl font-bold text-white">Khóa học của tôi</h2>
              {report.courses.length > 5 && <Link to="/profile" className="text-sm font-semibold text-orange-300 hover:text-orange-200">Xem tất cả</Link>}
            </div>

            {myCourses.length === 0 ? (
              <div className="rounded-xl border border-white/15 bg-slate-950/40 p-5 text-sm text-white/70">
                Bạn chưa đăng ký khóa học nào. <Link to="/courses" className="font-semibold text-orange-300">Khám phá khóa học</Link>
              </div>
            ) : (
              <div className="divide-y divide-white/10 border-y border-white/15">
                {myCourses.map((course) => {
                  const catalogCourse = catalogById.get(course.course_id)
                  const destination = course.last_accessed_lesson
                    ? `/lessons/${course.last_accessed_lesson.id}`
                    : `/courses/${course.course_id}`
                  return (
                    <article key={course.course_id} className="grid gap-3 py-4 sm:grid-cols-[52px_minmax(0,1fr)_90px_auto] sm:items-center">
                      <CourseThumbnail course={catalogCourse} className="h-12 w-12 rounded-lg" />
                      <div className="min-w-0">
                        <h3 className="truncate font-semibold text-white">{course.course_title}</h3>
                        <p className="mt-1 truncate text-sm text-white/60">
                          {course.completed_at
                            ? 'Đã hoàn thành khóa học'
                            : course.last_accessed_lesson
                              ? `Đang học: ${course.last_accessed_lesson.title}`
                              : 'Chưa bắt đầu'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-orange-300">{formatPercentage(course.progress_percentage)}</p>
                        <p className="mt-0.5 text-xs text-white/50">{course.lessons_completed}/{course.lessons_available} bài</p>
                      </div>
                      <Link to={destination} className="inline-flex min-h-11 items-center justify-center rounded-lg bg-orange-600 px-4 text-sm font-bold text-white hover:bg-orange-700">
                        {course.last_accessed_lesson ? 'Tiếp tục học' : 'Bắt đầu học'}
                      </Link>
                    </article>
                  )
                })}
              </div>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-2xl border border-white/15 bg-slate-950/50 p-5 backdrop-blur-md" aria-labelledby="student-profile-title">
            <div className="flex items-start justify-between gap-3">
              <h2 id="student-profile-title" className="text-lg font-bold text-white">Hồ sơ</h2>
              <Link to="/profile" className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-white/65 hover:bg-white/10 hover:text-white" aria-label="Chỉnh sửa hồ sơ">
                <Pencil className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
            <div className="mt-3 flex items-center gap-4">
              {avatar ? (
                <img src={avatar} alt={user?.full_name || 'Ảnh đại diện'} className="h-16 w-16 rounded-full border-2 border-orange-300/60 object-cover" referrerPolicy="no-referrer" />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-orange-500/20 text-xl font-bold text-orange-200">
                  {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                </div>
              )}
              <div className="min-w-0">
                <p className="truncate font-semibold text-white">{user?.full_name || user?.username}</p>
                <p className="mt-1 text-sm text-white/60">Học viên</p>
              </div>
            </div>
          </section>

          <section aria-labelledby="learning-progress-title">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 id="learning-progress-title" className="text-lg font-bold text-white">Tiến độ học tập</h2>
              {report.courses.length > 4 && <Link to="/profile" className="text-xs font-semibold text-orange-300">Xem toàn bộ</Link>}
            </div>
            <div className="space-y-3">
              {report.courses.slice(0, 4).map((course) => {
                const progress = Math.min(100, Math.max(0, Number(course.progress_percentage || 0)))
                const destination = course.last_accessed_lesson
                  ? `/lessons/${course.last_accessed_lesson.id}`
                  : `/courses/${course.course_id}`
                return (
                  <article key={course.course_id} className="rounded-xl border border-white/15 bg-slate-950/45 p-4 backdrop-blur-md">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="truncate text-sm font-semibold text-white">{course.course_title}</h3>
                        <p className="mt-1 text-xs text-white/55">{course.lessons_completed}/{course.lessons_available} bài hoàn thành</p>
                      </div>
                      <Link to={destination} className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-orange-300 hover:bg-white/10" aria-label={`Mở ${course.course_title}`}>
                        <ArrowRight className="h-4 w-4" aria-hidden="true" />
                      </Link>
                    </div>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10" aria-label={`Tiến độ ${formatPercentage(progress)}`}>
                      <div className="h-full rounded-full bg-orange-500" style={{ width: `${progress}%` }} />
                    </div>
                    <p className="mt-2 text-xs text-white/60">
                      {progress > 0
                        ? `${formatPercentage(progress)} · ${course.last_accessed_lesson?.title || 'Đang học'}`
                        : 'Chưa bắt đầu · Bắt đầu bài đầu tiên'}
                    </p>
                  </article>
                )
              })}
              {report.courses.length === 0 && <p className="rounded-xl border border-white/15 p-4 text-sm text-white/65">Chưa có khóa học để theo dõi.</p>}
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}

function ProgressBar({ value, label }) {
  const percentage = Math.min(100, Math.max(0, Number(value || 0)))
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between gap-3 text-xs text-white/65">
        <span>{label}</span>
        <span className="font-semibold text-white">{formatPercentage(percentage)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-orange-500" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, progress, emphasized = false }) {
  const percentage = progress == null ? null : Math.min(100, Math.max(0, Number(progress)))
  return (
    <article className={`flex min-h-24 items-center justify-between gap-4 rounded-2xl border p-4 backdrop-blur-md ${
      emphasized
        ? 'border-orange-300/35 bg-orange-950/40'
        : 'border-white/20 bg-[rgba(72,45,65,0.68)]'
    }`}>
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-xs font-medium text-white/75">
          <Icon className="h-4 w-4 shrink-0 text-orange-300" aria-hidden="true" />
          <span className="truncate">{label}</span>
        </div>
        <p className="mt-2 text-2xl font-bold text-white">{value}</p>
      </div>
      <div
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
        style={{
          background: percentage == null
            ? 'conic-gradient(rgba(255,255,255,0.2) 0 22%, rgba(255,255,255,0.08) 22% 100%)'
            : `conic-gradient(rgb(249 115 22) 0 ${percentage}%, rgba(255,255,255,0.1) ${percentage}% 100%)`,
        }}
        aria-label={percentage == null ? 'Không có mẫu số phù hợp' : formatPercentage(percentage)}
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#2d1727] text-[10px] font-bold text-white/80">
          {percentage == null ? '—' : formatPercentage(percentage)}
        </span>
      </div>
    </article>
  )
}

function MiniCalendar() {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = [...Array(firstWeekday).fill(null), ...Array.from({ length: daysInMonth }, (_, index) => index + 1)]
  const monthLabel = new Intl.DateTimeFormat('vi-VN', { month: 'long', year: 'numeric' }).format(today)

  return (
    <section className="rounded-2xl border border-white/20 bg-[rgba(58,35,52,0.68)] p-4 backdrop-blur-md" aria-labelledby="calendar-title">
      <div className="flex items-center justify-between gap-3">
        <h2 id="calendar-title" className="flex items-center gap-2 text-lg font-bold">
          <CalendarDays className="h-5 w-5 text-orange-300" aria-hidden="true" />
          Lịch
        </h2>
        <span className="text-xs font-medium capitalize text-white/60">{monthLabel}</span>
      </div>
      <div className="mt-4 grid grid-cols-7 gap-1 text-center text-[11px]">
        {['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((day) => (
          <span key={day} className="py-1 text-white/45">{day}</span>
        ))}
        {cells.map((day, index) => {
          const isToday = day === today.getDate()
          return (
            <span
              key={`${day || 'empty'}-${index}`}
              className={`flex aspect-square items-center justify-center rounded-md ${
                isToday ? 'bg-orange-600 font-bold text-white' : day ? 'text-white/70' : ''
              }`}
            >
              {day}
            </span>
          )
        })}
      </div>
      <p className="mt-3 border-t border-white/10 pt-3 text-xs leading-5 text-white/50">
        Chưa có dữ liệu deadline để đánh dấu trên lịch.
      </p>
    </section>
  )
}

function TeacherDashboard({
  user,
  report,
  selectedCourseReport,
  courseReports,
  onSelectCourse,
}) {
  const courses = report.courses || []
  const featuredCourses = courses.slice(0, 3)
  const selectedCourseId = selectedCourseReport?.course?.course_id || courses[0]?.course_id
  const learners = selectedCourseReport?.learners || []
  const featuredLearners = [...learners]
    .filter((learner) => Number(learner.progress_percentage) > 0)
    .sort((first, second) => Number(second.progress_percentage) - Number(first.progress_percentage))
    .slice(0, 5)
  const completeCourseReports = courses
    .map((course) => courseReports[course.course_id])
    .filter((courseReport) => (
      courseReport
      && courseReport.pagination?.count === courseReport.learners.length
    ))
  const allRostersLoaded = courses.length > 0 && completeCourseReports.length === courses.length
  const assessedLearnerIds = allRostersLoaded
    ? new Set(
      completeCourseReports.flatMap((courseReport) => (
        courseReport.learners
          .filter((learner) => learner.assessments_attempted > 0)
          .map((learner) => learner.user_id)
      )),
    )
    : null
  const overallAssessmentRate = assessedLearnerIds && report.summary.learners
    ? (assessedLearnerIds.size / report.summary.learners) * 100
    : null
  const quickLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, active: true },
    { to: '/teacher/upload', label: 'Tải học liệu', icon: FileUp },
    { to: '/teacher/courses', label: 'Quản lý khóa', icon: BookOpen },
    { to: '/courses', label: 'Khóa học', icon: GraduationCap },
    { to: '/forum', label: 'Diễn đàn', icon: MessageSquare },
  ]

  const getAssessmentRate = (courseId) => {
    const roster = courseReports[courseId]
    if (!roster?.learners?.length || roster.pagination?.count !== roster.learners.length) return null
    return (
      roster.learners.filter((learner) => learner.assessments_attempted > 0).length
      / roster.learners.length
    ) * 100
  }

  return (
    <div className="space-y-7 text-white">
      <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,7fr)_minmax(280px,3fr)]">
        <div className="min-w-0 space-y-8">
          <header className="flex min-h-40 flex-col justify-between gap-5 rounded-2xl border border-white/20 bg-[rgba(58,35,52,0.68)] p-6 backdrop-blur-md sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">Teacher Dashboard</p>
              <h1 className="mt-2 text-2xl font-bold sm:text-3xl">Chào mừng trở lại, {user?.full_name || user?.username}</h1>
              <p className="mt-2 max-w-xl text-sm leading-6 text-white/75 sm:text-base">
                Theo dõi khóa học, học viên và kết quả đánh giá trong cùng một không gian.
              </p>
            </div>
            <Button asChild className="min-h-11 shrink-0 bg-orange-600 px-5 text-white hover:bg-orange-700">
              <Link to="/teacher/upload">Tải học liệu</Link>
            </Button>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Thống kê giảng dạy">
            <MetricCard icon={BookOpen} label="Khóa học phụ trách" value={report.summary.courses} />
            <MetricCard icon={Users} label="Tổng học viên" value={report.summary.learners} />
            <MetricCard
              icon={ClipboardCheck}
              label="Học viên đã làm bài"
              value={assessedLearnerIds ? assessedLearnerIds.size : '—'}
              progress={overallAssessmentRate}
              emphasized
            />
          </section>

          <section aria-labelledby="quick-access-title">
            <h2 id="quick-access-title" className="mb-3 text-sm font-semibold uppercase tracking-[0.16em] text-white/75">Truy cập nhanh</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {quickLinks.map(({ to, label, icon: Icon, active }) => (
                <Link
                  key={to}
                  to={to}
                  aria-current={active ? 'page' : undefined}
                  className={`group flex min-h-24 flex-col items-center justify-center gap-2 rounded-xl border p-3 text-center transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 ${
                    active
                      ? 'border-orange-300/45 bg-orange-500/15'
                      : 'border-white/20 bg-[rgba(72,45,65,0.58)] hover:border-orange-300/40 hover:bg-white/15'
                  }`}
                >
                  <Icon className="h-5 w-5 text-orange-300 group-hover:text-orange-200" aria-hidden="true" />
                  <span className="text-xs font-semibold text-white/80 group-hover:text-white">{label}</span>
                </Link>
              ))}
            </div>
          </section>

          <section aria-labelledby="teacher-courses-title">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">Ưu tiên</p>
                <h2 id="teacher-courses-title" className="mt-1 text-xl font-bold">Khóa học đang phụ trách</h2>
              </div>
              <Link to="/teacher/courses" className="max-w-[160px] text-right text-sm font-semibold text-orange-300 hover:text-orange-200 sm:max-w-none">
                Xem chi tiết toàn bộ
              </Link>
            </div>

            {featuredCourses.length === 0 ? (
              <p className="rounded-xl border border-white/15 bg-slate-950/40 p-5 text-sm text-white/70">
                Chưa có khóa học thuộc phạm vi của bạn.
              </p>
            ) : (
              <div className={`flex snap-x gap-4 overflow-x-auto pb-2 md:grid md:overflow-visible ${
                featuredCourses.length === 1
                  ? 'md:grid-cols-2'
                  : featuredCourses.length === 2
                    ? 'md:grid-cols-2'
                    : 'md:grid-cols-2 xl:grid-cols-3'
              }`}>
                {featuredCourses.map((course) => {
                  const courseAssessmentRate = getAssessmentRate(course.course_id)
                  return (
                    <article key={course.course_id} className="w-[270px] shrink-0 snap-start rounded-2xl border border-white/20 bg-[rgba(58,35,52,0.64)] p-4 backdrop-blur-md md:w-auto">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/15 text-orange-300">
                          <BookOpen className="h-5 w-5" aria-hidden="true" />
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${course.is_published ? 'bg-emerald-400/15 text-emerald-200' : 'bg-amber-400/15 text-amber-200'}`}>
                          {course.is_published ? 'Đã xuất bản' : 'Bản nháp'}
                        </span>
                      </div>
                      <h3 className="mt-4 line-clamp-2 min-h-12 font-semibold">{course.course_title}</h3>
                      <p className="mt-1 text-sm text-white/65">{course.learner_count} học viên</p>
                      <div className="mt-4 space-y-3">
                        {courseAssessmentRate == null ? (
                          <div className="flex items-center justify-between gap-3 text-xs text-white/65">
                            <span>Đã làm bài kiểm tra</span>
                            <span className="font-semibold text-white">—</span>
                          </div>
                        ) : (
                          <ProgressBar value={courseAssessmentRate} label="Đã làm bài kiểm tra" />
                        )}
                        {course.learner_count > 0 ? (
                          <ProgressBar value={course.average_progress_percentage} label="Tiến độ trung bình" />
                        ) : (
                          <p className="text-xs text-white/55">Chưa có học viên tham gia.</p>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => onSelectCourse(course.course_id)}
                        className="mt-3 min-h-11 w-full justify-between px-2 text-orange-300 hover:bg-white/10 hover:text-orange-200"
                      >
                        Xem học viên <ArrowRight className="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Link
                        to={`/teacher/courses?course=${course.course_id}`}
                        className="mt-1 inline-flex min-h-11 w-full items-center justify-center rounded-lg text-sm font-semibold text-white/65 hover:bg-white/10 hover:text-white"
                      >
                        Quản lý khóa học
                      </Link>
                    </article>
                  )
                })}
              </div>
            )}
          </section>

        </div>

        <aside className="space-y-6">
          <MiniCalendar />

          <section aria-labelledby="featured-learners-title">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 id="featured-learners-title" className="text-lg font-bold">Sinh viên tiêu biểu</h2>
              {featuredLearners.length > 0 && (
                <span className="text-xs font-medium text-white/55">Theo tiến độ</span>
              )}
            </div>
            {featuredLearners.length === 0 ? (
              <p className="rounded-xl border border-white/20 bg-white/5 p-3 text-sm text-white/70">
                Hiện chưa có sinh viên tiêu biểu.
              </p>
            ) : (
              <div className="overflow-hidden rounded-xl border border-white/20 bg-[rgba(58,35,52,0.62)] backdrop-blur-md">
                {featuredLearners.map((learner, index) => (
                  <Link
                    key={learner.user_id}
                    to={`/users/${learner.user_id}`}
                    className="flex min-h-16 items-center gap-3 border-b border-white/10 px-3 py-2.5 last:border-0 hover:bg-white/10"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-sm font-bold text-orange-200">
                      {learner.full_name?.charAt(0) || 'H'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{learner.full_name}</p>
                      <p className="mt-0.5 truncate text-xs text-white/60">
                        {selectedCourseReport?.course?.course_title}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-sm font-bold text-orange-300">{formatPercentage(learner.progress_percentage)}</p>
                      {index === 0 && <p className="text-[10px] font-medium text-emerald-200">Tiến độ tốt</p>}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuthStore()
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [report, setReport] = useState(null)
  const [selectedCourseReport, setSelectedCourseReport] = useState(null)
  const [objectiveReport, setObjectiveReport] = useState(null)
  const [reinforcementOutcomes, setReinforcementOutcomes] = useState(null)
  const [loading, setLoading] = useState(true)
  const [courseLoading, setCourseLoading] = useState(false)
  const [exportingCourseId, setExportingCourseId] = useState(null)
  const [catalogCourses, setCatalogCourses] = useState([])
  const [courseReports, setCourseReports] = useState({})
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const loadReport = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await analyticsService.getProgressReport()
        if (!cancelled) setReport(data)
      } catch {
        if (!cancelled) setError('Không thể tải báo cáo tiến độ. Vui lòng thử lại.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadReport()
    return () => {
      cancelled = true
    }
  }, [user?.role])

  useEffect(() => {
    if (isTeacher) {
      setCatalogCourses([])
      return
    }

    let active = true
    courseService.getCourses()
      .then((courses) => {
        if (active) setCatalogCourses(courses)
      })
      .catch(() => {
        if (active) setCatalogCourses([])
      })
    return () => {
      active = false
    }
  }, [isTeacher])

  const loadCourseLearners = async (courseId) => {
    setCourseLoading(true)
    setError('')
    setSelectedCourseReport(null)
    setObjectiveReport(null)
    setReinforcementOutcomes(null)
    try {
      const [courseData, objectiveData, outcomeData] = await Promise.all([
        analyticsService.getProgressReport({ course_id: courseId }),
        analyticsService.getObjectiveReport(courseId),
        analyticsService.getReinforcementOutcomes(courseId),
      ])
      setSelectedCourseReport(courseData)
      setObjectiveReport(objectiveData)
      setReinforcementOutcomes(outcomeData)
    } catch {
      setError('Không thể tải tiến độ học viên của khóa học này.')
    } finally {
      setCourseLoading(false)
    }
  }

  useEffect(() => {
    if (!isTeacher || report?.scope !== 'teaching' || report.courses.length === 0) return

    let active = true
    const featuredIds = report.courses.slice(0, 3).map((course) => course.course_id)
    Promise.all(featuredIds.map((courseId) => analyticsService.getProgressReport({ course_id: courseId })))
      .then((courseData) => {
        if (!active) return
        setCourseReports(Object.fromEntries(courseData.map((item) => [item.course.course_id, item])))
        setSelectedCourseReport(courseData[0])
      })
      .catch(() => {
        if (active) setCourseReports({})
      })

    return () => {
      active = false
    }
  }, [isTeacher, report])

  const exportCourseProgress = async (course) => {
    setExportingCourseId(course.course_id)
    setError('')
    try {
      const blob = await analyticsService.exportCourseProgress(course.course_id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `course-${course.course_id}-progress.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      setError('Không thể xuất báo cáo CSV của khóa học này.')
    } finally {
      setExportingCourseId(null)
    }
  }

  const learnerSummary = report?.scope === 'learner' ? report.summary : null
  const teacherSummary = report?.scope === 'teaching' ? report.summary : null
  const showLegacyTeacherDashboard = false

  return (
    <div className="space-y-8">
      {isTeacher && showLegacyTeacherDashboard && <header>
        <h1 className="text-3xl font-bold text-white">Chào mừng, {user?.full_name}</h1>
        <p className="mt-2 text-white/75">
          {isTeacher
            ? 'Theo dõi tiến độ từ dữ liệu hoàn thành và bài đánh giá đã ghi nhận.'
            : 'Tiến độ và mức độ nắm vững kiến thức của bạn được tính độc lập.'}
        </p>
      </header>}

      {loading && (
        <div className="rounded-xl border border-white/20 bg-white p-5 text-slate-600" role="status">
          Đang tổng hợp tiến độ...
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800" role="alert">
          <AlertCircle className="h-5 w-5" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {!loading && learnerSummary && (
        <StudentDashboard user={user} report={report} catalogCourses={catalogCourses} />
      )}

      {!loading && teacherSummary && (
        <TeacherDashboard
          user={user}
          report={report}
          selectedCourseReport={selectedCourseReport}
          courseReports={courseReports}
          onSelectCourse={loadCourseLearners}
        />
      )}

      {!loading && teacherSummary && showLegacyTeacherDashboard && (
        <>
          <section className="grid gap-4 sm:grid-cols-3" aria-label="Tổng quan giảng dạy">
            <StatCard icon={BookOpen} label="Khóa học phụ trách" value={teacherSummary.courses} />
            <StatCard icon={Users} label="Học viên duy nhất" value={teacherSummary.learners} />
            <StatCard icon={CheckCircle2} label="Lượt hoàn thành khóa" value={teacherSummary.course_completions} />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="teaching-progress-title">
            <h2 id="teaching-progress-title" className="text-xl font-semibold text-slate-950">Tiến độ các khóa phụ trách</h2>
            {report.courses.length === 0 ? (
              <p className="mt-3 text-slate-600">Chưa có khóa học thuộc phạm vi của bạn.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[640px] text-left text-sm">
                  <thead className="border-b border-slate-200 text-slate-600">
                    <tr>
                      <th className="px-3 py-2 font-medium">Khóa học</th>
                      <th className="px-3 py-2 font-medium">Học viên</th>
                      <th className="px-3 py-2 font-medium">Tiến độ TB</th>
                      <th className="px-3 py-2 font-medium">Nắm vững TB</th>
                      <th className="px-3 py-2"><span className="sr-only">Thao tác</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.courses.map((course) => (
                      <tr key={course.course_id} className="border-b border-slate-100 last:border-0">
                        <td className="px-3 py-3 font-medium text-slate-950">{course.course_title}</td>
                        <td className="px-3 py-3 text-slate-700">{course.learner_count}</td>
                        <td className="px-3 py-3 text-slate-700">{formatPercentage(course.average_progress_percentage)}</td>
                        <td className="px-3 py-3 text-slate-700">{formatPercentage(course.average_mastery_percentage)}</td>
                        <td className="px-3 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              onClick={() => exportCourseProgress(course)}
                              disabled={exportingCourseId !== null}
                              variant="outline"
                              aria-label={`Xuất CSV tiến độ khóa ${course.course_title}`}
                            >
                              <Download className="mr-1 h-4 w-4" aria-hidden="true" />
                              {exportingCourseId === course.course_id ? 'Đang xuất...' : 'Xuất CSV'}
                            </Button>
                            <Button
                              onClick={() => loadCourseLearners(course.course_id)}
                              disabled={courseLoading}
                              className="bg-orange-700 text-white hover:bg-orange-800"
                            >
                              Xem học viên
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {selectedCourseReport && (
            <section className="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="learner-list-title">
              <div className="flex items-center justify-between gap-4">
                <h2 id="learner-list-title" className="text-xl font-semibold text-slate-950">
                  Học viên · {selectedCourseReport.course.course_title}
                </h2>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedCourseReport(null)
                    setObjectiveReport(null)
                    setReinforcementOutcomes(null)
                  }}
                  className="text-sm text-slate-600 hover:text-slate-950"
                >
                  Đóng
                </button>
              </div>
              {selectedCourseReport.learners.length === 0 ? (
                <p className="mt-3 text-slate-600">Khóa học chưa có học viên.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {selectedCourseReport.learners.map((learner) => (
                    <article key={learner.user_id} className="rounded-lg border border-slate-200 p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <h3 className="font-medium text-slate-950">{learner.full_name}</h3>
                        <p className="text-sm text-slate-600">
                          Tiến độ {formatPercentage(learner.progress_percentage)} · Nắm vững {formatPercentage(learner.mastery_percentage)} · Đạt {learner.assessments_passed}/{learner.assessments_attempted} đánh giá
                        </p>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              <div className="mt-6 border-t border-slate-200 pt-5">
                <h3 className="font-semibold text-slate-950">Mục tiêu cần củng cố</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Tổng hợp từ lần làm mới nhất của mỗi học viên trên phiên bản assessment hiện hành.
                </p>
                {objectiveReport?.objectives.length ? (
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {objectiveReport.objectives.map((objective) => (
                      <article
                        key={objective.learning_objective}
                        className="rounded-lg border border-slate-200 p-4"
                      >
                        <h4 className="font-medium text-slate-950">
                          {objective.learning_objective}
                        </h4>
                        <p className="mt-2 text-sm text-slate-600">
                          {objective.learners_needing_review}/{objective.learner_count} học viên cần ôn · Đúng {formatPercentage(objective.correct_rate_percentage)} trên {objective.answer_count} câu trả lời
                        </p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">
                    Chưa có câu trả lời assessment hiện hành để tổng hợp theo mục tiêu.
                  </p>
                )}
                {objectiveReport?.pagination.truncated && (
                  <p className="mt-3 text-sm text-amber-800">
                    Danh sách đang hiển thị {objectiveReport.pagination.limit}/{objectiveReport.pagination.count} mục tiêu.
                  </p>
                )}
              </div>

              <div className="mt-6 border-t border-slate-200 pt-5">
                <h3 className="font-semibold text-slate-950">Kết quả sau củng cố RAG</h3>
                <p className="mt-1 text-sm text-slate-600">
                  So sánh quan sát trước/sau, không chứng minh củng cố là nguyên nhân làm thay đổi điểm.
                </p>
                {reinforcementOutcomes?.summary.total_usable_exposures ? (
                  <>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="rounded-lg border border-slate-200 p-4">
                        <span className="text-sm text-slate-500">Exposure có bằng chứng</span>
                        <strong className="mt-1 block text-xl text-slate-950">
                          {reinforcementOutcomes.summary.total_usable_exposures}
                        </strong>
                      </div>
                      <div className="rounded-lg border border-slate-200 p-4">
                        <span className="text-sm text-slate-500">Có attempt tiếp theo</span>
                        <strong className="mt-1 block text-xl text-slate-950">
                          {reinforcementOutcomes.summary.paired_attempts}
                        </strong>
                      </div>
                      <div className="rounded-lg border border-slate-200 p-4">
                        <span className="text-sm text-slate-500">Điểm TB trước → sau</span>
                        <strong className="mt-1 block text-xl text-slate-950">
                          {formatScore(reinforcementOutcomes.summary.average_before_score)} → {formatScore(reinforcementOutcomes.summary.average_after_score)}
                        </strong>
                      </div>
                      <div className="rounded-lg border border-slate-200 p-4">
                        <span className="text-sm text-slate-500">Thay đổi TB</span>
                        <strong className="mt-1 block text-xl text-slate-950">
                          {formatScoreChange(reinforcementOutcomes.summary.average_score_change)} điểm
                        </strong>
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">
                      Chuyển sang đạt: {reinforcementOutcomes.summary.pass_conversion_count} · Chưa có attempt tiếp theo: {reinforcementOutcomes.summary.pending_followup}
                    </p>
                    {reinforcementOutcomes.truncated && (
                      <p className="mt-2 text-sm text-amber-800">
                        Báo cáo bị giới hạn; không dùng số liệu này làm baseline đầy đủ.
                      </p>
                    )}
                  </>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">
                    Chưa có phiên củng cố chứa bằng chứng RAG để ghép với attempt tiếp theo.
                  </p>
                )}
              </div>
            </section>
          )}
        </>
      )}

      {isTeacher && showLegacyTeacherDashboard && <section className="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="quick-actions-title">
        <h2 id="quick-actions-title" className="text-xl font-semibold text-slate-950">
          {isTeacher ? 'Thao tác giảng viên' : 'Tiếp tục học tập'}
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {isTeacher && (
            <Link to="/teacher/upload" className="rounded-lg border border-slate-200 p-4 hover:border-orange-400">
              <h3 className="font-semibold text-orange-700">Tải bài giảng PDF</h3>
              <p className="mt-1 text-sm text-slate-600">Trích xuất và lập chỉ mục tài liệu cho AI Tutor.</p>
            </Link>
          )}
          <Link to="/forum" className="rounded-lg border border-slate-200 p-4 hover:border-orange-400">
            <h3 className="font-semibold text-orange-700">Diễn đàn</h3>
            <p className="mt-1 text-sm text-slate-600">Trao đổi với giảng viên và cộng đồng.</p>
          </Link>
        </div>
      </section>}
    </div>
  )
}
