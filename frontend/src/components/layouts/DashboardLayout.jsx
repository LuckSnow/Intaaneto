import { Outlet } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-primary-600">Intaaneto</h1>
            </div>
            <div className="flex items-center space-x-4">
              <a href="/dashboard" className="text-gray-700 hover:text-primary-600">Dashboard</a>
              <a href="/courses" className="text-gray-700 hover:text-primary-600">Khóa học</a>
              <a href="/forum" className="text-gray-700 hover:text-primary-600">Diễn đàn</a>
              <div className="flex items-center space-x-2">
                <span className="text-gray-700">{user?.full_name}</span>
                <button onClick={logout} className="btn btn-secondary">Đăng xuất</button>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
