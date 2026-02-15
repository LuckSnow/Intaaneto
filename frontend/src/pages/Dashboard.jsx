import { useAuthStore } from '../store/authStore'

export default function Dashboard() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Chào mừng, {user?.full_name}! 👋
        </h1>
        <p className="text-gray-600 mt-2">Sẵn sàng học lập trình chưa?</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-700">Khóa học đang học</h3>
          <p className="text-3xl font-bold text-primary-600 mt-2">0</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-700">Bài tập hoàn thành</h3>
          <p className="text-3xl font-bold text-primary-600 mt-2">0</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-700">Điểm tích lũy</h3>
          <p className="text-3xl font-bold text-primary-600 mt-2">0</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Bắt đầu học</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="/forum" className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 transition">
            <h3 className="font-semibold text-primary-700">Diễn đàn</h3>
            <p className="text-sm text-gray-600 mt-1">Thảo luận và hỏi đáp với cộng đồng</p>
          </a>
          <a href="/exercises" className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 transition">
            <h3 className="font-semibold text-primary-700">Bài tập</h3>
            <p className="text-sm text-gray-600 mt-1">Luyện tập kỹ năng lập trình</p>
          </a>
        </div>
      </div>
    </div>
  )
}
