import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, ChartNoAxesCombined, FileText, Paperclip, Upload, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import { courseService } from '../services/courseService'
import {
  getVideoScriptMetrics,
  VIDEO_SCRIPT_MAX_CHARS,
  VIDEO_SCRIPT_MAX_SEGMENTS,
  VIDEO_SCRIPT_TARGET_MAX_CHARS,
  VIDEO_SCRIPT_TARGET_MIN_CHARS,
} from '../utils/multimediaScript'
import toast from 'react-hot-toast'

const STATUS_MAP = {
  pending: { label: 'Chờ xử lý', color: 'text-yellow-400', icon: FileText },
  extracting: { label: 'Đang trích xuất văn bản...', color: 'text-blue-400', icon: FileText },
  completed: { label: 'Đã lập chỉ mục và sẵn sàng hỏi đáp', color: 'text-green-400', icon: CheckCircle2 },
  failed: { label: 'Xử lý thất bại', color: 'text-red-400', icon: XCircle },
}

const MULTIMEDIA_STAGE_LABELS = {
  queued: 'Đang chờ worker local',
  narrating: 'Đang tạo giọng đọc tiếng Việt',
  rendering_slides: 'Đang dựng slide và phụ đề',
  compositing: 'Đang ghép video MP4',
  completed: 'Video đã sẵn sàng để xem trước',
  failed: 'Không thể tạo video',
}

export default function TeacherUpload() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const requestedCourseId = searchParams.get('course')
  const requestedLessonId = searchParams.get('lesson')
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
  const [videoScriptText, setVideoScriptText] = useState('')
  const [authoringBusy, setAuthoringBusy] = useState('')
  const [assessmentQuestionCount, setAssessmentQuestionCount] = useState('auto')
  const [restoredAuthoringRequest, setRestoredAuthoringRequest] = useState('')
  const videoScriptMetrics = getVideoScriptMetrics(videoScriptText, {
    maxChars: authoring?.video_script_limits?.max_chars,
    maxSegments: authoring?.video_script_limits?.max_segments,
  })
  const videoScriptHasUnsavedChanges = Boolean(
    authoring?.video_script
    && videoScriptText.trim() !== authoring.video_script.text.trim(),
  )
  const videoScriptInTargetRange = (
    videoScriptMetrics.characterCount >= VIDEO_SCRIPT_TARGET_MIN_CHARS
    && videoScriptMetrics.characterCount <= VIDEO_SCRIPT_TARGET_MAX_CHARS
  )
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
    const requestKey = requestedCourseId && requestedLessonId
      ? `${requestedCourseId}:${requestedLessonId}`
      : ''
    if (
      !requestKey
      || String(selectedCourse) !== requestedCourseId
      || restoredAuthoringRequest === requestKey
    ) {
      return undefined
    }

    let cancelled = false
    setRestoredAuthoringRequest(requestKey)
    setAuthoringBusy('status')
    courseService.getLessonAuthoringStatus(requestedLessonId)
      .then((data) => {
        if (cancelled) return
        setAuthoring(data)
        setSummaryText(data.summary?.text || '')
        setVideoScriptText(data.video_script?.text || '')
        setAssessmentQuestionCount('auto')
      })
      .catch((error) => {
        if (!cancelled) {
          toast.error(error.response?.data?.detail || 'Không thể quay lại bài đang biên soạn')
        }
      })
      .finally(() => {
        if (!cancelled) setAuthoringBusy('')
      })

    return () => {
      cancelled = true
    }
  }, [requestedCourseId, requestedLessonId, restoredAuthoringRequest, selectedCourse])

  useEffect(() => {
    if (!authoring?.lesson_id || !['queued', 'running'].includes(authoring.multimedia?.status)) {
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
  }, [authoring?.lesson_id, authoring?.multimedia?.status])

  const fetchCourses = async () => {
    try {
      const data = await courseService.getManagedCourses()
      setCourses(data)
      const requested = data.find(
        (course) => String(course.id) === requestedCourseId,
      )
      if (data.length > 0) setSelectedCourse(requested?.id || data[0].id)
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
      setVideoScriptText(data.video_script?.text || '')
      setAssessmentQuestionCount('auto')
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
      setVideoScriptText(data.video_script?.text || '')
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
    await runAuthoringAction(
      'multimedia',
      () => courseService.generateLessonMultimedia(authoring.lesson_id),
      'Video slide đã được đưa vào hàng đợi local',
    )
  }

  const handleGenerateVideoScript = async () => {
    if (!window.confirm('Tạo kịch bản video 4–5 phút bằng 1 lượt AI? Kết quả vẫn là bản nháp để bạn duyệt.')) return
    await runAuthoringAction(
      'video-script',
      () => courseService.generateLessonVideoScript(authoring.lesson_id),
      'Đã tạo kịch bản video nháp',
    )
  }

  const handleGenerateAssessment = async () => {
    const recommended = authoring.assessment_generation?.recommended_question_count || 5
    const resolvedCount = assessmentQuestionCount === 'auto'
      ? recommended
      : Number(assessmentQuestionCount)
    const providerCalls = resolvedCount / 5
    const confirmed = window.confirm(
      `Tạo ${resolvedCount} câu hỏi qua ${providerCalls} lượt AI? Kết quả vẫn là bản nháp để bạn rà soát.`,
    )
    if (!confirmed) return
    await runAuthoringAction(
      'assessment',
      () => courseService.generateLessonAssessment(
        authoring.lesson_id,
        assessmentQuestionCount,
      ),
      `Đã tạo assessment nháp ${resolvedCount} câu`,
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
            <Upload className="mr-2 h-5 w-5" aria-hidden="true" />Tải Bài Giảng
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
                  <Paperclip className="mr-1 inline h-4 w-4" aria-hidden="true" />{file.name} ({(file.size / (1024 * 1024)).toFixed(1)} MB)
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
            <h2 className="flex items-center gap-2 text-xl font-bold text-white mb-6"><ChartNoAxesCombined className="h-5 w-5" aria-hidden="true" />Trạng thái xử lý</h2>
            <div className="space-y-4">
              {uploadedLessons.map((lesson) => {
                const st = STATUS_MAP[lesson.status] || STATUS_MAP.pending
                const StatusIcon = st.icon
                return (
                  <div
                    key={lesson.id}
                    className="bg-white/5 border border-white/10 rounded-xl p-5 flex items-center gap-4"
                  >
                    <StatusIcon className={`h-6 w-6 ${st.color}`} aria-hidden="true" />
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
                <h3 className="font-semibold">3. Kịch bản video 4–5 phút</h3>
                <p className="mt-1 text-sm text-white/60">
                  Kịch bản dài hơn bản tóm tắt và chỉ được dùng cho slide/Piper. Tạo AI dùng 1 lượt provider; bạn phải duyệt trước khi dựng video.
                </p>
                <Button
                  onClick={handleGenerateVideoScript}
                  disabled={authoring.summary?.status !== 'approved' || Boolean(authoringBusy)}
                  className="mt-3 bg-orange-600 text-white hover:bg-orange-700"
                >
                  {authoringBusy === 'video-script' ? 'Đang tạo...' : authoring.video_script ? 'Tạo lại kịch bản nháp' : 'AI soạn kịch bản 4–5 phút'}
                </Button>
                {authoring.summary?.status !== 'approved' && (
                  <p className="mt-2 text-sm text-amber-200">Hãy duyệt bản tóm tắt trước khi soạn kịch bản video.</p>
                )}
                {authoring.video_script && (
                  <>
                    <textarea
                      value={videoScriptText}
                      onChange={(event) => setVideoScriptText(event.target.value)}
                      maxLength={authoring.video_script_limits?.max_chars || VIDEO_SCRIPT_MAX_CHARS}
                      rows={14}
                      className="mt-3 w-full rounded-lg border border-white/20 bg-black/20 p-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                    <div
                      className={`mt-2 rounded-lg border p-3 text-sm ${
                        videoScriptMetrics.isReady && videoScriptInTargetRange
                          ? 'border-emerald-400/30 bg-emerald-950/30 text-emerald-100'
                          : 'border-amber-400/40 bg-amber-950/30 text-amber-100'
                      }`}
                      role={videoScriptMetrics.isReady && videoScriptInTargetRange ? 'status' : 'alert'}
                    >
                      <p className="font-medium">
                        Video dự kiến: {videoScriptMetrics.segmentCount} đoạn đọc · {videoScriptMetrics.slideCount} slide
                      </p>
                      <p className="mt-1 text-white/70">
                        {videoScriptMetrics.characterCount}/{authoring.video_script_limits?.max_chars || VIDEO_SCRIPT_MAX_CHARS} ký tự · tối đa {authoring.video_script_limits?.max_segments || VIDEO_SCRIPT_MAX_SEGMENTS} đoạn đọc · tốc độ Piper {authoring.video_script_limits?.piper_length_scale || 1.12}x.
                      </p>
                      <p className="mt-1 text-white/70">Mục tiêu video 4–5 phút: khoảng {VIDEO_SCRIPT_TARGET_MIN_CHARS.toLocaleString('vi-VN')}–{VIDEO_SCRIPT_TARGET_MAX_CHARS.toLocaleString('vi-VN')} ký tự.</p>
                      {!videoScriptMetrics.isReady && (
                        <p className="mt-1">Hãy điều chỉnh kịch bản về giới hạn hiển thị trước khi duyệt.</p>
                      )}
                      {videoScriptMetrics.isReady && !videoScriptInTargetRange && (
                        <p className="mt-1">Kịch bản hợp lệ nhưng thời lượng có thể nằm ngoài mục tiêu 4–5 phút.</p>
                      )}
                      {!authoring.video_script.is_current && (
                        <p className="mt-1">Nguồn hoặc bản tóm tắt đã đổi. Hãy tạo lại kịch bản.</p>
                      )}
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-3 text-sm">
                      <span className={authoring.video_script.status === 'approved' ? 'text-emerald-300' : 'text-amber-300'}>
                        {authoring.video_script.status === 'approved' ? 'Đã duyệt' : 'Đang chờ duyệt'}
                      </span>
                      <Button
                        onClick={() => runAuthoringAction('approve-video-script', () => courseService.approveLessonVideoScript(authoring.lesson_id, videoScriptText), 'Đã duyệt kịch bản video')}
                        disabled={!videoScriptMetrics.isReady || !authoring.video_script.is_current || Boolean(authoringBusy)}
                        className="bg-emerald-700 text-white hover:bg-emerald-800"
                      >
                        {authoringBusy === 'approve-video-script' ? 'Đang lưu...' : 'Duyệt kịch bản video'}
                      </Button>
                    </div>
                  </>
                )}
              </div>

              <div className="rounded-xl border border-white/15 p-4">
                <h3 className="font-semibold">4. Assessment nháp</h3>
                <p className="mt-1 text-sm text-white/60">
                  Hệ thống đề xuất số câu theo lượng knowledge chunks và sinh từng batch 5 câu. Assessment luôn là bản nháp để bạn rà soát.
                </p>
                {authoring.assessment ? (
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <span className="text-sm text-white/70">{authoring.assessment.question_count} câu · {authoring.assessment.is_published ? 'Đã publish' : 'Bản nháp'}</span>
                    <Button onClick={() => navigate(`/teacher/assessments?course=${selectedCourse}&lesson=${authoring.lesson_id}`)} className="bg-orange-600 text-white hover:bg-orange-700">Mở trang rà soát</Button>
                  </div>
                ) : (
                  <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,220px)_1fr] sm:items-end">
                    <label className="text-sm font-medium text-white/80">
                      Số câu hỏi
                      <select
                        value={assessmentQuestionCount}
                        onChange={(event) => setAssessmentQuestionCount(event.target.value)}
                        disabled={!authoring.rag_ready || Boolean(authoringBusy)}
                        className="mt-1 block min-h-11 w-full rounded-lg border border-white/20 bg-slate-900 px-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      >
                        <option value="auto">
                          Tự động — {authoring.assessment_generation?.recommended_question_count || 5} câu
                        </option>
                        <option value="5">5 câu</option>
                        <option value="10">10 câu</option>
                        <option value="15">15 câu</option>
                        <option value="20">20 câu</option>
                      </select>
                    </label>
                    <div>
                      <p className="mb-2 text-sm text-white/60">
                        Nguồn hiện có {authoring.assessment_generation?.source_chunk_count || 0} chunks. Mỗi batch tương ứng một lượt gọi provider.
                      </p>
                      <Button
                        onClick={handleGenerateAssessment}
                        disabled={!authoring.rag_ready || Boolean(authoringBusy)}
                        className="bg-orange-600 text-white hover:bg-orange-700"
                      >
                        {authoringBusy === 'assessment' ? 'Đang tạo...' : 'Tạo assessment nháp'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-white/15 p-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="max-w-2xl">
                    <h3 className="font-semibold">5. Video slide với AI Tutor</h3>
                    <p className="mt-1 text-sm text-white/60">
                      Piper đọc tiếng Việt, hệ thống dựng slide và đóng phụ đề bằng FFmpeg. Tất cả chạy local, không dùng API hoặc GPU.
                    </p>
                  </div>
                  <div className="shrink-0 rounded-xl border border-orange-300/30 bg-white p-2">
                    <img
                      src="/images/AI_tutor.png"
                      alt="Avatar AI Tutor sẽ xuất hiện trong video"
                      className="h-20 w-20 object-contain"
                    />
                  </div>
                </div>

                <Button
                  onClick={handleGenerateVideo}
                  disabled={
                    authoring.video_script?.status !== 'approved'
                    || !authoring.video_script?.is_current
                    || videoScriptHasUnsavedChanges
                    || !videoScriptMetrics.isReady
                    || Boolean(authoringBusy)
                    || ['queued', 'running'].includes(authoring.multimedia?.status)
                  }
                  className="mt-4 bg-orange-600 text-white hover:bg-orange-700"
                >
                  {authoringBusy === 'multimedia' ? 'Đang đưa vào hàng đợi...' : authoring.multimedia?.status === 'completed' ? 'Tạo lại video slide' : 'Tạo video slide tiếng Việt'}
                </Button>

                {authoring.video_script?.status !== 'approved' && (
                  <p className="mt-2 text-sm text-amber-200">Hãy tạo và duyệt kịch bản video trước.</p>
                )}
                {authoring.video_script?.status === 'approved' && !videoScriptMetrics.isReady && (
                  <p className="mt-2 text-sm text-amber-200">Kịch bản vượt giới hạn video. Hãy chỉnh và duyệt lại.</p>
                )}

                {authoring.multimedia && (
                  <div className="mt-4 rounded-lg border border-white/10 bg-black/10 p-3 text-sm" aria-live="polite">
                    <p className="font-medium">
                      {MULTIMEDIA_STAGE_LABELS[authoring.multimedia.stage] || authoring.multimedia.stage}
                    </p>
                    {['queued', 'running'].includes(authoring.multimedia.status) && (
                      <p className="mt-1 text-white/60">Bạn có thể rời trang; trạng thái thật được lưu trong hệ thống.</p>
                    )}
                    {authoring.multimedia.safe_error && (
                      <p className="mt-1 text-red-300">{authoring.multimedia.safe_error}</p>
                    )}
                    {authoring.multimedia.status === 'completed' && (
                      <p className="mt-1 text-white/60">
                        {authoring.multimedia.scene_count} slide
                        {authoring.multimedia.duration_seconds ? ` · ${Math.round(Number(authoring.multimedia.duration_seconds))} giây` : ''}
                        {authoring.multimedia.render_duration_ms ? ` · dựng trong ${(authoring.multimedia.render_duration_ms / 1000).toFixed(1)} giây` : ''}
                      </p>
                    )}
                    {authoring.multimedia.video_url && (
                      <video className="mt-3 w-full rounded-lg bg-black" controls preload="metadata" src={authoring.multimedia.video_url}>
                        Trình duyệt không hỗ trợ video.
                      </video>
                    )}
                  </div>
                )}

                {authoring.narration?.audio_url && (
                  <details className="mt-3 text-sm text-white/70">
                    <summary className="cursor-pointer">Nghe riêng giọng đọc tiếng Việt</summary>
                    <audio className="mt-2 w-full" controls preload="metadata" src={authoring.narration.audio_url} />
                  </details>
                )}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
