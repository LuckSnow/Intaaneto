import { Outlet } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import logoFull from '../../assets/images/logo-full.png'
import { useAuthStore } from '../../store/authStore'

export default function MainLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
    window.location.href = '/'
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Image */}
      <div 
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      ></div>

      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-24 items-center">
            <div className="flex-shrink-0">
              <a href="/" className="block transition-all duration-300 hover:drop-shadow-[0_0_15px_rgba(249,115,22,0.8)]">
                <img 
                  src={logoFull} 
                  alt="Intaaneto" 
                  className="h-20 w-auto"
                />
              </a>
            </div>
            <div className="flex items-center space-x-6">
              <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                <a href="/courses">Khóa học</a>
              </Button>
              <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                <a href="/forum">Diễn đàn</a>
              </Button>
              
              {isAuthenticated ? (
                <>
                  {(user?.role === 'teacher' || user?.role === 'admin') && (
                    <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                      <a href="/teacher/upload">📤 Tải bài giảng</a>
                    </Button>
                  )}
                  <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                    <a href="/dashboard">Dashboard</a>
                  </Button>
                  <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                    <a href="/profile" className="flex items-center space-x-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm">
                        {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                      </div>
                      <span>{user?.full_name || user?.username}</span>
                    </a>
                  </Button>
                  <Button 
                    onClick={handleLogout}
                    className="rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(239,68,68,0.8)]"
                  >
                    Đăng xuất
                  </Button>
                </>
              ) : (
                <Button asChild className="rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(239,68,68,0.8)]">
                  <a href="/login">Đăng nhập</a>
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="pt-24">
        <Outlet />
      </main>
    </div>
  )
}
