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
  const [authoring, setAuthoring] = useState(null)
  const [summaryText, setSummaryText] = useState('')
  const [authoringBusy, setAuthoringBusy] = useState('')
  const [portrait, setPortrait] = useState(null)
  const [rightsConfirmed, setRightsConfirmed] = useState(false)
  const activeUploadLessonIds = uploadedLessons
    .filter((lesson) => !['completed', 'failed'].includes(lesson.status))
    .map((lesson) => lesson.id)
    .join(',')

  useEffect(() => {
    if (!user || (user.role !== 'teacher' && user.role !== 'admin')) {
      toast.error('Chỉ giáo viên mới có quyền truy cập')
      navigate('/')
      return
    }
    fetchCourses()
  }, [user, navigate])

  useEffect(() => {
    const activeIds = activeUploadLessonIds
      .split(',')
      .filter(Boolean)
      .map(Number)
    if (activeIds.length === 0) return undefined

    let cancelled = false
    const pollStatuses = async () => {
      const updates = await Promise.all(activeIds.map(async (lessonId) => {
        try {
          const result = await courseService.getLessonStatus(lessonId)
          return {
            id: lessonId,
            status: result.status,
            error: result.error || '',
          }
        } catch {
          return null
        }
      }))
      if (cancelled) return
      setUploadedLessons((current) => current.map((lesson) => {
        const update = updates.find((item) => item?.id === lesson.id)
        return update ? { ...lesson, ...update } : lesson
      }))
    }
    pollStatuses()
    const interval = window.setInterval(pollStatuses, 4000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [activeUploadLessonIds])

  useEffect(() => {
    if (!selectedCourse) {
      setUploadedLessons([])
      return undefined
    }
    let cancelled = false
    const restoreStatuses = async () => {
      try {
        const items = await courseService.getIngestionStatuses(selectedCourse)
        if (!cancelled) {
          setUploadedLessons(items.map((item) => ({
            id: item.lesson_id,
            title: item.lesson_title,
            status: item.processing_status,
            error: item.error || '',
          })))
        }
      } catch {
        if (!cancelled) toast.error('Không thể tải trạng thái xử lý PDF')
      }
    }
    restoreStatuses()
    return () => {
      cancelled = true
    }
  }, [selectedCourse])

  useEffect(() => {
    if (!authoring?.lesson_id || !['queued', 'running'].includes(authoring.video?.status)) {
      return undefined
    }
    let cancelled = false
    const poll = async () => {
      try {
        const data = await courseService.getLessonAuthoringStatus(authoring.lesson_id)
        if (!cancelled) setAuthoring(data)
      } catch {
        // Keep the last server-confirmed state visible.
      }
    }
    const interval = window.setInterval(poll, 5000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [authoring?.lesson_id, authoring?.video?.status])

  const fetchCourses = async () => {
    try {
      const data = await courseService.getManagedCourses()
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
      toast.success('PDF đã được đưa vào hàng đợi xử lý')

      // Add to tracking list
      const lesson = result.lesson
      setUploadedLessons((prev) => [
        {
          id: lesson.id,
          title: lesson.title,
          status: result.ingestion_job?.status === 'completed'
            ? 'completed'
            : lesson.processing_status || 'pending',
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
          ? { ...l, status: result.lesson?.processing_status || 'pending', error: '' }
          : l))
      )
      toast.success('PDF đã được đưa vào hàng đợi xử lý lại')
    } catch {
      toast.error('Không thể xử lý lại')
    }
  }

  const openAuthoring = async (lessonId) => {
    setAuthoringBusy('status')
    try {
      const data = await courseService.getLessonAuthoringStatus(lessonId)
      setAuthoring(data)
      setSummaryText(data.summary?.text || '')
      setPortrait(null)
      setRightsConfirmed(false)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Không thể tải trạng thái biên soạn')
    } finally {
      setAuthoringBusy('')
    }
  }

  const runAuthoringAction = async (name, action, successMessage) => {
    setAuthoringBusy(name)
    try {
      const data = await action()
      setAuthoring(data)
      setSummaryText(data.summary?.text || '')
      toast.success(successMessage)
    } catch (error) {
      const responseData = error.response?.data
      const fieldError = responseData && typeof responseData === 'object'
        ? Object.values(responseData).flat().find((message) => typeof message === 'string')
        : null
      toast.error(responseData?.detail || fieldError || 'Không thể thực hiện thao tác')
    } finally {
      setAuthoringBusy('')
    }
  }

  const handleGenerateVideo = async () => {
    if (!portrait || !rightsConfirmed) {
      toast.error('Hãy chọn ảnh và xác nhận quyền sử dụng')
      return
    }
    await runAuthoringAction(
      'video',
      () => courseService.generateLessonVideo(authoring.lesson_id, portrait),
      'Video đã được đưa vào hàng đợi GPU',
    )
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
                  Đang tải PDF...
                </span>
              ) : (
                'Tải lên và xử lý PDF'
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
                      <div className="flex flex-wrap gap-2">
                        <Button
                          onClick={() => openAuthoring(lesson.id)}
                          disabled={authoringBusy === 'status'}
                          className="border border-orange-400/30 bg-orange-500/20 text-orange-200 hover:bg-orange-500/30"
                        >
                          Biên soạn
                        </Button>
                        <Button
                          onClick={() => navigate(`/lessons/${lesson.id}`)}
                          className="bg-green-500/20 border border-green-500/30 text-green-300 hover:bg-green-500/30 rounded-lg px-4 py-2 text-sm"
                        >
                          Mở bài học →
                        </Button>
                      </div>
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

        {authoring && (
          <section className="mt-8 rounded-2xl border border-white/20 bg-slate-950/90 p-6 text-white" aria-label="Biên soạn học liệu AI">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">Biên soạn: {authoring.lesson_title}</h2>
                <p className="mt-1 text-sm text-white/60">
                  PDF {authoring.extracted_chars.toLocaleString('vi-VN')} ký tự · RAG {authoring.rag_ready ? 'đã sẵn sàng' : 'chưa sẵn sàng'}
                </p>
              </div>
              <Button onClick={() => setAuthoring(null)} className="border border-white/20 bg-transparent text-white hover:bg-white/10">Đóng</Button>
            </div>

            <div className="mt-5 grid gap-5">
              <div className="rounded-xl border border-white/15 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold">1. Học liệu PDF và RAG</h3>
                    <p className="text-sm text-white/60">PDF và chỉ mục phải sẵn sàng trước các bước sinh nội dung.</p>
                  </div>
                  {authoring.pdf_url && <a href={authoring.pdf_url} target="_blank" rel="noreferrer" className="text-sm text-orange-300 underline">Mở PDF</a>}
                </div>
              </div>

              <div className="rounded-xl border border-white/15 p-4">
                <h3 className="font-semibold">2. Tóm tắt nháp</h3>
                <p className="mt-1 text-sm text-white/60">AI chỉ tạo bản nháp. Nội dung chỉ xuất hiện cho học viên sau khi bạn duyệt.</p>
                <Button
                  onClick={() => runAuthoringAction('summary', () => courseService.generateLessonSummary(authoring.lesson_id), 'Đã tạo bản tóm tắt nháp')}
                  disabled={!authoring.rag_ready || Boolean(authoringBusy)}
                  className="mt-3 bg-orange-600 text-white hover:bg-orange-700"
                >
                  {authoringBusy === 'summary' ? 'Đang tạo...' : authoring.summary ? 'Tạo lại bản nháp' : 'Tạo bản tóm tắt'}
                </Button>
                {authoring.summary && (
                  <>
                    <textarea
                      value={summaryText}
                      onChange={(event) => setSummaryText(event.target.value)}
                      maxLength={4000}
                      rows={9}
                      className="mt-3 w-full rounded-lg border border-white/20 bg-black/20 p-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                    <div className="mt-2 flex items-center justify-between gap-3 text-sm">
                      <span className={authoring.summary.status === 'approved' ? 'text-emerald-300' : 'text-amber-300'}>
                        {authoring.summary.status === 'approved' ? 'Đã duyệt' : 'Đang chờ duyệt'}
                      </span>
                      <Button
                        onClick={() => runAuthoringAction('approve', () => courseService.approveLessonSummary(authoring.lesson_id, summaryText), 'Đã duyệt bản tóm tắt')}
                        disabled={!summaryText.trim() || Boolean(authoringBusy)}
                        className="bg-emerald-700 text-white hover:bg-emerald-800"
                      >
                        {authoringBusy === 'approve' ? 'Đang lưu...' : 'Duyệt tóm tắt'}
                      </Button>
                    </div>
                  </>
                )}
              </div>

              <div className="rounded-xl border border-white/15 p-4">
                <h3 className="font-semibold">3. Assessment nháp</h3>
                <p className="mt-1 text-sm text-white/60">Sinh 5 câu ở trạng thái draft; hãy kiểm tra đáp án và explanation trước khi publish.</p>
                {authoring.assessment ? (
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <span className="text-sm text-white/70">{authoring.assessment.question_count} câu · {authoring.assessment.is_published ? 'Đã publish' : 'Bản nháp'}</span>
                    <Button onClick={() => navigate(`/teacher/assessments?course=${selectedCourse}&lesson=${authoring.lesson_id}`)} className="bg-orange-600 text-white hover:bg-orange-700">Mở trang rà soát</Button>
                  </div>
                ) : (
                  <Button
                    onClick={() => runAuthoringAction('assessment', () => courseService.generateLessonAssessment(authoring.lesson_id), 'Đã tạo assessment nháp')}
                    disabled={!authoring.rag_ready || Boolean(authoringBusy)}
                    className="mt-3 bg-orange-600 text-white hover:bg-orange-700"
                  >
                    {authoringBusy === 'assessment' ? 'Đang tạo...' : 'Tạo assessment nháp'}
                  </Button>
                )}
              </div>

              <div className="rounded-xl border border-white/15 p-4">
                <h3 className="font-semibold">4. Giọng đọc và SadTalker</h3>
                <p className="mt-1 text-sm text-white/60">TTS local không cần key. Video cần ảnh chân dung có quyền sử dụng và GPU worker.</p>
                <Button
                  onClick={() => runAuthoringAction('narration', () => courseService.generateLessonNarration(authoring.lesson_id), 'Đã tạo giọng đọc local')}
                  disabled={authoring.summary?.status !== 'approved' || Boolean(authoringBusy)}
                  className="mt-3 bg-orange-600 text-white hover:bg-orange-700"
                >
                  {authoringBusy === 'narration' ? 'Đang tạo giọng...' : authoring.narration ? 'Tạo lại giọng đọc' : 'Tạo giọng đọc'}
                </Button>
                {authoring.narration?.audio_url && <audio className="mt-3 w-full" controls src={authoring.narration.audio_url} />}
                {authoring.narration && (
                  <div className="mt-4 space-y-3">
                    <label className="block text-sm font-medium">
                      Ảnh chân dung JPEG/PNG
                      <input type="file" accept="image/jpeg,image/png" onChange={(event) => setPortrait(event.target.files?.[0] || null)} className="mt-2 block w-full text-sm text-white/70" />
                    </label>
                    <label className="flex items-start gap-2 text-sm text-white/70">
                      <input type="checkbox" checked={rightsConfirmed} onChange={(event) => setRightsConfirmed(event.target.checked)} className="mt-1" />
                      Tôi xác nhận có quyền sử dụng ảnh, giọng đọc và kịch bản đã duyệt; video là nội dung tổng hợp.
                    </label>
                    <Button onClick={handleGenerateVideo} disabled={!portrait || !rightsConfirmed || Boolean(authoringBusy)} className="bg-orange-600 text-white hover:bg-orange-700">
                      {authoringBusy === 'video' ? 'Đang đưa vào hàng đợi...' : 'Tạo video SadTalker'}
                    </Button>
                  </div>
                )}
                {authoring.video && (
                  <div className="mt-4 rounded-lg border border-white/10 p-3 text-sm">
                    <p>Video job #{authoring.video.job_id}: {authoring.video.status}</p>
                    {authoring.video.safe_error && <p className="mt-1 text-red-300">{authoring.video.safe_error}</p>}
                    {authoring.video.video_url && <video className="mt-3 w-full rounded-lg" controls src={authoring.video.video_url} />}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
