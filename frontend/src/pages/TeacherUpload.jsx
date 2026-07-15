import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import { courseService } from '../services/courseService'
import toast from 'react-hot-toast'

const STATUS_MAP = {
  pending: { label: 'Chờ xử lý', color: 'text-yellow-400', icon: '⏳' },
  extracting: { label: 'Đang trích xuất văn bản...', color: 'text-blue-400', icon: '📄' },
  completed: { label: 'Đã lập chỉ mục và sẵn sàng hỏi đáp', color: 'text-green-400', icon: '✅' },
  failed: { label: 'Xử lý thất bại', color: 'text-red-400', icon: '❌' },
}

export default function TeacherUpload() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [courses, setCourses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [order, setOrder] = useState(1)
  const [uploading, setUploading] = useState(false)
  const [uploadedLessons, setUploadedLessons] = useState([])

  useEffect(() => {
    if (!user || (user.role !== 'teacher' && user.role !== 'admin')) {
      toast.error('Chỉ giáo viên mới có quyền truy cập')
      navigate('/')
      return
    }
    fetchCourses()
  }, [user, navigate])

  const fetchCourses = async () => {
    try {
      const data = await courseService.getCourses()
      setCourses(data)
      if (data.length > 0) setSelectedCourse(data[0].id)
    } catch (error) {
      console.error(error)
    }
  }

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (!selected) return
    const ext = selected.name.split('.').pop().toLowerCase()
    if (ext !== 'pdf') {
      toast.error('Chỉ hỗ trợ file PDF')
      return
    }
    if (selected.size > 20 * 1024 * 1024) {
      toast.error('File PDF không được vượt quá 20MB')
      return
    }
    setFile(selected)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      toast.error('Vui lòng chọn file bài giảng')
      return
    }
    if (!selectedCourse) {
      toast.error('Vui lòng chọn khóa học')
      return
    }
    if (!title.trim()) {
      toast.error('Vui lòng nhập tiêu đề bài giảng')
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('course', selectedCourse)
      formData.append('title', title.trim())
      formData.append('description', description.trim())
      formData.append('uploaded_file', file)
      formData.append('order', order)

      const result = await courseService.uploadLesson(formData)
      toast.success('PDF đã được trích xuất và lập chỉ mục')

      // Add to tracking list
      const lesson = result.lesson
      setUploadedLessons((prev) => [
        {
          id: lesson.id,
          title: lesson.title,
          status: lesson.processing_status || 'pending',
          error: '',
        },
        ...prev,
      ])

      // Reset form
      setTitle('')
      setDescription('')
      setFile(null)
      setOrder((prev) => prev + 1)
      // Reset file input
      const fileInput = document.getElementById('lesson-file-input')
      if (fileInput) fileInput.value = ''
    } catch (error) {
      const msg = error.response?.data
      if (typeof msg === 'object') {
        const firstKey = Object.keys(msg)[0]
        toast.error(Array.isArray(msg[firstKey]) ? msg[firstKey][0] : String(msg[firstKey]))
      } else {
        toast.error('Tải lên thất bại')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleReprocess = async (lessonId) => {
    try {
      const result = await courseService.reprocessLesson(lessonId)
      setUploadedLessons((prev) =>
        prev.map((l) => (l.id === lessonId
          ? { ...l, status: result.lesson?.processing_status || 'completed', error: '' }
          : l))
      )
      toast.success('PDF đã được xử lý lại')
    } catch {
      toast.error('Không thể xử lý lại')
    }
  }

  return (
    <div className="min-h-screen">
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      />

      <div className="max-w-4xl mx-auto px-6 py-10 pt-28">
        {/* Header */}
        <div className="text-center mb-10">
          <h1
            className="text-4xl font-bold text-white mb-3"
            style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}
          >
            📤 Tải Bài Giảng
          </h1>
          <p className="text-lg text-white/70">
            Tải lên một file PDF để trích xuất nội dung và lập chỉ mục cho AI Tutor
          </p>
        </div>

        {/* Upload Form */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Course Select */}
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">Khóa học</label>
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 transition"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id} className="bg-gray-900 text-white">
                    {c.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Title */}
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">Tiêu đề bài giảng</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: Chương 1 - Mô hình OSI"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 transition"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">Mô tả (tùy chọn)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Mô tả ngắn gọn nội dung bài giảng..."
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 transition resize-none"
              />
            </div>

            {/* Order */}
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">Thứ tự bài học</label>
              <input
                type="number"
                min={1}
                value={order}
                onChange={(e) => setOrder(Number(e.target.value))}
                className="w-32 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 transition"
              />
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">File bài giảng (PDF)</label>
              <div className="relative">
                <input
                  id="lesson-file-input"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileChange}
                  className="block w-full text-white/70 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:bg-orange-500/20 file:text-orange-300 file:font-semibold file:cursor-pointer hover:file:bg-orange-500/30 transition"
                />
              </div>
              {file && (
                <p className="mt-2 text-white/60 text-sm">
                  📎 {file.name} ({(file.size / (1024 * 1024)).toFixed(1)} MB)
                </p>
              )}
            </div>

            {/* Submit */}
            <Button
              type="submit"
              disabled={uploading}
              className="w-full py-4 text-lg rounded-xl bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(239,68,68,0.8)] disabled:opacity-50"
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                  Đang tải lên và lập chỉ mục...
                </span>
              ) : (
                'Tải lên & lập chỉ mục PDF'
              )}
            </Button>
          </form>
        </div>

        {/* Processing Status List */}
        {uploadedLessons.length > 0 && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8">
            <h2 className="text-xl font-bold text-white mb-6">📊 Trạng thái xử lý</h2>
            <div className="space-y-4">
              {uploadedLessons.map((lesson) => {
                const st = STATUS_MAP[lesson.status] || STATUS_MAP.pending
                return (
                  <div
                    key={lesson.id}
                    className="bg-white/5 border border-white/10 rounded-xl p-5 flex items-center gap-4"
                  >
                    <span className="text-2xl">{st.icon}</span>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-semibold truncate">{lesson.title}</h3>
                      <p className={`text-sm ${st.color}`}>{st.label}</p>
                      {lesson.error && (
                        <p className="text-red-400 text-xs mt-1">{lesson.error}</p>
                      )}
                    </div>

                    {/* Progress animation for non-terminal states */}
                    {!['completed', 'failed'].includes(lesson.status) && (
                      <div className="w-8 h-8">
                        <div className="animate-spin h-6 w-6 border-2 border-orange-400 border-t-transparent rounded-full" />
                      </div>
                    )}

                    {lesson.status === 'completed' && (
                      <Button
                        onClick={() => navigate(`/lessons/${lesson.id}`)}
                        className="bg-green-500/20 border border-green-500/30 text-green-300 hover:bg-green-500/30 rounded-lg px-4 py-2 text-sm"
                      >
                        Mở bài học →
                      </Button>
                    )}

                    {lesson.status === 'failed' && (
                      <Button
                        onClick={() => handleReprocess(lesson.id)}
                        className="bg-red-500/20 border border-red-500/30 text-red-300 hover:bg-red-500/30 rounded-lg px-4 py-2 text-sm"
                      >
                        Thử lại
                      </Button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
