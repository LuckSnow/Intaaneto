import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '../store/authStore'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function CourseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [enrolling, setEnrolling] = useState(false)
  const [isEnrolled, setIsEnrolled] = useState(false)

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        const response = await api.get(`/courses/${id}/`)
        setCourse(response.data)
        
        // Check if user is enrolled (if authenticated)
        if (isAuthenticated) {
          try {
            await api.get(`/courses/${id}/progress/`)
            setIsEnrolled(true)
          } catch (error) {
            setIsEnrolled(false)
          }
        }
      } catch (error) {
        console.error('Failed to fetch course:', error)
        toast.error('Không thể tải thông tin khóa học')
      } finally {
        setLoading(false)
      }
    }
    fetchCourse()
  }, [id, isAuthenticated])

  const handleEnroll = async () => {
    if (!isAuthenticated) {
      toast('Vui lòng đăng nhập để bắt đầu học', { icon: '🔐' })
      navigate('/login')
      return
    }

    setEnrolling(true)
    try {
      await api.post(`/courses/${id}/enroll/`)
      setIsEnrolled(true)
      toast.success('Đăng ký khóa học thành công!')
      // Navigate to first lesson
      if (course.lessons && course.lessons.length > 0) {
        navigate(`/lessons/${course.lessons[0].id}`)
      }
    } catch (error) {
      toast.error(error.response?.data?.message || 'Đăng ký thất bại')
    } finally {
      setEnrolling(false)
    }
  }

  const handleStartLearning = () => {
    if (!isAuthenticated) {
      toast('Vui lòng đăng nhập để tiếp tục học', { icon: '🔐' })
      navigate('/login')
      return
    }
    if (course.lessons && course.lessons.length > 0) {
      navigate(`/lessons/${course.lessons[0].id}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Không tìm thấy khóa học</h2>
          <Button onClick={() => navigate('/')} className="bg-gradient-to-r from-orange-500 to-red-500">
            Về trang chủ
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Course Header */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8 mb-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Course Image */}
            <div className="aspect-video bg-gradient-to-br from-orange-500/30 to-red-500/30 rounded-xl flex items-center justify-center overflow-hidden">
              {course.thumbnail ? (
                <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
              ) : (
                <span className="text-8xl">📚</span>
              )}
            </div>

            {/* Course Info */}
            <div className="flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <span className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full text-sm text-orange-300 font-semibold">
                  {course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}
                </span>
                <span className="text-white/60">⏱️ {course.duration_hours || 40} giờ</span>
              </div>

              <h1 className="text-4xl font-bold text-white mb-4" style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}>
                {course.title}
              </h1>

              <p className="text-white/80 text-lg mb-6">
                {course.description}
              </p>

              <div className="flex items-center gap-6 mb-8 text-white/70">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">👥</span>
                  <span>{course.total_students || 0} học viên</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">⭐</span>
                  <span>{course.average_rating || '5.0'} / 5.0</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">📝</span>
                  <span>{course.lessons?.length || 0} bài học</span>
                </div>
              </div>

              {/* Enroll Button */}
              <div className="mt-auto">
                {isEnrolled ? (
                  <Button
                    onClick={handleStartLearning}
                    className="w-full py-4 text-lg rounded-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(34,197,94,0.8)]"
                  >
                    Tiếp tục học →
                  </Button>
                ) : (
                  <Button
                    onClick={handleEnroll}
                    disabled={enrolling}
                    className="w-full py-4 text-lg rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(239,68,68,0.8)]"
                  >
                    {enrolling ? 'Đang xử lý...' : '🎓 Bắt đầu học ngay'}
                  </Button>
                )}
                {!isAuthenticated && (
                  <p className="text-center text-white/60 text-sm mt-3">
                    Cần đăng nhập để bắt đầu học
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Course Content */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Nội dung khóa học</h2>
          
          {course.lessons && course.lessons.length > 0 ? (
            <div className="space-y-3">
              {course.lessons.map((lesson, index) => (
                <div
                  key={lesson.id}
                  onClick={() => isEnrolled && navigate(`/lessons/${lesson.id}`)}
                  className={`bg-white/5 border border-white/10 rounded-lg p-4 transition-all ${
                    isEnrolled ? 'hover:bg-white/10 cursor-pointer' : ''
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-300 font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-white font-semibold">{lesson.title}</h3>
                      <p className="text-white/60 text-sm">{lesson.duration_minutes || 30} phút</p>
                    </div>
                    {isEnrolled && (
                      <span className="text-white/40 text-sm">🔓</span>
                    )}
                    {!isEnrolled && (
                      <span className="text-white/40 text-sm">🔒</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-white/60 text-center py-8">Nội dung khóa học đang được cập nhật...</p>
          )}
        </div>
      </div>
    </div>
  )
}
