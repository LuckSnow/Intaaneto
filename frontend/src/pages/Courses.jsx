import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

const DIFFICULTY_OPTIONS = [
  { value: 'all', label: 'Tất cả' },
  { value: 'beginner', label: 'Cơ bản' },
  { value: 'intermediate', label: 'Trung bình' },
  { value: 'advanced', label: 'Nâng cao' },
]

const DIFFICULTY_MAP = {
  beginner: 'Cơ bản',
  intermediate: 'Trung bình',
  advanced: 'Nâng cao',
}

const DIFFICULTY_COLOR = {
  beginner: 'bg-green-500/20 border-green-500/30 text-green-300',
  intermediate: 'bg-orange-500/20 border-orange-500/30 text-orange-300',
  advanced: 'bg-red-500/20 border-red-500/30 text-red-300',
}

export default function Courses() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [difficulty, setDifficulty] = useState('all')

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

  const filtered = courses.filter((c) => {
    const matchSearch = c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.description?.toLowerCase().includes(search.toLowerCase())
    const matchDifficulty = difficulty === 'all' || c.difficulty === difficulty
    return matchSearch && matchDifficulty
  })

  return (
    <div className="min-h-screen">
      {/* Background */}
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      />

      <div className="max-w-7xl mx-auto px-6 py-10 pt-28">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold text-white mb-3" style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}>
            Khóa Học
          </h1>
          <p className="text-lg text-white/70">Tìm kiếm và khám phá các khóa học phù hợp với bạn</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          {/* Search */}
          <div className="flex-1 relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/50">🔍</span>
            <input
              type="text"
              placeholder="Tìm kiếm khóa học..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 transition"
            />
          </div>

          {/* Difficulty filter */}
          <div className="flex gap-2 flex-wrap">
            {DIFFICULTY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDifficulty(opt.value)}
                className={`px-5 py-3 rounded-xl border text-sm font-semibold transition-all ${
                  difficulty === opt.value
                    ? 'bg-orange-500 border-orange-500 text-white shadow-lg shadow-orange-500/25'
                    : 'bg-white/10 border-white/20 text-white/70 hover:bg-white/20 hover:text-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <p className="text-white/50 text-sm mb-6">
          {loading ? 'Đang tải...' : `Hiển thị ${filtered.length} khóa học`}
        </p>

        {/* Course Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <span className="text-6xl mb-4 block">📭</span>
            <p className="text-2xl text-white/60 mb-2">Không tìm thấy khóa học</p>
            <p className="text-white/40">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filtered.map((course) => (
              <Link
                key={course.id}
                to={`/courses/${course.id}`}
                className="group relative block"
              >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition"></div>
                <div className="relative bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl overflow-hidden hover:bg-white/20 transition-all h-[420px] flex flex-col">
                  {/* Course Image */}
                  <div className="h-48 flex-shrink-0 bg-gradient-to-br from-orange-500/30 to-red-500/30 flex items-center justify-center">
                    {course.thumbnail ? (
                      <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-6xl">📚</span>
                    )}
                  </div>

                  {/* Course Info */}
                  <div className="p-6 flex flex-col flex-1">
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`px-3 py-1 border rounded-full text-xs font-semibold ${DIFFICULTY_COLOR[course.difficulty] || DIFFICULTY_COLOR.beginner}`}>
                        {DIFFICULTY_MAP[course.difficulty] || 'Cơ bản'}
                      </span>
                      <span className="text-white/60 text-sm">⏱️ {course.duration_hours || 40} giờ</span>
                    </div>

                    <h3 className="text-xl font-bold text-white mb-2 line-clamp-2 group-hover:text-orange-300 transition">
                      {course.title}
                    </h3>

                    <p className="text-white/70 text-sm mb-4 line-clamp-2 flex-1">
                      {course.description || 'Khóa học chất lượng cao với lộ trình học rõ ràng'}
                    </p>

                    <div className="flex items-center justify-between mt-auto">
                      <div className="flex items-center gap-4 text-sm text-white/60">
                        <span>👥 {course.total_students || 0}</span>
                        <span>⭐ {course.average_rating || '5.0'}</span>
                        <span>📄 {course.lessons_count || 0} bài</span>
                      </div>
                      <span className="text-orange-400 font-bold group-hover:text-orange-300 transition">
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
    </div>
  )
}
