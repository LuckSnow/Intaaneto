import { useEffect, useState } from 'react'
import { BookOpen, Edit3, Loader2, Plus, Save, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import { courseService } from '../services/courseService'

const blankCourse = () => ({
  title: '',
  description: '',
  difficulty: 'beginner',
  duration_hours: 0,
  objectives: '',
  prerequisites: '',
  order: 0,
  is_published: false,
})

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

const inputClass = 'mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20 disabled:bg-slate-100'

export default function TeacherCourses() {
  const [courses, setCourses] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [form, setForm] = useState(blankCourse)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    courseService.getManagedCourses()
      .then((data) => {
        if (active) setCourses(data)
      })
      .catch((requestError) => {
        if (active) setError(firstError(requestError.response?.data) || 'Không thể tải khóa học được quản lý.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const startCreate = () => {
    setSelectedId(null)
    setForm(blankCourse())
    setError('')
  }

  const startEdit = (course) => {
    setSelectedId(course.id)
    setForm({
      title: course.title,
      description: course.description || '',
      difficulty: course.difficulty,
      duration_hours: course.duration_hours || 0,
      objectives: course.objectives || '',
      prerequisites: course.prerequisites || '',
      order: course.order || 0,
      is_published: course.is_published,
    })
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSave = async (event) => {
    event.preventDefault()
    if (!form.title.trim() || !form.description.trim()) {
      setError('Tiêu đề và mô tả khóa học không được để trống.')
      return
    }
    setSaving(true)
    setError('')
    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      difficulty: form.difficulty,
      duration_hours: Number(form.duration_hours),
      objectives: form.objectives.trim(),
      prerequisites: form.prerequisites.trim(),
      order: Number(form.order),
      is_published: form.is_published,
    }
    try {
      const saved = selectedId
        ? await courseService.updateCourse(selectedId, payload)
        : await courseService.createCourse(payload)
      setCourses((current) => {
        const exists = current.some((course) => course.id === saved.id)
        return exists
          ? current.map((course) => (course.id === saved.id ? saved : course))
          : [...current, saved]
      })
      setSelectedId(saved.id)
      setForm((current) => ({ ...current, is_published: saved.is_published }))
      toast.success(selectedId ? 'Đã cập nhật khóa học.' : 'Đã tạo khóa học.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể lưu khóa học.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedId) return
    const selected = courses.find((course) => course.id === selectedId)
    if (!window.confirm(`Xóa khóa học “${selected?.title || ''}”? Chỉ course rỗng mới được xóa.`)) return
    setSaving(true)
    setError('')
    try {
      await courseService.deleteCourse(selectedId)
      setCourses((current) => current.filter((course) => course.id !== selectedId))
      startCreate()
      toast.success('Đã xóa khóa học rỗng.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể xóa khóa học.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const selectedCourse = courses.find((course) => course.id === selectedId)
  const deleteDisabled = saving || !selectedId || (selectedCourse?.lessons_count || 0) > 0 || (selectedCourse?.total_students || 0) > 0

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 py-8">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <BookOpen className="h-7 w-7 text-orange-700" aria-hidden="true" />
              <h1 className="text-2xl font-bold text-slate-950">Quản lý khóa học</h1>
            </div>
            <p className="mt-2 max-w-2xl text-slate-600">Tạo lộ trình ở trạng thái nháp, bổ sung PDF và bài đánh giá, rồi mới xuất bản cho học viên.</p>
          </div>
          <Button type="button" onClick={startCreate} className="bg-orange-700 text-white hover:bg-orange-800">
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" /> Khóa học mới
          </Button>
        </header>

        {error && <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">{error}</div>}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <form onSubmit={handleSave} className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">{selectedId ? 'Chỉnh sửa khóa học' : 'Khóa học mới'}</h2>
                {selectedCourse && <p className="mt-1 text-sm text-slate-600">Đường dẫn ổn định: {selectedCourse.slug}</p>}
              </div>
              <span className={`rounded-full px-3 py-1 text-sm font-medium ${form.is_published ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}`}>{form.is_published ? 'Đã xuất bản' : 'Bản nháp'}</span>
            </div>

            <div className="grid gap-5">
              <label className="text-sm font-medium text-slate-800">Tiêu đề<input className={inputClass} maxLength={255} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
              <label className="text-sm font-medium text-slate-800">Mô tả<textarea className={inputClass} rows={4} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required /></label>
              <div className="grid gap-5 sm:grid-cols-3">
                <label className="text-sm font-medium text-slate-800">Trình độ<select className={inputClass} value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value })}><option value="beginner">Cơ bản</option><option value="intermediate">Trung bình</option><option value="advanced">Nâng cao</option></select></label>
                <label className="text-sm font-medium text-slate-800">Thời lượng (giờ)<input className={inputClass} type="number" min="0" value={form.duration_hours} onChange={(event) => setForm({ ...form, duration_hours: Number(event.target.value) })} /></label>
                <label className="text-sm font-medium text-slate-800">Thứ tự<input className={inputClass} type="number" min="0" value={form.order} onChange={(event) => setForm({ ...form, order: Number(event.target.value) })} /></label>
              </div>
              <label className="text-sm font-medium text-slate-800">Mục tiêu học tập<textarea className={inputClass} rows={3} value={form.objectives} onChange={(event) => setForm({ ...form, objectives: event.target.value })} /></label>
              <label className="text-sm font-medium text-slate-800">Kiến thức tiên quyết<textarea className={inputClass} rows={3} value={form.prerequisites} onChange={(event) => setForm({ ...form, prerequisites: event.target.value })} /></label>
              <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-4 py-3 text-sm font-medium text-slate-800"><input type="checkbox" className="h-4 w-4 accent-orange-700" checked={form.is_published} disabled={!selectedId || (selectedCourse?.lessons_count || 0) === 0} onChange={(event) => setForm({ ...form, is_published: event.target.checked })} />Xuất bản khóa học</label>
              {(!selectedId || (selectedCourse?.lessons_count || 0) === 0) && <p className="-mt-3 text-sm text-slate-600">Hãy lưu course nháp và thêm ít nhất một lesson sẵn sàng trước khi xuất bản.</p>}
            </div>

            <div className="mt-6 flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
              <Button type="button" variant="outline" onClick={handleDelete} disabled={deleteDisabled} className="border-red-300 text-red-700 hover:bg-red-50"><Trash2 className="mr-2 h-4 w-4" aria-hidden="true" /> Xóa course rỗng</Button>
              <Button type="submit" disabled={saving} className="bg-orange-700 text-white hover:bg-orange-800">{saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <Save className="mr-2 h-4 w-4" aria-hidden="true" />}{selectedId ? 'Lưu thay đổi' : 'Tạo khóa học'}</Button>
            </div>
            {selectedId && deleteDisabled && !saving && <p className="mt-3 text-sm text-slate-600">Course đã có lesson hoặc học viên không thể xóa; hãy chuyển về bản nháp để lưu trữ.</p>}
          </form>

          <aside className="rounded-xl border border-slate-200 bg-white p-4" aria-label="Khóa học đang quản lý">
            <h2 className="px-2 pb-3 font-semibold text-slate-950">Khóa học của bạn</h2>
            {loading ? (
              <div className="flex items-center gap-2 px-2 py-8 text-sm text-slate-600" role="status"><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Đang tải…</div>
            ) : courses.length === 0 ? (
              <p className="px-2 py-8 text-sm text-slate-600">Chưa có khóa học. Hãy tạo bản nháp đầu tiên.</p>
            ) : (
              <div className="space-y-2">
                {courses.map((course) => (
                  <button key={course.id} type="button" onClick={() => startEdit(course)} className={`w-full rounded-lg border p-3 text-left transition ${selectedId === course.id ? 'border-orange-600 bg-orange-50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'}`}>
                    <span className="flex items-start justify-between gap-2"><span className="font-medium text-slate-950">{course.title}</span><Edit3 className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" /></span>
                    <span className="mt-1 block text-xs text-slate-600">{course.lessons_count} bài · {course.total_students} học viên · {course.is_published ? 'Đã xuất bản' : 'Bản nháp'}</span>
                  </button>
                ))}
              </div>
            )}
            <div className="mt-4 grid gap-2 border-t border-slate-200 pt-4 text-sm">
              <Link to="/teacher/upload" className="rounded-lg px-3 py-2 text-orange-800 hover:bg-orange-50">Tải PDF cho course →</Link>
              <Link to="/teacher/assessments" className="rounded-lg px-3 py-2 text-orange-800 hover:bg-orange-50">Biên soạn assessment →</Link>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
