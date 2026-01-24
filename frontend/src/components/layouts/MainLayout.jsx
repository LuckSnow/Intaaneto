import { Outlet } from 'react-router-dom'

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-primary-600">Intaaneto</h1>
            </div>
            <div className="flex items-center space-x-4">
              <a href="/courses" className="text-gray-700 hover:text-primary-600">Khóa học</a>
              <a href="/forum" className="text-gray-700 hover:text-primary-600">Diễn đàn</a>
              <a href="/login" className="btn btn-primary">Đăng nhập</a>
            </div>
          </div>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
