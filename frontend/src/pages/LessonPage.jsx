import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import { courseService } from '../services/courseService'
import { aiService } from '../services/aiService'
import toast from 'react-hot-toast'
import { AlertCircle, ArrowRight, BookOpen, Bot, CheckCircle2, ClipboardCheck, Send } from 'lucide-react'

const STATUS_MAP = {
  pending: { label: 'Chờ xử lý', color: 'text-yellow-400', icon: '⏳' },
  extracting: { label: 'Đang trích xuất văn bản...', color: 'text-blue-400', icon: '📄' },
  summarizing: { label: 'AI đang tóm tắt...', color: 'text-purple-400', icon: '🤖' },
  generating_video: { label: 'Đang tạo video AI...', color: 'text-cyan-400', icon: '🎬' },
  completed: { label: 'Sẵn sàng', color: 'text-green-400', icon: '✅' },
  failed: { label: 'Thất bại', color: 'text-red-400', icon: '❌' },
}

export default function LessonPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('video') // video | summary | comments | chat

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
            if (data.status === 'completed') toast.success('Video AI đã sẵn sàng!')
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

  // Fetch comments when tab is opened
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500" />
      </div>
    )
  }

  if (!lesson) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Không tìm thấy bài học</h2>
          <Button onClick={() => navigate('/courses')} className="bg-gradient-to-r from-orange-500 to-red-500">
            Quay lại
          </Button>
        </div>
      </div>
    )
  }

  const st = STATUS_MAP[lesson.processing_status] || STATUS_MAP.pending
  const isReady = lesson.processing_status === 'completed'
  const videoUrl = lesson.video_file || lesson.ai_video_url || lesson.video_url

  return (
    <div className="min-h-screen">
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      />

      <div className="max-w-7xl mx-auto px-4 py-8 pt-24">
        {/* Back link + title */}
        <div className="mb-6 flex items-center gap-4">
          <Link
            to={lesson.course ? `/courses/${lesson.course}` : '/courses'}
            className="text-white/60 hover:text-white transition text-sm"
          >
            ← Quay lại khóa học
          </Link>
        </div>

        <h1
          className="text-3xl font-bold text-white mb-2"
          style={{ textShadow: '0 0 20px rgba(249,115,22,0.5)' }}
        >
          {lesson.title}
        </h1>
        {lesson.description && <p className="text-white/60 mb-6">{lesson.description}</p>}

        {/* Processing Status Banner */}
        {!isReady && lesson.processing_status && lesson.processing_status !== 'failed' && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 mb-6 flex items-center gap-4">
            <div className="animate-spin h-8 w-8 border-2 border-orange-400 border-t-transparent rounded-full" />
            <div>
              <p className={`font-semibold ${st.color}`}>
                {st.icon} {st.label}
              </p>
              <p className="text-white/50 text-sm">AI đang xử lý bài giảng. Trang sẽ tự cập nhật khi hoàn tất.</p>
            </div>
          </div>
        )}

        {lesson.processing_status === 'failed' && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-6">
            <p className="text-red-400 font-semibold">❌ Xử lý thất bại</p>
            {lesson.processing_error && <p className="text-red-300/70 text-sm mt-1">{lesson.processing_error}</p>}
          </div>
        )}

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Video + Tabs */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Player */}
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl overflow-hidden">
              {isReady && videoUrl ? (
                <div className="aspect-video bg-black">
                  <video
                    src={videoUrl}
                    controls
                    autoPlay={false}
                    className="w-full h-full"
                    poster=""
                  >
                    Trình duyệt không hỗ trợ video.
                  </video>
                </div>
              ) : (
                <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                  <div className="text-center">
                    <span className="text-6xl block mb-4">{st.icon}</span>
                    <p className={`text-lg font-semibold ${st.color}`}>{st.label}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="flex gap-2 flex-wrap">
              {[
                { key: 'video', label: '📖 Nội dung' },
                { key: 'summary', label: '🤖 Tóm tắt AI' },
                { key: 'comments', label: '💬 Bình luận' },
                { key: 'chat', label: '🧠 Hỏi AI' },
                ...(user?.role === 'student' ? [{ key: 'assessment', label: 'Bài đánh giá' }] : []),
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    activeTab === tab.key
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/25'
                      : 'bg-white/10 border border-white/20 text-white/70 hover:bg-white/20'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
              {activeTab === 'video' && (
                <div>
                  <h2 className="text-xl font-bold text-white mb-4">Nội dung bài giảng</h2>
                  {(lesson.content || lesson.learning_content) ? (
                    <>
                      <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                        {lesson.content || lesson.learning_content}
                      </div>
                      {lesson.content_truncated && (
                        <p className="mt-4 text-sm text-amber-200">
                          Bản xem trên web đã được rút gọn. Mở PDF để đọc toàn bộ học liệu.
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-white/50">Bài học chưa có nội dung có thể đọc.</p>
                  )}
                  {lesson.uploaded_file && (
                    <a href={lesson.uploaded_file} target="_blank" rel="noreferrer" className="mt-4 inline-block text-sm font-medium text-orange-300 underline">
                      Mở file PDF gốc
                    </a>
                  )}
                  {lesson.rag_ready && (
                    <p className="mt-3 text-sm text-emerald-300">Kho kiến thức RAG đã sẵn sàng cho AI Tutor.</p>
                  )}
                </div>
              )}

              {activeTab === 'summary' && (
                <div>
                  <h2 className="text-xl font-bold text-white mb-4">🤖 Tóm tắt bởi AI</h2>
                  {lesson.ai_summary ? (
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">{lesson.ai_summary}</div>
                  ) : (
                    <p className="text-white/50">Giảng viên chưa duyệt bản tóm tắt cho bài học này.</p>
                  )}
                </div>
              )}

              {activeTab === 'comments' && (
                <div>
                  <h2 className="text-xl font-bold text-white mb-4">💬 Bình luận</h2>

                  {/* Comment input */}
                  {isAuthenticated && (
                    <div className="mb-6">
                      {replyTo && (
                        <div className="flex items-center gap-2 mb-2 text-sm text-white/60">
                          <span>Trả lời {replyTo.user_name}:</span>
                          <button onClick={() => setReplyTo(null)} className="text-red-400 hover:text-red-300">
                            ✕ Hủy
                          </button>
                        </div>
                      )}
                      <div className="flex gap-3">
                        <input
                          value={commentText}
                          onChange={(e) => setCommentText(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendComment()}
                          placeholder="Viết bình luận..."
                          className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-orange-500/50 transition"
                        />
                        <Button
                          onClick={handleSendComment}
                          disabled={sendingComment || !commentText.trim()}
                          className="bg-orange-500 hover:bg-orange-600 text-white rounded-xl px-6 border-0"
                        >
                          {sendingComment ? '...' : 'Gửi'}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Comment list */}
                  {comments.length === 0 ? (
                    <p className="text-white/50 text-center py-6">Chưa có bình luận nào. Hãy là người đầu tiên!</p>
                  ) : (
                    <div className="space-y-4">
                      {comments.map((c) => (
                        <CommentItem key={c.id} comment={c} onReply={setReplyTo} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'chat' && (
                <div>
                  <div className="mb-4 flex items-center gap-2 text-white">
                    <Bot className="h-5 w-5 text-orange-300" aria-hidden="true" />
                    <h2 className="text-xl font-bold">AI Tutor theo tài liệu</h2>
                  </div>

                  {/* Chat messages */}
                  <div className="h-80 overflow-y-auto mb-4 space-y-3 pr-2 custom-scrollbar">
                    {chatHistoryLoading && (
                      <p className="py-10 text-center text-sm text-white/50" role="status">
                        Đang khôi phục cuộc trò chuyện...
                      </p>
                    )}
                    {!chatHistoryLoading && chatMessages.length === 0 && (
                      <div className="text-center py-10 text-white/40">
                        <BookOpen className="mx-auto mb-3 h-8 w-8" aria-hidden="true" />
                        <p>Đặt câu hỏi về nội dung đã được index của bài học.</p>
                      </div>
                    )}
                    {chatMessages.map((msg, i) => (
                      <div
                        key={msg.id || `${msg.role}-${i}`}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm ${
                            msg.role === 'user'
                              ? 'bg-orange-500/30 border border-orange-500/40 text-white'
                              : 'bg-white/10 border border-white/20 text-white/90'
                          }`}
                        >
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                          {msg.role === 'assistant' && msg.grounded === true && (
                            <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-300">
                              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                              <span>Dựa trên tài liệu bài học</span>
                            </div>
                          )}

                          {msg.role === 'assistant' && msg.grounded === false && (
                            <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-300">
                              <AlertCircle className="h-4 w-4" aria-hidden="true" />
                              <span>
                                {msg.retrievalStatus === 'not_indexed'
                                  ? 'Bài học chưa được index'
                                  : 'Chưa đủ bằng chứng trong tài liệu'}
                              </span>
                            </div>
                          )}

                          {msg.error && (
                            <div className="mt-3 flex items-center gap-1.5 text-xs text-red-300">
                              <AlertCircle className="h-4 w-4" aria-hidden="true" />
                              <span>Không thể hoàn thành yêu cầu</span>
                            </div>
                          )}

                          {msg.citations?.length > 0 && (
                            <details className="mt-3 border-t border-white/10 pt-3">
                              <summary className="cursor-pointer text-xs font-medium text-orange-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400">
                                {msg.citations.length} nguồn tham khảo
                              </summary>
                              <ol className="mt-2 space-y-2">
                                {msg.citations.map((citation) => (
                                  <li
                                    key={citation.id}
                                    className="rounded-lg border border-white/10 bg-black/10 p-2.5"
                                  >
                                    <div className="flex items-center gap-1.5 text-xs font-medium text-white/80">
                                      <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                                      <span>
                                        {citation.lesson_title} ·{' '}
                                        {citation.location?.page_start
                                          ? citation.location.page_start === citation.location.page_end
                                            ? `Trang ${citation.location.page_start}`
                                            : `Trang ${citation.location.page_start}–${citation.location.page_end}`
                                          : `Đoạn ${citation.ordinal + 1}`}
                                      </span>
                                    </div>
                                    <p className="mt-1.5 whitespace-pre-wrap text-xs leading-relaxed text-white/60">
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
                        <div className="bg-white/10 border border-white/20 px-4 py-3 rounded-2xl">
                          <div className="flex gap-1">
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" />
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce [animation-delay:0.1s]" />
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce [animation-delay:0.2s]" />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat input */}
                  <div className="flex gap-3">
                    <input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendChat()}
                      placeholder="Hỏi AI về bài giảng này..."
                      disabled={chatHistoryLoading}
                      className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-orange-500/50 transition"
                    />
                    <Button
                      onClick={handleSendChat}
                      disabled={chatLoading || chatHistoryLoading || !chatInput.trim()}
                      className="bg-orange-600 hover:bg-orange-700 text-white rounded-xl px-5 border-0"
                      aria-label="Gửi câu hỏi"
                    >
                      {chatLoading ? '...' : <Send className="h-4 w-4" aria-hidden="true" />}
                    </Button>
                  </div>
                </div>
              )}

              {activeTab === 'assessment' && (
                <div>
                  <div className="mb-4 flex items-center gap-2 text-white">
                    <ClipboardCheck className="h-5 w-5 text-orange-300" aria-hidden="true" />
                    <h2 className="text-xl font-bold">Kiểm tra mức độ tiếp thu</h2>
                  </div>

                  {assessmentLoading && (
                    <p className="text-white/60" role="status">Đang tải bài đánh giá...</p>
                  )}

                  {!assessmentLoading && !assessment && !assessmentError && (
                    <p className="text-white/60">
                      Bài học này chưa có bài đánh giá. Bạn có thể đánh dấu hoàn thành khi đã học xong.
                    </p>
                  )}

                  {assessmentError && (
                    <div className="mb-4 rounded-xl border border-red-400/40 bg-red-500/10 p-4 text-sm text-red-200" role="alert">
                      {assessmentError}
                    </div>
                  )}

                  {assessment && (
                    <div className="space-y-5">
                      <div className="rounded-xl border border-white/15 bg-black/10 p-4">
                        <h3 className="font-semibold text-white">{assessment.title}</h3>
                        {assessment.instructions && (
                          <p className="mt-1 text-sm text-white/60">{assessment.instructions}</p>
                        )}
                        <p className="mt-2 text-sm text-orange-200">
                          Ngưỡng đạt: {assessment.pass_threshold}%
                        </p>
                      </div>

                      {assessment.questions.map((question, questionIndex) => (
                        <fieldset key={question.id} className="rounded-xl border border-white/15 p-4">
                          <legend className="px-1 font-medium text-white">
                            Câu {questionIndex + 1}: {question.prompt}
                          </legend>
                          <div className="mt-3 space-y-2">
                            {question.choices.map((choice, choiceIndex) => (
                              <label
                                key={choiceIndex}
                                className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-white/10 px-3 py-2 text-sm text-white/80 hover:bg-white/5"
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
                                  className="h-4 w-4 accent-orange-600"
                                />
                                <span>{choice}</span>
                              </label>
                            ))}
                          </div>
                        </fieldset>
                      ))}

                      {assessmentResult && (
                        <div
                          className={`rounded-xl border p-4 ${
                            assessmentResult.passed
                              ? 'border-emerald-400/40 bg-emerald-500/10 text-emerald-100'
                              : 'border-amber-400/40 bg-amber-500/10 text-amber-100'
                          }`}
                          role="status"
                        >
                          <p className="font-semibold">
                            {assessmentResult.passed ? 'Đã đạt' : 'Cần củng cố'} · {assessmentResult.score}%
                          </p>
                          {!assessmentResult.passed && assessmentResult.weak_objectives?.length > 0 && (
                            <div className="mt-2 text-sm">
                              <p>Hãy ôn lại:</p>
                              <ul className="mt-1 list-disc space-y-1 pl-5">
                                {assessmentResult.weak_objectives.map((objective) => (
                                  <li key={objective}>{objective}</li>
                                ))}
                              </ul>
                              <Button
                                onClick={handleLoadReinforcement}
                                disabled={reinforcementLoading}
                                className="mt-4 bg-amber-700 text-white hover:bg-amber-800"
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
                        <div className="rounded-xl border border-red-400/40 bg-red-500/10 p-4 text-sm text-red-200" role="alert">
                          {reinforcementError}
                        </div>
                      )}

                      {reinforcement && (
                        <div className="space-y-3" aria-label="Học liệu củng cố">
                          <div className="rounded-xl border border-white/15 bg-black/10 p-4">
                            <h3 className="font-semibold text-white">Học liệu củng cố theo mục tiêu</h3>
                            <p className="mt-1 text-sm text-white/60">
                              Các đoạn dưới đây được truy xuất trong đúng bài học. Việc ôn tập không tự thay đổi điểm đánh giá.
                            </p>
                          </div>

                          {reinforcement.items.map((item) => (
                            <section
                              key={item.learning_objective}
                              className="rounded-xl border border-white/15 p-4"
                            >
                              <h4 className="font-medium text-white">{item.learning_objective}</h4>
                              <p className="mt-1 text-sm text-white/60">{item.message}</p>

                              {item.citations.length > 0 ? (
                                <ol className="mt-3 space-y-2">
                                  {item.citations.map((citation) => (
                                    <li
                                      key={citation.id}
                                      className="rounded-lg border border-white/10 bg-black/10 p-3"
                                    >
                                      <p className="text-xs font-medium text-orange-200">
                                        {citation.lesson_title} ·{' '}
                                        {citation.location?.page_start
                                          ? citation.location.page_start === citation.location.page_end
                                            ? `Trang ${citation.location.page_start}`
                                            : `Trang ${citation.location.page_start}–${citation.location.page_end}`
                                          : `Đoạn ${citation.ordinal + 1}`}
                                      </p>
                                      <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-white/70">
                                        {citation.excerpt}
                                      </p>
                                    </li>
                                  ))}
                                </ol>
                              ) : (
                                <p className="mt-3 text-sm text-amber-200">
                                  {item.status === 'not_indexed'
                                    ? 'Bài học chưa được lập chỉ mục RAG.'
                                    : 'Chưa có đoạn tài liệu đủ liên quan để gợi ý.'}
                                </p>
                              )}

                              <Button
                                onClick={() => handleAskAboutObjective(item.tutor_prompt)}
                                className="mt-3 border border-white/20 bg-transparent text-white hover:bg-white/10"
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
                        <section className="rounded-xl border border-white/15 bg-black/10 p-4">
                          <div className="flex items-start gap-3">
                            <Bot className="mt-0.5 h-5 w-5 text-orange-300" aria-hidden="true" />
                            <div>
                              <h3 className="font-semibold text-white">Tự kiểm tra bằng hội thoại AI</h3>
                              <p className="mt-1 text-sm text-white/60">
                                Đây chỉ là khuyến nghị luyện tập sau khi bạn đã đạt bài trắc nghiệm.
                                Kết quả không thay đổi điểm, mastery hoặc quyền chuyển bài.
                              </p>
                            </div>
                          </div>

                          <label htmlFor="dialogue-question" className="mt-4 block text-sm font-medium text-white">
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
                            className="mt-2 min-h-11 w-full rounded-lg border border-white/20 bg-slate-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                          >
                            {assessment.questions.map((question) => (
                              <option key={question.id} value={question.id}>{question.prompt}</option>
                            ))}
                          </select>

                          <label htmlFor="dialogue-answer" className="mt-4 block text-sm font-medium text-white">
                            Trả lời bằng lời của bạn
                          </label>
                          <textarea
                            id="dialogue-answer"
                            value={dialogueAnswer}
                            onChange={(event) => setDialogueAnswer(event.target.value)}
                            disabled={dialogueLoading}
                            maxLength={2000}
                            rows={4}
                            className="mt-2 w-full rounded-lg border border-white/20 bg-black/20 px-3 py-2 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500"
                            placeholder="Giải thích ngắn gọn điều bạn hiểu..."
                          />
                          <Button
                            onClick={handleDialogueKnowledgeCheck}
                            disabled={dialogueLoading || !dialogueQuestionId || !dialogueAnswer.trim()}
                            className="mt-3 bg-orange-600 text-white hover:bg-orange-700"
                          >
                            {dialogueLoading ? 'Đang đối chiếu học liệu...' : 'Nhận khuyến nghị'}
                          </Button>

                          {dialogueError && (
                            <p className="mt-3 text-sm text-red-200" role="alert">{dialogueError}</p>
                          )}

                          {dialogueResult && (
                            <div className="mt-4 rounded-lg border border-white/15 p-3" role="status">
                              <p className="text-sm font-semibold text-orange-200">
                                Khuyến nghị: {
                                  dialogueResult.outcome === 'demonstrated'
                                    ? 'Đã thể hiện hiểu biết'
                                    : dialogueResult.outcome === 'partial'
                                      ? 'Hiểu một phần'
                                      : dialogueResult.outcome === 'not_demonstrated'
                                        ? 'Chưa thể hiện rõ'
                                        : 'Chưa đủ bằng chứng'
                                }
                              </p>
                              <p className="mt-2 whitespace-pre-wrap text-sm text-white/80">{dialogueResult.feedback}</p>
                              <p className="mt-2 text-sm text-white/60">Bước tiếp theo: {dialogueResult.next_step}</p>
                              {dialogueResult.citations?.length > 0 && (
                                <ol className="mt-3 space-y-2">
                                  {dialogueResult.citations.map((citation) => (
                                    <li key={citation.id} className="rounded border border-white/10 p-2 text-sm text-white/70">
                                      <span className="font-medium text-orange-200">
                                        {citation.location?.page_start
                                          ? `Trang ${citation.location.page_start}`
                                          : citation.lesson_title}
                                      </span>
                                      <p className="mt-1 whitespace-pre-wrap">{citation.excerpt}</p>
                                    </li>
                                  ))}
                                </ol>
                              )}
                            </div>
                          )}
                        </section>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Lesson Info Card */}
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Thông tin bài học</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-white/70">
                  <span>Trạng thái</span>
                  <span className={st.color}>
                    {st.icon} {st.label}
                  </span>
                </div>
                {lesson.duration_minutes && (
                  <div className="flex justify-between text-white/70">
                    <span>Thời lượng</span>
                    <span>{lesson.duration_minutes} phút</span>
                  </div>
                )}
                {lesson.comments_count !== undefined && (
                  <div className="flex justify-between text-white/70">
                    <span>Bình luận</span>
                    <span>{lesson.comments_count}</span>
                  </div>
                )}
              </div>

              {isAuthenticated && (
                <div className="mt-6 space-y-3">
                  <Button
                    onClick={
                      assessment && !assessment.passed
                        ? () => setActiveTab('assessment')
                        : handleCompleteLesson
                    }
                    disabled={completion?.is_completed}
                    className="w-full py-3 rounded-xl bg-green-600 hover:bg-green-700 disabled:bg-green-700/60 text-white font-semibold border-0 transition-colors"
                  >
                    {completion?.is_completed
                      ? '✓ Đã hoàn thành'
                      : assessment && !assessment.passed
                        ? 'Làm bài đánh giá'
                        : 'Đánh dấu hoàn thành'}
                  </Button>

                  {completion?.next_lesson && (
                    <Button
                      onClick={() => navigate(`/lessons/${completion.next_lesson.id}`)}
                      className="w-full py-3 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-semibold border-0 transition-colors"
                    >
                      Sang bài tiếp theo
                      <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
                    </Button>
                  )}

                  {completion?.is_completed && !completion.next_lesson && (
                    <p className="text-center text-sm text-white/60">
                      Bạn đã hoàn thành bài khả dụng cuối cùng trong khóa học.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Quick tips */}
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-3">💡 Mẹo học tập</h3>
              <ul className="space-y-2 text-white/60 text-sm">
                <li>🎯 Xem video AI tóm tắt trước khi đọc chi tiết</li>
                <li>💬 Đặt câu hỏi cho AI nếu chưa hiểu</li>
                <li>📝 Ghi chú lại những điểm quan trọng</li>
                <li>👥 Trao đổi với bạn học qua bình luận</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ---------- Comment Item Component ---------- */
function CommentItem({ comment, onReply }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-orange-500/30 flex items-center justify-center text-sm text-orange-300 font-bold shrink-0">
          {comment.user_name?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-white font-semibold">{comment.user_name}</span>
            <span className="text-white/40 text-xs">
              {comment.created_at ? new Date(comment.created_at).toLocaleDateString('vi-VN') : ''}
            </span>
          </div>
          <p className="text-white/80 text-sm mt-1 whitespace-pre-wrap">{comment.content}</p>
          <button
            onClick={() => onReply({ id: comment.id, user_name: comment.user_name })}
            className="text-orange-400 hover:text-orange-300 text-xs mt-2 transition"
          >
            ↩ Trả lời
          </button>

          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 pl-4 border-l border-white/10 space-y-3">
              {comment.replies.map((r) => (
                <div key={r.id} className="flex items-start gap-2">
                  <div className="w-6 h-6 rounded-full bg-blue-500/30 flex items-center justify-center text-xs text-blue-300 font-bold shrink-0">
                    {r.user_name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-white font-semibold">{r.user_name}</span>
                      <span className="text-white/40">
                        {r.created_at ? new Date(r.created_at).toLocaleDateString('vi-VN') : ''}
                      </span>
                    </div>
                    <p className="text-white/70 text-sm mt-0.5">{r.content}</p>
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
