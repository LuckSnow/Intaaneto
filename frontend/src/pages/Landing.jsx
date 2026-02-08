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
    <div className="fixed inset-0 overflow-auto">
      {/* Background Image */}
      <div 
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      ></div>

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
                    className="group relative block"
                  >
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition"></div>
                    <div className="relative bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl overflow-hidden hover:bg-white/20 transition-all">
                      {/* Course Image */}
                      <div className="aspect-video bg-gradient-to-br from-orange-500/30 to-red-500/30 flex items-center justify-center">
                        {course.thumbnail ? (
                          <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-6xl">📚</span>
                        )}
                      </div>
                      
                      {/* Course Info */}
                      <div className="p-6">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full text-xs text-orange-300 font-semibold">
                            {course.difficulty === 'beginner' ? 'Cơ bản' : course.difficulty === 'intermediate' ? 'Trung bình' : 'Nâng cao'}
                          </span>
                          <span className="text-white/60 text-sm">⏱️ {course.duration_hours || 40} giờ</span>
                        </div>
                        
                        <h3 className="text-xl font-bold text-white mb-2 line-clamp-2 group-hover:text-orange-300 transition">
                          {course.title}
                        </h3>
                        
                        <p className="text-white/70 text-sm mb-4 line-clamp-3">
                          {course.description || 'Khóa học chất lượng cao với lộ trình học rõ ràng'}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm text-white/60">
                            <span>👥 {course.total_students || 0}</span>
                            <span>⭐ {course.average_rating || '5.0'}</span>
                          </div>
                          <span className="text-orange-400 font-bold group-hover:text-orange-300 transition">
                            Xem chi tiết →
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
