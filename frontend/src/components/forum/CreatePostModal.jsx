import { useRef, useState } from 'react'
import { ImagePlus, X } from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import { forumService } from '../../services/forumService'
import { useAuthStore } from '../../store/authStore'
import { getUserAvatar } from '../../utils/avatar'

export default function CreatePostModal({ isOpen, onClose, onCreated, courses = [] }) {
  const user = useAuthStore((state) => state.user)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [courseId, setCourseId] = useState('')
  const [images, setImages] = useState([null, null, null, null])
  const [previews, setPreviews] = useState([null, null, null, null])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef(null)
  const avatar = getUserAvatar(user)

  if (!isOpen) return null

  const reset = () => {
    previews.filter(Boolean).forEach((preview) => URL.revokeObjectURL(preview))
    setTitle('')
    setContent('')
    setCourseId('')
    setImages([null, null, null, null])
    setPreviews([null, null, null, null])
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleImageAdd = (event) => {
    const nextImages = [...images]
    const nextPreviews = [...previews]
    Array.from(event.target.files).slice(0, 4).forEach((file) => {
      const index = nextImages.findIndex((image) => image === null)
      if (index < 0) return
      nextImages[index] = file
      nextPreviews[index] = URL.createObjectURL(file)
    })
    setImages(nextImages)
    setPreviews(nextPreviews)
    event.target.value = ''
  }

  const removeImage = (index) => {
    if (previews[index]) URL.revokeObjectURL(previews[index])
    setImages((current) => current.map((image, itemIndex) => itemIndex === index ? null : image))
    setPreviews((current) => current.map((preview, itemIndex) => itemIndex === index ? null : preview))
  }

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim() || !courseId) {
      toast.error('Vui lòng nhập tiêu đề, nội dung và chọn khóa học')
      return
    }
    setIsSubmitting(true)
    try {
      await forumService.createPost({
        title: title.trim(),
        content: content.trim(),
        category: 'question',
        course_id: courseId,
        image_1: images[0],
        image_2: images[1],
        image_3: images[2],
        image_4: images[3],
      })
      toast.success('Đăng bài thành công!')
      reset()
      onCreated?.()
    } catch {
      toast.error('Đăng bài thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="create-post-title">
      <button type="button" className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={handleClose} aria-label="Đóng" />
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/15 bg-slate-950/95 shadow-2xl">
        <header className="flex items-center justify-between border-b border-white/10 p-5 sm:px-6">
          <h2 id="create-post-title" className="text-xl font-bold text-white">Tạo bài viết mới</h2>
          <button type="button" onClick={handleClose} className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-white/70 hover:bg-white/10" aria-label="Đóng form">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </header>

        <div className="space-y-5 p-5 sm:p-6">
          <div className="flex items-center gap-3">
            {avatar ? <img src={avatar} alt="" className="h-10 w-10 rounded-full object-cover" /> : <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20 font-bold text-orange-200">{user?.full_name?.charAt(0) || 'U'}</div>}
            <div><p className="font-medium text-white">{user?.full_name}</p><p className="text-xs text-white/50">@{user?.username}</p></div>
          </div>

          <div>
            <label htmlFor="forum-course" className="mb-2 block text-sm font-semibold text-white/80">Tag khóa học</label>
            <select id="forum-course" value={courseId} onChange={(event) => setCourseId(event.target.value)} required className="min-h-12 w-full rounded-xl border border-white/15 bg-slate-900 px-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500">
              <option value="">Chọn khóa học</option>
              {courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
            </select>
          </div>

          <div>
            <label htmlFor="forum-title" className="mb-2 block text-sm font-semibold text-white/80">Tiêu đề</label>
            <input id="forum-title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} className="min-h-12 w-full rounded-xl border border-white/15 bg-white/5 px-4 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500" placeholder="Tiêu đề bài viết..." />
          </div>

          <div>
            <label htmlFor="forum-content" className="mb-2 block text-sm font-semibold text-white/80">Nội dung</label>
            <textarea id="forum-content" value={content} onChange={(event) => setContent(event.target.value)} maxLength={20000} rows={7} className="w-full resize-y rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500" placeholder="Viết nội dung bài viết..." />
          </div>

          <div className="flex flex-wrap gap-3">
            {previews.map((preview, index) => preview && (
              <div key={preview} className="relative h-24 w-24 overflow-hidden rounded-xl border border-white/10">
                <img src={preview} alt="Ảnh đã chọn" className="h-full w-full object-cover" />
                <button type="button" onClick={() => removeImage(index)} className="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-black/70" aria-label="Xóa ảnh"><X className="h-4 w-4 text-white" /></button>
              </div>
            ))}
          </div>
        </div>

        <footer className="flex items-center justify-between gap-4 border-t border-white/10 p-5 sm:px-6">
          <input type="file" ref={fileInputRef} onChange={handleImageAdd} accept="image/jpeg,image/png,image/webp" multiple className="hidden" />
          <button type="button" onClick={() => fileInputRef.current?.click()} disabled={images.filter(Boolean).length >= 4} className="inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm text-white/70 hover:bg-white/10 disabled:opacity-40">
            <ImagePlus className="h-5 w-5" aria-hidden="true" /> Thêm ảnh
          </button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !title.trim() || !content.trim() || !courseId} className="min-h-11 bg-orange-600 px-6 font-bold text-white hover:bg-orange-700">
            {isSubmitting ? 'Đang đăng...' : 'Đăng bài'}
          </Button>
        </footer>
      </div>
    </div>
  )
}
