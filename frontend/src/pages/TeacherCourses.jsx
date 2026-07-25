import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  BookOpen,
  Clock3,
  Edit3,
  Filter,
  Loader2,
  Plus,
  Search,
  Users,
} from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import CourseFormModal from '../components/courses/CourseFormModal'
import { Button } from '@/components/ui/button'
import { courseService } from '../services/courseService'

const firstError = (value) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return firstError(value[0])
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) {
      const message = firstError(item)
      if (message) return message
    }
  }
  return ''
}

export default function TeacherCourses() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedCourseId = searchParams.get('course')
  const [courses, setCourses] = useState([])
  const [editingCourse, setEditingCourse] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState('newest')

  useEffect(() => {
    let active = true
    courseService.getManagedCourses()
      .then((data) => {
        if (!active) return
        setCourses(data)
        const requested = data.find((course) => String(course.id) === requestedCourseId)
        if (requested) {
          setEditingCourse(requested)
          setModalOpen(true)
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(firstError(requestError.response?.data) || 'Không thể tải các khóa học bạn quản lý.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [requestedCourseId])

  const openCreate = () => {
    setEditingCourse(null)
    setModalOpen(true)
  }

  const openEdit = (course) => {
    setEditingCourse(course)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingCourse(null)
    if (requestedCourseId) setSearchParams({}, { replace: true })
  }

  const handleSaved = (saved) => {
    setCourses((current) => {
      const exists = current.some((course) => course.id === saved.id)
      return exists
        ? current.map((course) => (course.id === saved.id ? saved : course))
        : [saved, ...current]
    })
    closeModal()
  }

  const handleDeleted = (courseId) => {
    setCourses((current) => current.filter((course) => course.id !== courseId))
    closeModal()
  }

  const filteredCourses = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase('vi')
    return courses
      .filter((course) => {
        const matchesQuery = !normalizedQuery
          || course.title.toLocaleLowerCase('vi').includes(normalizedQuery)
          || (course.description || '').toLocaleLowerCase('vi').includes(normalizedQuery)
        const matchesFilter = filter === 'all'
          || (filter === 'published' && course.is_published)
          || (filter === 'draft' && !course.is_published)
          || course.difficulty === filter
        return matchesQuery && matchesFilter
      })
      .sort((first, second) => {
        if (sort === 'az') return first.title.localeCompare(second.title, 'vi')
        if (sort === 'students') return Number(second.total_students || 0) - Number(first.total_students || 0)
        return new Date(second.created_at || 0) - new Date(first.created_at || 0)
      })
  }, [courses, filter, query, sort])

  const openDetail = (courseId) => navigate(`/teacher/courses/${courseId}`)

  return (
    <div className="min-h-[calc(100vh-3.5rem)] py-6 text-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <BookOpen className="h-7 w-7 text-orange-300" aria-hidden="true" />
              <h1 className="text-2xl font-bold">Quản lý khóa học</h1>
            </div>
            <p className="mt-2 max-w-2xl text-white/70">
              Quản lý nội dung giảng dạy, học viên và tiến độ của từng khóa học.
            </p>
          </div>
          <Button type="button" onClick={openCreate} className="bg-orange-600 text-white hover:bg-orange-700">
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" /> Khóa học mới
          </Button>
        </header>

        {error && <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">{error}</div>}

        <section className="mb-6 grid gap-3 rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-md lg:grid-cols-[minmax(240px,1fr)_220px_190px]">
          <label className="relative">
            <span className="sr-only">Tìm kiếm khóa học</span>
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-white/45" aria-hidden="true" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm kiếm khóa học..." className="min-h-11 w-full rounded-lg border border-white/15 bg-black/20 pl-10 pr-3 text-sm text-white outline-none placeholder:text-white/40 focus:border-orange-400 focus:ring-2 focus:ring-orange-400/20" />
          </label>
          <label className="relative">
            <span className="sr-only">Lọc khóa học</span>
            <Filter className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-white/45" aria-hidden="true" />
            <select value={filter} onChange={(event) => setFilter(event.target.value)} className="min-h-11 w-full rounded-lg border border-white/15 bg-[#321c2d] pl-10 pr-3 text-sm text-white outline-none focus:border-orange-400">
              <option value="all">Tất cả khóa tôi quản lý</option>
              <option value="published">Đã xuất bản</option>
              <option value="draft">Bản nháp</option>
              <option value="beginner">Cơ bản</option>
              <option value="intermediate">Trung bình</option>
              <option value="advanced">Nâng cao</option>
            </select>
          </label>
          <label>
            <span className="sr-only">Sắp xếp khóa học</span>
            <select value={sort} onChange={(event) => setSort(event.target.value)} className="min-h-11 w-full rounded-lg border border-white/15 bg-[#321c2d] px-3 text-sm text-white outline-none focus:border-orange-400">
              <option value="newest">Mới nhất</option>
              <option value="az">A–Z</option>
              <option value="students">Nhiều học viên nhất</option>
            </select>
          </label>
        </section>

        <section aria-label="Khóa học đang quản lý">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="font-semibold">Khóa học của bạn</h2>
            <span className="text-sm text-white/60">{filteredCourses.length}/{courses.length} khóa học</span>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-4 py-8 text-sm text-white/70" role="status"><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Đang tải…</div>
          ) : courses.length === 0 ? (
            <div className="rounded-xl border border-white/15 bg-white/10 px-5 py-10 text-center">
              <p className="font-semibold">Bạn chưa tạo khóa học nào.</p>
              <Button type="button" onClick={openCreate} className="mt-4 bg-orange-600 text-white hover:bg-orange-700"><Plus className="mr-2 h-4 w-4" />Khóa học mới</Button>
            </div>
          ) : filteredCourses.length === 0 ? (
            <p className="rounded-xl border border-white/15 bg-white/10 px-5 py-8 text-center text-sm text-white/70">Không tìm thấy khóa học phù hợp.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredCourses.map((course) => (
                <article
                  key={course.id}
                  role="link"
                  tabIndex={0}
                  onClick={() => openDetail(course.id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      openDetail(course.id)
                    }
                  }}
                  className="group flex min-h-64 cursor-pointer flex-col rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur-md transition hover:border-orange-300/50 hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
                  aria-label={`Xem chi tiết khóa học ${course.title}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="rounded-full bg-orange-500/15 px-2.5 py-1 text-xs font-semibold text-orange-200">
                      {course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}
                    </span>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${course.is_published ? 'bg-emerald-400/15 text-emerald-200' : 'bg-white/10 text-white/65'}`}>{course.is_published ? 'Đã xuất bản' : 'Bản nháp'}</span>
                  </div>
                  <h3 className="mt-4 line-clamp-2 text-lg font-bold">{course.title}</h3>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-white/65">{course.description}</p>
                  <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-white/65">
                    <span className="flex items-center gap-1.5"><BookOpen className="h-4 w-4 text-orange-300" />{course.lessons_count || 0} bài học</span>
                    <span className="flex items-center gap-1.5"><Users className="h-4 w-4 text-orange-300" />{course.total_students || 0} học viên</span>
                    <span className="flex items-center gap-1.5"><Clock3 className="h-4 w-4 text-orange-300" />{course.duration_hours || 0} giờ</span>
                  </div>
                  <div className="mt-auto flex items-center justify-between gap-2 pt-5">
                    <span className="inline-flex min-h-11 items-center text-sm font-semibold text-orange-300">
                      Xem chi tiết <ArrowRight className="ml-1.5 h-4 w-4 transition group-hover:translate-x-0.5" />
                    </span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation()
                        openEdit(course)
                      }}
                      onKeyDown={(event) => event.stopPropagation()}
                      className="inline-flex min-h-11 items-center rounded-lg px-3 text-sm font-semibold text-white/70 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
                      aria-label={`Chỉnh sửa ${course.title}`}
                    >
                      <Edit3 className="mr-1.5 h-4 w-4" /> Sửa
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <CourseFormModal
        open={modalOpen}
        course={editingCourse}
        onClose={closeModal}
        onSaved={handleSaved}
        onDeleted={handleDeleted}
      />
    </div>
  )
}
