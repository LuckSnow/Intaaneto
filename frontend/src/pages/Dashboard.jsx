import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, BookOpen, CheckCircle2, Download, Target, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { analyticsService } from '../services/analyticsService'
import { useAuthStore } from '../store/authStore'

const formatPercentage = (value) => `${Number(value || 0).toFixed(0)}%`

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

export default function Dashboard() {
  const { user } = useAuthStore()
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [report, setReport] = useState(null)
  const [selectedCourseReport, setSelectedCourseReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [courseLoading, setCourseLoading] = useState(false)
  const [exportingCourseId, setExportingCourseId] = useState(null)
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

  const loadCourseLearners = async (courseId) => {
    setCourseLoading(true)
    setError('')
    try {
      const data = await analyticsService.getProgressReport({ course_id: courseId })
      setSelectedCourseReport(data)
    } catch {
      setError('Không thể tải tiến độ học viên của khóa học này.')
    } finally {
      setCourseLoading(false)
    }
  }

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

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-white">Chào mừng, {user?.full_name}</h1>
        <p className="mt-2 text-white/75">
          {isTeacher
            ? 'Theo dõi tiến độ từ dữ liệu hoàn thành và bài đánh giá đã ghi nhận.'
            : 'Tiến độ và mức độ nắm vững kiến thức của bạn được tính độc lập.'}
        </p>
      </header>

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
        <>
          <section aria-labelledby="learner-summary-title">
            <h2 id="learner-summary-title" className="sr-only">Tổng quan học tập</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard icon={BookOpen} label="Khóa học đã đăng ký" value={learnerSummary.courses_enrolled} />
              <StatCard icon={CheckCircle2} label="Bài học hoàn thành" value={learnerSummary.lessons_completed} />
              <StatCard icon={Target} label="Tiến độ trung bình" value={formatPercentage(learnerSummary.average_progress_percentage)} />
              <StatCard icon={Target} label="Mức độ nắm vững" value={formatPercentage(learnerSummary.average_mastery_percentage)} />
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="course-progress-title">
            <h2 id="course-progress-title" className="text-xl font-semibold text-slate-950">Tiến độ theo khóa học</h2>
            {report.courses.length === 0 ? (
              <p className="mt-3 text-slate-600">Bạn chưa đăng ký khóa học nào.</p>
            ) : (
              <div className="mt-4 space-y-3">
                {report.courses.map((course) => (
                  <article key={course.course_id} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <h3 className="font-semibold text-slate-950">{course.course_title}</h3>
                        <p className="mt-1 text-sm text-slate-600">
                          {course.lessons_completed}/{course.lessons_available} bài hoàn thành · {course.assessments_passed}/{course.assessments_published} đánh giá đạt
                        </p>
                      </div>
                      <div className="flex gap-5 text-sm">
                        <div><span className="block text-slate-500">Tiến độ</span><strong className="text-slate-950">{formatPercentage(course.progress_percentage)}</strong></div>
                        <div><span className="block text-slate-500">Nắm vững</span><strong className="text-slate-950">{formatPercentage(course.mastery_percentage)}</strong></div>
                      </div>
                    </div>
                    <div className="mt-3">
                      {course.last_accessed_lesson ? (
                        <Link className="text-sm font-medium text-orange-700 hover:text-orange-800" to={`/lessons/${course.last_accessed_lesson.id}`}>
                          Tiếp tục: {course.last_accessed_lesson.title}
                        </Link>
                      ) : (
                        <Link className="text-sm font-medium text-orange-700 hover:text-orange-800" to={`/courses/${course.course_id}`}>
                          Mở khóa học
                        </Link>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {!loading && teacherSummary && (
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
                <button type="button" onClick={() => setSelectedCourseReport(null)} className="text-sm text-slate-600 hover:text-slate-950">
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
            </section>
          )}
        </>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="quick-actions-title">
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
          {!isTeacher && (
            <Link to="/courses" className="rounded-lg border border-slate-200 p-4 hover:border-orange-400">
              <h3 className="font-semibold text-orange-700">Danh sách khóa học</h3>
              <p className="mt-1 text-sm text-slate-600">Mở khóa học và tiếp tục bài gần nhất.</p>
            </Link>
          )}
          <Link to="/forum" className="rounded-lg border border-slate-200 p-4 hover:border-orange-400">
            <h3 className="font-semibold text-orange-700">Diễn đàn</h3>
            <p className="mt-1 text-sm text-slate-600">Trao đổi với giảng viên và cộng đồng.</p>
          </Link>
        </div>
      </section>
    </div>
  )
}
