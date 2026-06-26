import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import { courseService } from '../services/courseService'
import { aiService } from '../services/aiService'
import toast from 'react-hot-toast'

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
  const chatEndRef = useRef(null)

  // Polling for processing
  const [polling, setPolling] = useState(false)

  useEffect(() => {
    fetchLesson()
  }, [id])

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
      await courseService.completeLesson(id)
      toast.success('Đã hoàn thành bài học!')
    } catch {
      toast.error('Không thể đánh dấu hoàn thành')
    }
  }

  // AI Chat
  const handleSendChat = async () => {
    if (!chatInput.trim()) return
    const question = chatInput.trim()
    setChatInput('')
    setChatMessages((prev) => [...prev, { role: 'user', content: question }])
    setChatLoading(true)
    try {
      const context = lesson?.ai_summary
        ? `Đây là nội dung bài giảng "${lesson.title}":\n${lesson.ai_summary}\n\nCâu hỏi của sinh viên:`
        : ''
      const data = await aiService.sendMessage({
        message: context ? `${context}\n${question}` : question,
        context: 'lesson_support',
      })
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response || data.message || 'Không có phản hồi' },
      ])
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '⚠️ Có lỗi xảy ra. Vui lòng thử lại.' },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

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
  const videoUrl = lesson.ai_video_url || lesson.video_url

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
                  {lesson.content ? (
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">{lesson.content}</div>
                  ) : (
                    <p className="text-white/50">Nội dung sẽ được cập nhật sau khi AI xử lý xong.</p>
                  )}
                </div>
              )}

              {activeTab === 'summary' && (
                <div>
                  <h2 className="text-xl font-bold text-white mb-4">🤖 Tóm tắt bởi AI</h2>
                  {lesson.ai_summary ? (
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">{lesson.ai_summary}</div>
                  ) : (
                    <p className="text-white/50">AI đang tóm tắt bài giảng... Vui lòng chờ.</p>
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
                  <h2 className="text-xl font-bold text-white mb-4">🧠 Hỏi AI về bài giảng</h2>

                  {/* Chat messages */}
                  <div className="h-80 overflow-y-auto mb-4 space-y-3 pr-2 custom-scrollbar">
                    {chatMessages.length === 0 && (
                      <div className="text-center py-10 text-white/40">
                        <span className="text-4xl block mb-2">🤖</span>
                        <p>Hãy đặt câu hỏi về bài giảng, AI sẽ hỗ trợ giải đáp!</p>
                      </div>
                    )}
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${
                            msg.role === 'user'
                              ? 'bg-orange-500/30 border border-orange-500/40 text-white'
                              : 'bg-white/10 border border-white/20 text-white/90'
                          }`}
                        >
                          {msg.content}
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
                      className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-orange-500/50 transition"
                    />
                    <Button
                      onClick={handleSendChat}
                      disabled={chatLoading || !chatInput.trim()}
                      className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl px-6 border-0"
                    >
                      {chatLoading ? '...' : '🚀'}
                    </Button>
                  </div>
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
                <Button
                  onClick={handleCompleteLesson}
                  className="w-full mt-6 py-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold border-0 transition-all"
                >
                  ✅ Đánh dấu hoàn thành
                </Button>
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
