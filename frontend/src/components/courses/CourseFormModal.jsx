import { useEffect, useRef, useState } from 'react'
import { Loader2, Save, Trash2, X } from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import { courseService } from '../../services/courseService'

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

const toForm = (course) => course ? {
  title: course.title || '',
  description: course.description || '',
  difficulty: course.difficulty || 'beginner',
  duration_hours: course.duration_hours || 0,
  objectives: course.objectives || '',
  prerequisites: course.prerequisites || '',
  order: course.order || 0,
  is_published: Boolean(course.is_published),
} : blankCourse()

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

export default function CourseFormModal({ open, course, onClose, onSaved, onDeleted }) {
  const [form, setForm] = useState(blankCourse)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [thumbnailFile, setThumbnailFile] = useState(null)
  const [thumbnailPreview, setThumbnailPreview] = useState('')
  const [removeThumbnail, setRemoveThumbnail] = useState(false)
  const fileRef = useRef(null)
  const dialogRef = useRef(null)
  const closeRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    setForm(toForm(course))
    setError('')
    setThumbnailFile(null)
    setRemoveThumbnail(false)
    if (fileRef.current) fileRef.current.value = ''
  }, [course, open])

  useEffect(() => {
    if (!thumbnailFile) {
      setThumbnailPreview('')
      return undefined
    }
    const url = URL.createObjectURL(thumbnailFile)
    setThumbnailPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [thumbnailFile])

  useEffect(() => {
    if (!open) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()

    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && !saving) onClose()
      if (event.key !== 'Tab' || !dialogRef.current) return
      const focusable = [...dialogRef.current.querySelectorAll('button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled])')]
      if (!focusable.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose, open, saving])

  if (!open) return null

  const handleSave = async (event) => {
    event.preventDefault()
    if (!form.title.trim() || !form.description.trim()) {
      setError('Tiêu đề và mô tả khóa học không được để trống.')
      return
    }
    setSaving(true)
    setError('')
    const values = {
      title: form.title.trim(),
      description: form.description.trim(),
      difficulty: form.difficulty,
      duration_hours: Number(form.duration_hours),
      objectives: form.objectives.trim(),
      prerequisites: form.prerequisites.trim(),
      order: Number(form.order),
      is_published: form.is_published,
      remove_thumbnail: removeThumbnail,
    }
    const payload = new FormData()
    Object.entries(values).forEach(([key, value]) => payload.append(key, String(value)))
    if (thumbnailFile) payload.append('thumbnail_upload', thumbnailFile)
    try {
      const saved = course
        ? await courseService.updateCourse(course.id, payload)
        : await courseService.createCourse(payload)
      toast.success(course ? 'Đã cập nhật khóa học.' : 'Đã tạo khóa học.')
      onSaved(saved)
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể lưu khóa học.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!course) return
    if (!window.confirm(`Xóa khóa học “${course.title}”? Chỉ khóa học rỗng mới được xóa.`)) return
    setSaving(true)
    setError('')
    try {
      await courseService.deleteCourse(course.id)
      toast.success('Đã xóa khóa học rỗng.')
      onDeleted(course.id)
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể xóa khóa học.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const deleteDisabled = saving || !course || (course.lessons_count || 0) > 0 || (course.total_students || 0) > 0

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/75 p-3 backdrop-blur-sm sm:p-6" onMouseDown={(event) => event.target === event.currentTarget && !saving && onClose()}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="course-form-title" className="max-h-[94vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-slate-50 text-slate-950 shadow-2xl">
        <form onSubmit={handleSave}>
          <header className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-slate-50/95 px-5 py-4 backdrop-blur sm:px-7">
            <div>
              <h2 id="course-form-title" className="text-xl font-bold">{course ? 'Chỉnh sửa khóa học' : 'Tạo khóa học mới'}</h2>
              <p className="mt-1 text-sm text-slate-600">{course ? 'Cập nhật thông tin khóa học đang quản lý.' : 'Tạo bản nháp trước, sau đó thêm bài học để xuất bản.'}</p>
            </div>
            <button ref={closeRef} type="button" onClick={onClose} disabled={saving} className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600" aria-label="Đóng biểu mẫu"><X className="h-5 w-5" /></button>
          </header>

          <div className="grid gap-5 px-5 py-6 sm:px-7">
            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</div>}
            <label className="text-sm font-medium">Tiêu đề<input className={inputClass} maxLength={255} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required autoFocus /></label>
            <label className="text-sm font-medium">Mô tả<textarea className={inputClass} rows={4} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required /></label>
            <section className="rounded-xl border border-slate-200 bg-white p-4" aria-label="Ảnh bìa khóa học">
              <label htmlFor="course-thumbnail" className="text-sm font-medium">Ảnh bìa khóa học</label>
              <p id="course-thumbnail-help" className="mt-1 text-sm text-slate-600">JPG, PNG hoặc WebP tĩnh, tối đa 2 MB và 4096 pixel mỗi chiều. Nên dùng tỷ lệ 16:9.</p>
              {(thumbnailPreview || (!removeThumbnail && course?.thumbnail)) && (
                <img src={thumbnailPreview || course.thumbnail} alt="Xem trước ảnh bìa khóa học" className="mt-3 aspect-video w-full max-w-sm rounded-lg border border-slate-200 object-cover" />
              )}
              <input ref={fileRef} id="course-thumbnail" type="file" accept="image/jpeg,image/png,image/webp" disabled={saving} aria-describedby="course-thumbnail-help" className={`${inputClass} min-h-11`} onChange={(event) => {
                const file = event.target.files?.[0]
                if (!file) return
                if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 2 * 1024 * 1024) {
                  setError('Chọn ảnh JPG, PNG hoặc WebP không quá 2 MB.')
                  event.target.value = ''
                  return
                }
                setError('')
                setThumbnailFile(file)
                setRemoveThumbnail(false)
              }} />
              {(thumbnailFile || (course?.thumbnail && !removeThumbnail)) && (
                <button type="button" disabled={saving} className="mt-2 min-h-11 rounded px-2 text-sm font-medium text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600" onClick={() => {
                  setThumbnailFile(null)
                  setRemoveThumbnail(true)
                  if (fileRef.current) fileRef.current.value = ''
                }}>Gỡ ảnh bìa</button>
              )}
              {removeThumbnail && <p className="mt-2 text-sm text-slate-600">Ảnh bìa sẽ được gỡ khi lưu thay đổi.</p>}
            </section>
            <div className="grid gap-5 sm:grid-cols-3">
              <label className="text-sm font-medium">Trình độ<select className={inputClass} value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value })}><option value="beginner">Cơ bản</option><option value="intermediate">Trung bình</option><option value="advanced">Nâng cao</option></select></label>
              <label className="text-sm font-medium">Thời lượng (giờ)<input className={inputClass} type="number" min="0" value={form.duration_hours} onChange={(event) => setForm({ ...form, duration_hours: Number(event.target.value) })} /></label>
              <label className="text-sm font-medium">Thứ tự<input className={inputClass} type="number" min="0" value={form.order} onChange={(event) => setForm({ ...form, order: Number(event.target.value) })} /></label>
            </div>
            <label className="text-sm font-medium">Mục tiêu học tập<textarea className={inputClass} rows={3} value={form.objectives} onChange={(event) => setForm({ ...form, objectives: event.target.value })} /></label>
            <label className="text-sm font-medium">Kiến thức tiên quyết<textarea className={inputClass} rows={3} value={form.prerequisites} onChange={(event) => setForm({ ...form, prerequisites: event.target.value })} /></label>
            <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-4 py-3 text-sm font-medium"><input type="checkbox" className="h-4 w-4 accent-orange-700" checked={form.is_published} disabled={!course || (course.lessons_count || 0) === 0} onChange={(event) => setForm({ ...form, is_published: event.target.checked })} />Xuất bản khóa học</label>
            {(!course || (course.lessons_count || 0) === 0) && <p className="-mt-3 text-sm text-slate-600">Hãy lưu bản nháp và thêm ít nhất một bài học sẵn sàng trước khi xuất bản.</p>}
          </div>

          <footer className="sticky bottom-0 flex flex-col gap-3 border-t border-slate-200 bg-slate-50/95 px-5 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between sm:px-7">
            <Button type="button" variant="outline" onClick={handleDelete} disabled={deleteDisabled} className="border-red-300 text-red-700 hover:bg-red-50"><Trash2 className="mr-2 h-4 w-4" /> Xóa khóa học rỗng</Button>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>Hủy</Button>
              <Button type="submit" disabled={saving} className="bg-orange-600 text-white hover:bg-orange-700">{saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}{course ? 'Lưu thay đổi' : 'Lưu bản nháp'}</Button>
            </div>
          </footer>
        </form>
      </div>
    </div>
  )
}
