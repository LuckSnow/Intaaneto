import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import { courseService } from '../services/courseService'
import { aiService } from '../services/aiService'
import toast from 'react-hot-toast'
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Bot,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  FileText,
  MessageCircle,
  Send,
  Sparkles,
  X,
  XCircle,
} from 'lucide-react'
import PdfLessonViewer from '../components/lesson/PdfLessonViewer'

const STATUS_MAP = {
  pending: { label: 'Chờ xử lý', color: 'text-amber-400 border-amber-500/20 bg-amber-500/10', icon: Clock3 },
  extracting: { label: 'Đang trích xuất', color: 'text-sky-400 border-sky-500/20 bg-sky-500/10', icon: FileText },
  summarizing: { label: 'Đang tóm tắt', color: 'text-purple-400 border-purple-500/20 bg-purple-500/10', icon: Bot },
  generating_video: { label: 'Đang tạo video', color: 'text-cyan-400 border-cyan-500/20 bg-cyan-500/10', icon: Bot },
  completed: { label: 'Sẵn sàng', color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10', icon: CheckCircle2 },
  failed: { label: 'Thất bại', color: 'text-rose-400 border-rose-500/20 bg-rose-500/10', icon: XCircle },
}

export default function LessonPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  const [lesson, setLesson] = useState(null)
  const [course, setCourse] = useState(null)
  const [courseNavigationOpen, setCourseNavigationOpen] = useState(true)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('video') // video | summary | comments | chat | assessment

  // Comments
  const [comments, setComments] = useState([])
  const [commentText, setCommentText] = useState('')
  const [replyTo, setReplyTo] = useState(null)
  const [sendingComment, setSendingComment] = useState(false)

  // AI Chat
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatHistoryLoading, setChatHistoryLoading] = useState(false)
  const [chatSessionId, setChatSessionId] = useState(null)
  const chatEndRef = useRef(null)

  // Polling for processing
  const [polling, setPolling] = useState(false)
  const [completion, setCompletion] = useState(null)

  // Deterministic lesson assessment
  const [assessment, setAssessment] = useState(null)
  const [assessmentLoading, setAssessmentLoading] = useState(false)
  const [assessmentAnswers, setAssessmentAnswers] = useState({})
  const [assessmentResult, setAssessmentResult] = useState(null)
  const [assessmentError, setAssessmentError] = useState('')
  const [submittingAssessment, setSubmittingAssessment] = useState(false)
  const [reinforcement, setReinforcement] = useState(null)
  const [reinforcementLoading, setReinforcementLoading] = useState(false)
  const [reinforcementError, setReinforcementError] = useState('')
  const [dialogueQuestionId, setDialogueQuestionId] = useState('')
  const [dialogueAnswer, setDialogueAnswer] = useState('')
  const [dialogueResult, setDialogueResult] = useState(null)
  const [dialogueLoading, setDialogueLoading] = useState(false)
  const [dialogueError, setDialogueError] = useState('')

  useEffect(() => {
    fetchLesson()
  }, [id])

  useEffect(() => {
    if (!isAuthenticated) return

    let cancelled = false
    const fetchChatHistory = async () => {
      setChatHistoryLoading(true)
      try {
        const data = await aiService.getLessonChatHistory(Number(id))
        if (cancelled) return
        setChatSessionId(data.session_id)
        setChatMessages((data.messages || []).map((message) => ({
          id: message.id,
          role: message.role,
          content: message.content,
          citations: message.citations || [],
          grounded: message.grounded,
          retrievalStatus: message.retrieval_status,
        })))
      } catch {
        // Lesson loading owns the visible access error. Chat history failure
        // must not replace the lesson or invent an empty server state.
      } finally {
        if (!cancelled) setChatHistoryLoading(false)
      }
    }
    fetchChatHistory()
    return () => {
      cancelled = true
    }
  }, [id, isAuthenticated])

  useEffect(() => {
    setChatMessages([])
    setChatInput('')
    setChatSessionId(null)
    setCompletion(null)
    setAssessment(null)
    setAssessmentAnswers({})
    setAssessmentResult(null)
    setAssessmentError('')
    setReinforcement(null)
    setReinforcementError('')
    setDialogueQuestionId('')
    setDialogueAnswer('')
    setDialogueResult(null)
    setDialogueError('')
  }, [id])

  useEffect(() => {
    if (user?.role !== 'student') return

    let cancelled = false
    const fetchAssessment = async () => {
      setAssessmentLoading(true)
      try {
        const data = await courseService.getLessonAssessment(id)
        if (!cancelled) {
          setAssessment(data)
          setDialogueQuestionId(data?.questions?.[0]?.id || '')
        }
      } catch (error) {
        if (!cancelled && error.response?.status !== 404) {
          setAssessmentError('Không thể tải bài đánh giá. Vui lòng thử lại.')
        }
      } finally {
        if (!cancelled) setAssessmentLoading(false)
      }
    }
    fetchAssessment()
    return () => {
      cancelled = true
    }
  }, [id, user?.role])

  useEffect(() => {
    if (polling && lesson) {
      const interval = setInterval(async () => {
        try {
          const data = await courseService.getLessonStatus(id)
          if (data.status === 'completed' || data.status === 'failed') {
            setPolling(false)
            fetchLesson()
            if (data.status === 'completed') toast.success('Nội dung bài học đã sẵn sàng!')
          }
          setLesson((prev) => prev && { ...prev, processing_status: data.status })
        } catch {
          /* ignore */
        }
      }, 8000)
      return () => clearInterval(interval)
    }
  }, [polling, lesson, id])

  const fetchLesson = async () => {
    try {
      const data = await courseService.getLesson(id)
      setLesson(data)
      try {
        const courseData = await courseService.getCourse(data.course)
        setCourse(courseData)
      } catch {
        setCourse(null)
      }
      if (data.processing_status && !['completed', 'failed'].includes(data.processing_status)) {
        setPolling(true)
      }
    } catch (error) {
      console.error(error)
      toast.error('Không thể tải bài học')
    } finally {
      setLoading(false)
    }
  }

  const fetchComments = async () => {
    try {
      const data = await courseService.getComments(id)
      setComments(data)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    if (activeTab === 'comments') fetchComments()
  }, [activeTab, id])

  const handleSendComment = async () => {
    if (!commentText.trim()) return
    setSendingComment(true)
    try {
      const payload = { lesson: Number(id), content: commentText.trim() }
      if (replyTo) payload.parent = replyTo.id
      await courseService.addComment(payload)
      setCommentText('')
      setReplyTo(null)
      fetchComments()
    } catch {
      toast.error('Gửi bình luận thất bại')
    } finally {
      setSendingComment(false)
    }
  }

  const handleCompleteLesson = async () => {
    try {
      const result = await courseService.completeLesson(id)
      setCompletion(result)
      toast.success('Đã hoàn thành bài học!')
    } catch (error) {
      if (error.response?.data?.code === 'assessment_required') {
        setActiveTab('assessment')
        toast.error('Bạn cần đạt bài đánh giá trước khi chuyển bài.')
      } else {
        toast.error('Không thể đánh dấu hoàn thành')
      }
    }
  }

  const handleSubmitAssessment = async () => {
    if (!assessment || submittingAssessment) return
    setSubmittingAssessment(true)
    setAssessmentError('')
    try {
      const answers = assessment.questions.map((question) => ({
        question_id: question.id,
        selected_choice: assessmentAnswers[question.id],
      }))
      const result = await courseService.submitAssessment(assessment.id, answers)
      setAssessmentResult(result)
      setReinforcement(null)
      setReinforcementError('')
      if (result.passed) {
        setCompletion({
          is_completed: true,
          progress_percentage: result.progress_percentage,
          next_lesson: result.next_lesson,
        })
        toast.success('Bạn đã đạt bài đánh giá!')
      } else {
        toast.error('Bạn cần củng cố một số mục tiêu trước khi thử lại.')
      }
    } catch (error) {
      setAssessmentError(
        error.response?.data?.answers?.[0]
          || error.response?.data?.detail
          || 'Không thể nộp bài đánh giá. Vui lòng thử lại.'
      )
    } finally {
      setSubmittingAssessment(false)
    }
  }

  const handleLoadReinforcement = async () => {
    if (!assessmentResult?.id || reinforcementLoading) return
    setReinforcementLoading(true)
    setReinforcementError('')
    try {
      const data = await courseService.getAssessmentReinforcement(
        assessment.id,
        assessmentResult.id,
      )
      setReinforcement(data)
    } catch (error) {
      setReinforcementError(
        error.response?.data?.detail
          || 'Không thể tải nội dung củng cố. Vui lòng thử lại.',
      )
    } finally {
      setReinforcementLoading(false)
    }
  }

  const handleAskAboutObjective = (prompt) => {
    setChatInput(prompt)
    setActiveTab('chat')
  }

  const handleDialogueKnowledgeCheck = async () => {
    if (!assessment || !dialogueQuestionId || !dialogueAnswer.trim() || dialogueLoading) return
    setDialogueLoading(true)
    setDialogueError('')
    setDialogueResult(null)
    try {
      const result = await courseService.runDialogueKnowledgeCheck(
        assessment.id,
        Number(dialogueQuestionId),
        dialogueAnswer.trim(),
      )
      setDialogueResult(result)
    } catch (error) {
      setDialogueError(
        error.response?.data?.detail
          || 'Kiểm tra hội thoại tạm thời không khả dụng. Điểm và tiến độ không thay đổi.',
      )
    } finally {
      setDialogueLoading(false)
    }
  }

  // AI Chat
  const handleSendChat = async () => {
    if (!chatInput.trim() || chatLoading || chatHistoryLoading) return
    const question = chatInput.trim()
    setChatInput('')
    setChatMessages((prev) => [...prev, { role: 'user', content: question }])
    setChatLoading(true)
    try {
      const payload = {
        message: question,
        lesson_id: Number(id),
      }
      if (chatSessionId) payload.session_id = chatSessionId
      const data = await aiService.sendMessage(payload)
      setChatSessionId(data.session_id)
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer || data.message?.content || 'Không có phản hồi',
          citations: data.citations || [],
          grounded: data.grounded,
          retrievalStatus: data.retrieval?.status,
        },
      ])
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'AI Tutor tạm thời không khả dụng. Vui lòng thử lại.',
          error: true,
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, chatLoading])

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center" role="status">
        <span className="h-9 w-9 animate-spin rounded-full border-2 border-slate-600 border-t-orange-500" />
        <span className="sr-only">Đang tải bài học</span>
      </div>
    )
  }

  if (!lesson) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4">
        <div className="text-center text-slate-200">
          <h2 className="text-xl font-bold mb-3">Không tìm thấy bài học</h2>
          <Button onClick={() => navigate('/courses')} className="bg-orange-600 hover:bg-orange-700 text-white">
            Quay lại khóa học
          </Button>
        </div>
      </div>
    )
  }

  const st = STATUS_MAP[lesson.processing_status] || STATUS_MAP.pending
  const isReady = lesson.processing_status === 'completed'
  const videoUrl = lesson.video_file || lesson.ai_video_url || lesson.video_url
  const isCompleted = Boolean(completion?.is_completed || lesson.is_completed)

  // Navigation across course lessons
  const lessons = course?.lessons || []
  const currentIndex = lessons.findIndex((l) => String(l.id) === String(id))
  const previousLesson = currentIndex > 0 ? lessons[currentIndex - 1] : null
  const nextLesson = currentIndex >= 0 && currentIndex < lessons.length - 1 ? lessons[currentIndex + 1] : null
  const targetNextLesson = completion?.next_lesson || nextLesson

  return (
    <div className="min-h-screen text-slate-200">
      <div className="mx-auto max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
        {/* Header: Title, metadata, and primary action */}
        <header className="mb-6 border-b border-slate-800/80 pb-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              {/* Metadata row: Course, duration, status */}
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                {course?.title && (
                  <>
                    <span className="font-medium text-slate-300">{course.title}</span>
                    <span className="text-slate-600">•</span>
                  </>
                )}
                {lesson.duration_minutes ? (
                  <>
                    <span className="inline-flex items-center gap-1">
                      <Clock3 className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
                      {lesson.duration_minutes} phút
                    </span>
                    <span className="text-slate-600">•</span>
                  </>
                ) : null}
                <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium ${st.color}`}>
                  <st.icon className="h-3 w-3" aria-hidden="true" />
                  {st.label}
                </span>
                {lesson.rag_ready && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-emerald-400">
                    <Sparkles className="h-3 w-3" aria-hidden="true" />
                    RAG Ready
                  </span>
                )}
              </div>

              <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
                {lesson.title}
              </h1>

              {lesson.description && (
                <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-slate-400">
                  {lesson.description}
                </p>
              )}
            </div>

            {/* Quick Completion Action (Desktop) */}
            {isAuthenticated && (
              <div className="flex shrink-0 items-center gap-2">
                <Button
                  onClick={
                    assessment && !assessment.passed
                      ? () => setActiveTab('assessment')
                      : handleCompleteLesson
                  }
                  disabled={isCompleted}
                  className={`h-9 px-3.5 text-xs font-medium sm:text-sm transition-colors ${
                    isCompleted
                      ? 'border border-emerald-500/30 bg-emerald-500/15 text-emerald-300 cursor-default'
                      : 'bg-emerald-600 text-white hover:bg-emerald-700'
                  }`}
                >
                  {isCompleted ? (
                    <>
                      <CheckCircle2 className="mr-1.5 h-4 w-4" aria-hidden="true" />
                      Đã hoàn thành
                    </>
                  ) : assessment && !assessment.passed ? (
                    'Làm bài đánh giá'
                  ) : (
                    'Đánh dấu hoàn thành'
                  )}
                </Button>

                {targetNextLesson && (
                  <Button
                    onClick={() => navigate(`/lessons/${targetNextLesson.id}`)}
                    className="h-9 px-3 text-xs sm:text-sm font-medium bg-orange-600 hover:bg-orange-700 text-white"
                  >
                    Bài tiếp <ArrowRight className="ml-1 h-3.5 w-3.5" aria-hidden="true" />
                  </Button>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Processing Status Banner (Only when working or failed) */}
        {!isReady && lesson.processing_status && lesson.processing_status !== 'failed' && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/90 p-4" role="status">
            <div className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
            <div className="text-sm">
              <p className="font-medium text-slate-200">{st.label}</p>
              <p className="mt-0.5 text-xs text-slate-400">Hệ thống đang xử lý bài giảng. Trang sẽ tự cập nhật khi hoàn tất.</p>
            </div>
          </div>
        )}

        {lesson.processing_status === 'failed' && (
          <div className="mb-6 rounded-xl border border-rose-900/40 bg-rose-950/25 p-4 text-sm" role="alert">
            <p className="flex items-center gap-2 font-medium text-rose-400">
              <XCircle className="h-4 w-4" aria-hidden="true" /> Xử lý thất bại
            </p>
            {lesson.processing_error && <p className="mt-1 text-xs text-rose-300/80">{lesson.processing_error}</p>}
          </div>
        )}

        {/* Mobile Course Navigator Toggle */}
        <div className="mb-6 lg:hidden">
          <CourseNavigator
            course={course}
            currentLessonId={id}
            isOpen={courseNavigationOpen}
            onToggle={() => setCourseNavigationOpen((open) => !open)}
            onSelectLesson={(lessonId) => navigate(`/lessons/${lessonId}`)}
          />
        </div>

        {/* 2-Column Content Layout (Course Navigator + Main Learning Area) */}
        <div className="grid items-start gap-8 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)]">
          {/* Left Sidebar: Course Navigator (Desktop) */}
          <aside className="sticky top-20 hidden self-start lg:block" aria-label="Điều hướng khóa học">
            <CourseNavigator
              course={course}
              currentLessonId={id}
              isOpen={courseNavigationOpen}
              onToggle={() => setCourseNavigationOpen((open) => !open)}
              onSelectLesson={(lessonId) => navigate(`/lessons/${lessonId}`)}
            />
          </aside>

          {/* Main Learning Surface */}
          <main className="min-w-0 space-y-6">
            {/* Optional Video Player (Only rendered when videoUrl is actually present) */}
            {isReady && videoUrl && (
              <div className="overflow-hidden rounded-xl border border-slate-800 bg-black shadow-sm">
                <div className="aspect-video">
                  <video
                    src={videoUrl}
                    controls
                    autoPlay={false}
                    className="h-full w-full"
                    poster=""
                  >
                    Trình duyệt không hỗ trợ video.
                  </video>
                </div>
              </div>
            )}

            {/* Clean Underline Tabs */}
            <div className="flex border-b border-slate-800 gap-1 overflow-x-auto pb-px" role="tablist" aria-label="Nội dung bài học">
              {[
                { key: 'video', label: 'Nội dung', icon: BookOpen },
                { key: 'summary', label: 'Tóm tắt AI', icon: Bot },
                { key: 'chat', label: 'Hỏi AI', icon: Brain },
                ...(user?.role === 'student' ? [{ key: 'assessment', label: 'Đánh giá', icon: ClipboardCheck }] : []),
                {
                  key: 'comments',
                  label: 'Bình luận',
                  icon: MessageCircle,
                  count: comments.length > 0 ? comments.length : lesson.comments_count,
                },
              ].map((tab) => {
                const isActive = activeTab === tab.key
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    role="tab"
                    aria-selected={isActive}
                    className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? 'border-orange-500 text-orange-400 font-semibold'
                        : 'border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <tab.icon className="h-4 w-4" aria-hidden="true" />
                    <span>{tab.label}</span>
                    {Boolean(tab.count) && tab.count > 0 && (
                      <span className={`rounded-full px-1.5 py-0.2 text-xs ${isActive ? 'bg-orange-500/20 text-orange-300' : 'bg-slate-800 text-slate-400'}`}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Tab Body */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 sm:p-7">
              {/* TAB 1: CONTENT */}
              {activeTab === 'video' && (
                <div>
                  {lesson.uploaded_file ? (
                    <>
                      <PdfLessonViewer key={lesson.uploaded_file} lessonId={lesson.id} pdfUrl={lesson.uploaded_file} title={lesson.title} />
                      {(lesson.content || lesson.learning_content) && (
                        <details className="mt-5 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                          <summary className="cursor-pointer text-sm font-medium text-orange-400 hover:text-orange-300">
                            Xem văn bản đã trích xuất
                          </summary>
                          <div className="mt-4 max-h-[70vh] overflow-auto">
                            <FormattedLessonText text={lesson.content || lesson.learning_content} />
                          </div>
                          {lesson.content_truncated && (
                            <p className="mt-3 text-xs text-amber-300/80">
                              Bản văn bản trên web đã được rút gọn; trình xem PDF phía trên vẫn chứa tài liệu gốc.
                            </p>
                          )}
                        </details>
                      )}
                    </>
                  ) : (lesson.content || lesson.learning_content) ? (
                    <div>
                      <div className="max-h-[80vh] overflow-auto pr-1">
                        <FormattedLessonText text={lesson.content || lesson.learning_content} />
                      </div>
                      {lesson.content_truncated && (
                        <p className="mt-4 text-xs text-amber-300/80">
                          Bản xem trên web đã được rút gọn. Mở tài liệu gốc để đọc toàn bộ học liệu.
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400">Bài học chưa có nội dung văn bản.</p>
                  )}
                </div>
              )}

              {/* TAB 2: AI SUMMARY */}
              {activeTab === 'summary' && (
                <div>
                  <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
                    <Bot className="h-5 w-5 text-orange-400" aria-hidden="true" />
                    Tóm tắt bài giảng bởi AI
                  </h2>
                  {lesson.ai_summary ? (
                    <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                      {lesson.ai_summary}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400">Giảng viên chưa duyệt bản tóm tắt cho bài học này.</p>
                  )}
                </div>
              )}

              {/* TAB 3: AI TUTOR */}
              {activeTab === 'chat' && (
                <div>
                  <div className="mb-4 flex items-center gap-2 text-slate-100">
                    <Brain className="h-5 w-5 text-orange-400" aria-hidden="true" />
                    <h2 className="text-lg font-semibold">AI Tutor theo tài liệu bài học</h2>
                  </div>

                  {/* Chat messages */}
                  <div className="mb-4 h-96 overflow-y-auto space-y-3 pr-2">
                    {chatHistoryLoading && (
                      <p className="py-12 text-center text-xs text-slate-400" role="status">
                        Đang khôi phục hội thoại...
                      </p>
                    )}
                    {!chatHistoryLoading && chatMessages.length === 0 && (
                      <div className="py-14 text-center text-slate-400">
                        <BookOpen className="mx-auto mb-2 h-7 w-7 text-slate-500" aria-hidden="true" />
                        <p className="text-sm font-medium text-slate-300">Đặt câu hỏi về bài giảng</p>
                        <p className="mt-1 text-xs text-slate-500">AI Tutor trả lời dựa trên tài liệu đã được index của bài học.</p>
                      </div>
                    )}
                    {chatMessages.map((msg, i) => (
                      <div
                        key={msg.id || `${msg.role}-${i}`}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
                            msg.role === 'user'
                              ? 'border border-orange-500/30 bg-orange-600/15 text-orange-100'
                              : 'border border-slate-800 bg-slate-950/70 text-slate-200'
                          }`}
                        >
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                          {msg.role === 'assistant' && msg.grounded === true && (
                            <div className="mt-2.5 flex items-center gap-1 text-xs text-emerald-400">
                              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>Dựa trên tài liệu bài học</span>
                            </div>
                          )}

                          {msg.role === 'assistant' && msg.grounded === false && (
                            <div className="mt-2.5 flex items-center gap-1 text-xs text-amber-300">
                              <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>
                                {msg.retrievalStatus === 'not_indexed'
                                  ? 'Bài học chưa được index'
                                  : 'Chưa đủ bằng chứng trong tài liệu'}
                              </span>
                            </div>
                          )}

                          {msg.error && (
                            <div className="mt-2.5 flex items-center gap-1 text-xs text-rose-400">
                              <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>Không thể hoàn thành yêu cầu</span>
                            </div>
                          )}

                          {msg.citations?.length > 0 && (
                            <details className="mt-3 border-t border-slate-800 pt-2.5">
                              <summary className="cursor-pointer text-xs font-medium text-orange-400 hover:text-orange-300">
                                {msg.citations.length} nguồn trích dẫn
                              </summary>
                              <ol className="mt-2 space-y-2">
                                {msg.citations.map((citation) => (
                                  <li
                                    key={citation.id}
                                    className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5"
                                  >
                                    <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
                                      <BookOpen className="h-3.5 w-3.5 text-orange-400" aria-hidden="true" />
                                      <span>
                                        {citation.lesson_title} ·{' '}
                                        {citation.location?.page_start
                                          ? citation.location.page_start === citation.location.page_end
                                            ? `Trang ${citation.location.page_start}`
                                            : `Trang ${citation.location.page_start}–${citation.location.page_end}`
                                          : `Đoạn ${citation.ordinal + 1}`}
                                      </span>
                                    </div>
                                    <p className="mt-1 whitespace-pre-wrap text-xs leading-relaxed text-slate-400">
                                      {citation.excerpt}
                                    </p>
                                  </li>
                                ))}
                              </ol>
                            </details>
                          )}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                          <div className="flex gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" />
                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.1s]" />
                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]" />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat input */}
                  <div className="flex gap-2">
                    <input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendChat()}
                      placeholder="Hỏi AI về bài giảng này..."
                      disabled={chatHistoryLoading}
                      className="flex-1 rounded-lg border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                    />
                    <Button
                      onClick={handleSendChat}
                      disabled={chatLoading || chatHistoryLoading || !chatInput.trim()}
                      className="h-10 px-4 rounded-lg bg-orange-600 hover:bg-orange-700 text-white"
                      aria-label="Gửi câu hỏi"
                    >
                      {chatLoading ? '...' : <Send className="h-4 w-4" aria-hidden="true" />}
                    </Button>
                  </div>
                </div>
              )}

              {/* TAB 4: ASSESSMENT */}
              {activeTab === 'assessment' && (
                <div>
                  <div className="mb-4 flex items-center gap-2 text-slate-100">
                    <ClipboardCheck className="h-5 w-5 text-orange-400" aria-hidden="true" />
                    <h2 className="text-lg font-semibold">Kiểm tra mức độ tiếp thu</h2>
                  </div>

                  {assessmentLoading && (
                    <p className="text-sm text-slate-400" role="status">Đang tải bài đánh giá...</p>
                  )}

                  {!assessmentLoading && !assessment && !assessmentError && (
                    <p className="text-sm text-slate-400">
                      Bài học này chưa có bài đánh giá. Bạn có thể đánh dấu hoàn thành khi đã học xong.
                    </p>
                  )}

                  {assessmentError && (
                    <div className="mb-4 rounded-lg border border-rose-900/40 bg-rose-950/25 p-3 text-sm text-rose-300" role="alert">
                      {assessmentError}
                    </div>
                  )}

                  {assessment && (
                    <div className="space-y-5">
                      <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                        <h3 className="font-semibold text-slate-100 text-sm sm:text-base">{assessment.title}</h3>
                        {assessment.instructions && (
                          <p className="mt-1 text-xs text-slate-400">{assessment.instructions}</p>
                        )}
                        <p className="mt-2 text-xs font-medium text-orange-400">
                          Ngưỡng đạt: {assessment.pass_threshold}%
                        </p>
                      </div>

                      {assessment.questions.map((question, questionIndex) => (
                        <fieldset key={question.id} className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
                          <legend className="px-1 text-sm font-medium text-slate-200">
                            Câu {questionIndex + 1}: {question.prompt}
                          </legend>
                          <div className="mt-3 space-y-2">
                            {question.choices.map((choice, choiceIndex) => (
                              <label
                                key={choiceIndex}
                                className="flex min-h-10 cursor-pointer items-center gap-3 rounded-md border border-slate-800/80 px-3 py-2 text-xs sm:text-sm text-slate-300 hover:bg-slate-800/50"
                              >
                                <input
                                  type="radio"
                                  name={`question-${question.id}`}
                                  value={choiceIndex}
                                  checked={assessmentAnswers[question.id] === choiceIndex}
                                  onChange={() => setAssessmentAnswers((current) => ({
                                    ...current,
                                    [question.id]: choiceIndex,
                                  }))}
                                  disabled={submittingAssessment}
                                  className="h-4 w-4 accent-orange-500"
                                />
                                <span>{choice}</span>
                              </label>
                            ))}
                          </div>
                        </fieldset>
                      ))}

                      {assessmentResult && (
                        <div
                          className={`rounded-lg border p-4 text-sm ${
                            assessmentResult.passed
                              ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-200'
                              : 'border-amber-500/30 bg-amber-950/20 text-amber-200'
                          }`}
                          role="status"
                        >
                          <p className="font-semibold">
                            {assessmentResult.passed ? 'Đã đạt' : 'Cần củng cố'} · {assessmentResult.score}%
                          </p>
                          {!assessmentResult.passed && assessmentResult.weak_objectives?.length > 0 && (
                            <div className="mt-2 text-xs sm:text-sm">
                              <p className="text-slate-300">Mục tiêu cần ôn lại:</p>
                              <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-400">
                                {assessmentResult.weak_objectives.map((objective) => (
                                  <li key={objective}>{objective}</li>
                                ))}
                              </ul>
                              <Button
                                onClick={handleLoadReinforcement}
                                disabled={reinforcementLoading}
                                className="mt-3 bg-amber-700 text-white hover:bg-amber-800 text-xs"
                              >
                                {reinforcementLoading
                                  ? 'Đang tìm học liệu...'
                                  : reinforcement ? 'Tải lại học liệu củng cố' : 'Ôn theo tài liệu bài học'}
                              </Button>
                            </div>
                          )}
                        </div>
                      )}

                      {reinforcementError && (
                        <div className="rounded-lg border border-rose-900/40 bg-rose-950/25 p-3 text-xs text-rose-300" role="alert">
                          {reinforcementError}
                        </div>
                      )}

                      {reinforcement && (
                        <div className="space-y-3" aria-label="Học liệu củng cố">
                          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3.5">
                            <h3 className="text-sm font-semibold text-slate-100">Học liệu củng cố theo mục tiêu</h3>
                            <p className="mt-1 text-xs text-slate-400">
                              Các đoạn trích xuất dưới đây được đối chiếu từ tài liệu bài học.
                            </p>
                          </div>

                          {reinforcement.items.map((item) => (
                            <section
                              key={item.learning_objective}
                              className="rounded-lg border border-slate-800 bg-slate-950/40 p-3.5"
                            >
                              <h4 className="text-xs sm:text-sm font-medium text-slate-200">{item.learning_objective}</h4>
                              <p className="mt-1 text-xs text-slate-400">{item.message}</p>

                              {item.citations.length > 0 ? (
                                <ol className="mt-2.5 space-y-2">
                                  {item.citations.map((citation) => (
                                    <li
                                      key={citation.id}
                                      className="rounded border border-slate-800 bg-slate-900/60 p-2.5 text-xs text-slate-300"
                                    >
                                      <p className="font-medium text-orange-300">
                                        {citation.lesson_title} ·{' '}
                                        {citation.location?.page_start
                                          ? citation.location.page_start === citation.location.page_end
                                            ? `Trang ${citation.location.page_start}`
                                            : `Trang ${citation.location.page_start}–${citation.location.page_end}`
                                          : `Đoạn ${citation.ordinal + 1}`}
                                      </p>
                                      <p className="mt-1 leading-relaxed text-slate-400">
                                        {citation.excerpt}
                                      </p>
                                    </li>
                                  ))}
                                </ol>
                              ) : (
                                <p className="mt-2 text-xs text-amber-300/80">
                                  {item.status === 'not_indexed'
                                    ? 'Bài học chưa được lập chỉ mục RAG.'
                                    : 'Chưa có đoạn tài liệu đủ liên quan để gợi ý.'}
                                </p>
                              )}

                              <Button
                                onClick={() => handleAskAboutObjective(item.tutor_prompt)}
                                className="mt-2.5 border border-slate-700 bg-slate-800/80 text-xs text-slate-200 hover:bg-slate-800"
                              >
                                Hỏi AI Tutor về mục tiêu này
                              </Button>
                            </section>
                          ))}
                        </div>
                      )}

                      {!assessmentResult?.passed && (
                        <Button
                          onClick={handleSubmitAssessment}
                          disabled={
                            submittingAssessment
                            || Object.keys(assessmentAnswers).length !== assessment.questions.length
                          }
                          className="w-full bg-orange-600 text-white hover:bg-orange-700"
                        >
                          {submittingAssessment
                            ? 'Đang chấm bài...'
                            : assessmentResult ? 'Làm lại bài đánh giá' : 'Nộp bài đánh giá'}
                        </Button>
                      )}

                      {(assessment.passed || assessmentResult?.passed) && (
                        <section className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                          <div className="flex items-start gap-3">
                            <Bot className="mt-0.5 h-4 w-4 text-orange-400" aria-hidden="true" />
                            <div>
                              <h3 className="text-sm font-semibold text-slate-100">Tự luyện tập với hội thoại AI</h3>
                              <p className="mt-0.5 text-xs text-slate-400">
                                Khuyến nghị kiểm tra sau bài trắc nghiệm (không ảnh hưởng điểm).
                              </p>
                            </div>
                          </div>

                          <label htmlFor="dialogue-question" className="mt-3 block text-xs font-medium text-slate-300">
                            Câu hỏi
                          </label>
                          <select
                            id="dialogue-question"
                            value={dialogueQuestionId}
                            onChange={(event) => {
                              setDialogueQuestionId(event.target.value)
                              setDialogueResult(null)
                            }}
                            disabled={dialogueLoading}
                            className="mt-1 min-h-10 w-full rounded-md border border-slate-800 bg-slate-900 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500"
                          >
                            {assessment.questions.map((question) => (
                              <option key={question.id} value={question.id}>{question.prompt}</option>
                            ))}
                          </select>

                          <label htmlFor="dialogue-answer" className="mt-3 block text-xs font-medium text-slate-300">
                            Trả lời bằng từ ngữ của bạn
                          </label>
                          <textarea
                            id="dialogue-answer"
                            value={dialogueAnswer}
                            onChange={(event) => setDialogueAnswer(event.target.value)}
                            disabled={dialogueLoading}
                            maxLength={2000}
                            rows={3}
                            className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                            placeholder="Giải thích ngắn gọn ý hiểu của bạn..."
                          />
                          <Button
                            onClick={handleDialogueKnowledgeCheck}
                            disabled={dialogueLoading || !dialogueQuestionId || !dialogueAnswer.trim()}
                            className="mt-2.5 bg-orange-600 text-xs text-white hover:bg-orange-700"
                          >
                            {dialogueLoading ? 'Đang đối chiếu...' : 'Nhận nhận xét'}
                          </Button>

                          {dialogueError && (
                            <p className="mt-2 text-xs text-rose-300" role="alert">{dialogueError}</p>
                          )}

                          {dialogueResult && (
                            <div className="mt-3 rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-xs" role="status">
                              <p className="font-medium text-orange-300">
                                Kết quả: {
                                  dialogueResult.outcome === 'demonstrated'
                                    ? 'Đã hiểu rõ'
                                    : dialogueResult.outcome === 'partial'
                                      ? 'Hiểu một phần'
                                      : 'Chưa thể hiện rõ'
                                }
                              </p>
                              <p className="mt-1 text-slate-300">{dialogueResult.feedback}</p>
                              <p className="mt-1 text-slate-400">Gợi ý: {dialogueResult.next_step}</p>
                            </div>
                          )}
                        </section>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: COMMENTS */}
              {activeTab === 'comments' && (
                <div>
                  <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
                    <MessageCircle className="h-5 w-5 text-orange-400" aria-hidden="true" />
                    Thảo luận ({comments.length})
                  </h2>

                  {/* Comment input */}
                  {isAuthenticated && (
                    <div className="mb-6">
                      {replyTo && (
                        <div className="mb-2 flex items-center gap-2 text-xs text-slate-400">
                          <span>Trả lời {replyTo.user_name}:</span>
                          <button onClick={() => setReplyTo(null)} className="text-rose-400 hover:text-rose-300">
                            <X className="mr-0.5 inline h-3.5 w-3.5" aria-hidden="true" /> Hủy
                          </button>
                        </div>
                      )}
                      <div className="flex gap-2">
                        <input
                          value={commentText}
                          onChange={(e) => setCommentText(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendComment()}
                          placeholder="Viết bình luận..."
                          className="flex-1 rounded-lg border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                        />
                        <Button
                          onClick={handleSendComment}
                          disabled={sendingComment || !commentText.trim()}
                          className="rounded-lg bg-orange-600 px-5 text-sm text-white hover:bg-orange-700"
                        >
                          {sendingComment ? '...' : 'Gửi'}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Comments list */}
                  {comments.length === 0 ? (
                    <p className="py-8 text-center text-xs text-slate-500">Chưa có bình luận nào.</p>
                  ) : (
                    <div className="space-y-3">
                      {comments.map((c) => (
                        <CommentItem key={c.id} comment={c} onReply={setReplyTo} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Bottom Step-by-Step Navigation Bar */}
              <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-6">
                {previousLesson ? (
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/lessons/${previousLesson.id}`)}
                    className="border-slate-800 bg-slate-950 text-xs sm:text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    <ChevronLeft className="mr-1 h-4 w-4" aria-hidden="true" />
                    <span>Bài trước</span>
                  </Button>
                ) : (
                  <div />
                )}

                <div className="flex items-center gap-2">
                  {isAuthenticated && !isCompleted && (
                    <Button
                      onClick={
                        assessment && !assessment.passed
                          ? () => setActiveTab('assessment')
                          : handleCompleteLesson
                      }
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-medium"
                    >
                      <CheckCircle2 className="mr-1.5 h-4 w-4" aria-hidden="true" />
                      {assessment && !assessment.passed ? 'Làm bài đánh giá' : 'Đánh dấu hoàn thành'}
                    </Button>
                  )}

                  {targetNextLesson && (
                    <Button
                      onClick={() => navigate(`/lessons/${targetNextLesson.id}`)}
                      className="bg-orange-600 hover:bg-orange-700 text-white text-xs sm:text-sm font-medium"
                    >
                      <span>Bài tiếp theo</span>
                      <ChevronRight className="ml-1 h-4 w-4" aria-hidden="true" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

/* ---------- Course Navigator Sidebar Component ---------- */
function CourseNavigator({ course, currentLessonId, isOpen, onToggle, onSelectLesson }) {
  const lessons = course?.lessons || []

  return (
    <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/90 text-slate-200">
      <div className="border-b border-slate-800 p-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-orange-400">Khóa học</p>
        <h2 className="mt-1 font-semibold text-slate-100 text-base line-clamp-2">{course?.title || 'Đang tải...'}</h2>
        <p className="mt-1 text-xs text-slate-400">{lessons.length} bài học</p>
      </div>

      <button
        type="button"
        onClick={onToggle}
        className="flex min-h-10 w-full items-center justify-between border-b border-slate-800 px-4 py-2.5 text-left text-xs font-medium text-slate-300 hover:bg-slate-800/50 lg:hidden"
        aria-expanded={isOpen}
      >
        <span>Danh sách bài học</span>
        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <div className={`${isOpen ? 'block' : 'hidden'} lg:block`}>
        <ol className="max-h-[calc(100vh-14rem)] overflow-y-auto divide-y divide-slate-800/60 py-1">
          {lessons.map((courseLesson, index) => {
            const isCurrent = String(courseLesson.id) === String(currentLessonId)
            const padIndex = String(index + 1).padStart(2, '0')
            return (
              <li key={courseLesson.id}>
                <button
                  type="button"
                  onClick={() => onSelectLesson(courseLesson.id)}
                  aria-current={isCurrent ? 'step' : undefined}
                  className={`flex min-h-12 w-full items-start gap-3 px-4 py-3 text-left transition-colors ${
                    isCurrent
                      ? 'bg-orange-500/10 border-l-2 border-orange-500 text-slate-100'
                      : 'border-l-2 border-transparent text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                  }`}
                >
                  <span className={`text-xs font-mono mt-0.5 ${isCurrent ? 'text-orange-400 font-semibold' : 'text-slate-500'}`}>
                    {padIndex}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className={`text-sm leading-snug line-clamp-2 ${isCurrent ? 'font-medium text-slate-100' : 'text-slate-300'}`}>
                      {courseLesson.title}
                    </p>
                    {courseLesson.duration_minutes > 0 && (
                      <span className="mt-1 inline-flex items-center gap-1 text-[11px] text-slate-500">
                        <Clock3 className="h-3 w-3" aria-hidden="true" /> {courseLesson.duration_minutes} phút
                      </span>
                    )}
                  </div>
                </button>
              </li>
            )
          })}
          {!course && <li className="p-4 text-xs text-slate-500">Đang tải danh sách bài...</li>}
          {course && lessons.length === 0 && <li className="p-4 text-xs text-slate-500">Chưa có bài học.</li>}
        </ol>
      </div>
    </section>
  )
}

/* ---------- Formatted Lesson Text Component ---------- */
function FormattedLessonText({ text }) {
  if (!text) return null
  // Strip corpus metadata comments (e.g., <!-- intaaneto-learning-corpus:... -->)
  const cleaned = text.replace(/^<!--[\s\S]*?-->\s*/, '').trim()

  const lines = cleaned.split('\n')
  const elements = []
  let listItems = []

  const flushList = (key) => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${key}`} className="my-3 space-y-1.5 pl-5 list-disc text-slate-300">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed text-sm">{item}</li>
          ))}
        </ul>
      )
      listItems = []
    }
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim()
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      listItems.push(trimmed.slice(2).trim())
    } else {
      flushList(index)
      if (!trimmed) {
        // empty space
      } else if (trimmed.startsWith('# ')) {
        elements.push(
          <h2 key={index} className="mt-6 mb-3 text-xl font-bold tracking-tight text-slate-100 first:mt-0">
            {trimmed.slice(2)}
          </h2>
        )
      } else if (trimmed.startsWith('## ')) {
        elements.push(
          <h3 key={index} className="mt-5 mb-2 text-base font-semibold tracking-tight text-slate-100">
            {trimmed.slice(3)}
          </h3>
        )
      } else if (trimmed.startsWith('### ')) {
        elements.push(
          <h4 key={index} className="mt-4 mb-2 text-sm font-semibold text-slate-200">
            {trimmed.slice(4)}
          </h4>
        )
      } else {
        elements.push(
          <p key={index} className="my-2.5 text-sm leading-relaxed text-slate-300">
            {trimmed}
          </p>
        )
      }
    }
  })
  flushList('final')

  return <div className="space-y-1">{elements}</div>
}

/* ---------- Comment Item Component ---------- */
function CommentItem({ comment, onReply }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-xs font-bold text-orange-300">
          {comment.user_name?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-medium text-slate-200">{comment.user_name}</span>
            <span className="text-slate-500">
              {comment.created_at ? new Date(comment.created_at).toLocaleDateString('vi-VN') : ''}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-300 whitespace-pre-wrap">{comment.content}</p>
          <button
            onClick={() => onReply({ id: comment.id, user_name: comment.user_name })}
            className="mt-2 text-xs text-orange-400 hover:text-orange-300"
          >
            Trả lời
          </button>

          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 space-y-3 border-l border-slate-800 pl-4">
              {comment.replies.map((r) => (
                <div key={r.id} className="flex items-start gap-2.5">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-800 text-[11px] font-bold text-slate-300">
                    {r.user_name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-medium text-slate-200">{r.user_name}</span>
                      <span className="text-slate-500">
                        {r.created_at ? new Date(r.created_at).toLocaleDateString('vi-VN') : ''}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-300">{r.content}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
