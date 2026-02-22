import { useAuthStore } from '../store/authStore'

export default function Dashboard() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-heading font-bold text-white drop-shadow-lg">
          Chào mừng, {user?.full_name}! 👋
        </h1>
        <p className="text-white/70 mt-2">Sẵn sàng học lập trình chưa?</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-orange-50 rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-heading font-semibold text-gray-700">Khóa học đang học</h3>
          <p className="text-3xl font-bold text-orange-500 mt-2">0</p>
        </div>
        <div className="bg-orange-50 rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-heading font-semibold text-gray-700">Bài tập hoàn thành</h3>
          <p className="text-3xl font-bold text-orange-500 mt-2">0</p>
        </div>
        <div className="bg-orange-50 rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-heading font-semibold text-gray-700">Điểm tích lũy</h3>
          <p className="text-3xl font-bold text-orange-500 mt-2">0</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-orange-50 rounded-2xl p-6 shadow-md">
        <h2 className="text-xl font-heading font-bold text-gray-800 mb-4">Bắt đầu học</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="/forum" className="p-4 border-2 border-orange-200 rounded-xl hover:border-orange-400 hover:bg-orange-100/50 transition">
            <h3 className="font-heading font-semibold text-orange-600">Diễn đàn</h3>
            <p className="text-sm text-gray-600 mt-1">Thảo luận và hỏi đáp với cộng đồng</p>
          </a>
          <a href="/exercises" className="p-4 border-2 border-orange-200 rounded-xl hover:border-orange-400 hover:bg-orange-100/50 transition">
            <h3 className="font-heading font-semibold text-orange-600">Bài tập</h3>
            <p className="text-sm text-gray-600 mt-1">Luyện tập kỹ năng lập trình</p>
          </a>
        </div>
      </div>
    </div>
  )
}
