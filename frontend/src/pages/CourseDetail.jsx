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
        <div className="bg-orange-50 rounded-2xl shadow-lg p-8 mb-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Course Image */}
            <div className="aspect-video bg-gray-100 rounded-xl overflow-hidden">
              {course.thumbnail ? (
                <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
                  <span className="text-8xl">📚</span>
                </div>
              )}
            </div>

            {/* Course Info */}
            <div className="flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  course.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                  course.difficulty === 'intermediate' ? 'bg-orange-100 text-orange-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}
                </span>
                <span className="text-gray-400">⏱️ {course.duration_hours || 40} giờ</span>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4 font-heading">
                {course.title}
              </h1>

              <p className="text-gray-600 text-base mb-6 leading-relaxed">
                {course.description}
              </p>

              <div className="flex items-center gap-6 mb-8 text-gray-500">
                <div className="flex items-center gap-2">
                  <span className="text-xl">👥</span>
                  <span className="text-sm">{course.total_students || 0} học viên</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl">⭐</span>
                  <span className="text-sm">{course.average_rating || '5.0'} / 5.0</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl">📝</span>
                  <span className="text-sm">{course.lessons?.length || 0} bài học</span>
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
                  <p className="text-center text-gray-400 text-sm mt-3">
                    Cần đăng nhập để bắt đầu học
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Course Content */}
        <div className="bg-orange-50 rounded-2xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 font-heading">Nội dung khóa học</h2>
          
          {course.lessons && course.lessons.length > 0 ? (
            <div className="space-y-3">
              {course.lessons.map((lesson, index) => (
                <div
                  key={lesson.id}
                  className="bg-gray-50 border border-gray-100 rounded-xl p-4 hover:bg-orange-50 hover:border-orange-200 transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-gray-800 font-semibold">{lesson.title}</h3>
                      <p className="text-gray-400 text-sm">{lesson.duration_minutes || 30} phút</p>
                    </div>
                    {isEnrolled ? (
                      <span className="text-green-500 text-sm">🔓</span>
                    ) : (
                      <span className="text-gray-300 text-sm">🔒</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">Nội dung khóa học đang được cập nhật...</p>
          )}
        </div>
      </div>
    </div>
  )
}
