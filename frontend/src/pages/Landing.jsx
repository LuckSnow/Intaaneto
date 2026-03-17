import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

export default function Landing() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await api.get('/courses/')
        setCourses(response.data.results || response.data)
      } catch (error) {
        console.error('Failed to fetch courses:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchCourses()
  }, [])

  return (
    <div className="min-h-screen">
      {/* Content */}
      <div className="relative z-10 min-h-screen">
        {/* Hero Section */}
        <main className="px-8">
          <div className="max-w-7xl mx-auto min-h-screen flex flex-col justify-center items-center text-center pt-32">
            <h1 className="text-7xl md:text-8xl font-black text-white mb-12 tracking-tight leading-none">
              INTAANETO
            </h1>
            <p className="text-2xl md:text-3xl font-light text-white mb-4 tracking-wide animate-typing overflow-hidden whitespace-nowrap border-r-4 border-orange-500 pr-2 inline-block" 
               style={{ 
                 textShadow: '0 0 20px rgba(249,115,22,0.8), 0 0 40px rgba(249,115,22,0.5), 0 0 60px rgba(249,115,22,0.3)',
                 animation: 'typing 8s ease-in-out infinite, blink-caret 0.75s step-end infinite'
               }}>
              Nền tảng Học Lập Trình Trực Tuyến
            </p>
            {/* CTA Button */}
            <div className="mt-16">
              <a 
                href="/register" 
                className="inline-block px-12 py-4 rounded-full bg-white text-gray-900 hover:bg-gray-100 transition-all font-bold text-lg shadow-2xl hover:shadow-3xl transform hover:scale-105"
              >
                Bắt đầu học ngay
              </a>
            </div>
          </div>

        
        </main>

        {/* Courses Section */}
        <section className="px-8 py-20">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-5xl font-bold text-white mb-4" style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}>
                Khóa Học Nổi Bật
              </h2>
              <p className="text-xl text-white/80">Khám phá và bắt đầu hành trình học tập của bạn</p>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500"></div>
              </div>
            ) : courses.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-2xl text-white/60">Chưa có khóa học nào</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {courses.map((course) => (
                  <Link 
                    key={course.id} 
                    to={`/courses/${course.id}`}
                    className="group block"
                  >
                    <div className="bg-orange-50 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 h-[420px] flex flex-col transform hover:-translate-y-1">
                      {/* Course Image */}
                      <div className="h-48 flex-shrink-0 bg-gray-100 relative overflow-hidden">
                        {course.thumbnail ? (
                          <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
                            <span className="text-6xl">📚</span>
                          </div>
                        )}
                        {/* Difficulty Badge */}
                        <span className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                          course.difficulty === 'beginner' ? 'bg-green-500 text-white' :
                          course.difficulty === 'intermediate' ? 'bg-orange-500 text-white' :
                          'bg-red-500 text-white'
                        }`}>
                          {course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}
                        </span>
                      </div>
                      
                      {/* Course Info */}
                      <div className="p-5 flex flex-col flex-1">
                        <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-orange-600 transition font-heading">
                          {course.title}
                        </h3>
                        
                        <p className="text-gray-500 text-sm mb-4 line-clamp-2 flex-1 leading-relaxed">
                          {course.description || 'Khóa học chất lượng cao với lộ trình học rõ ràng'}
                        </p>
                        
                        <div className="border-t border-gray-100 pt-3 flex items-center justify-between mt-auto">
                          <div className="flex items-center gap-3 text-sm text-gray-400">
                            <span className="flex items-center gap-1">👥 {course.total_students || 0}</span>
                            <span className="flex items-center gap-1">⭐ {course.average_rating || '5.0'}</span>
                            <span className="flex items-center gap-1">⏱️ {course.duration_hours || 40}h</span>
                          </div>
                          <span className="text-orange-500 font-semibold text-sm group-hover:text-orange-600 transition">
                            Xem →
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Footer */}
        <footer className="px-8 py-8 border-t border-white/10">
          <div className="max-w-7xl mx-auto text-center">
            <p className="text-white/60">&copy; 2026 Intaaneto. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
