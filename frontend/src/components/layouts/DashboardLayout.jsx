import { Outlet } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { Button } from '@/components/ui/button'
import logoFull from '../../assets/images/logo-full.png'

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()

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
              <a href="/dashboard" className="block transition-all duration-300 hover:drop-shadow-[0_0_15px_rgba(249,115,22,0.8)]">
                <img 
                  src={logoFull} 
                  alt="Intaaneto" 
                  className="h-20 w-auto"
                />
              </a>
            </div>
            <div className="flex items-center space-x-6">
              <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                <a href="/dashboard">Dashboard</a>
              </Button>
              <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                <a href="/forum">Diễn đàn</a>
              </Button>
              <div className="flex items-center space-x-4 border-l border-white/20 pl-6">
                <Button variant="ghost" asChild className="text-white hover:text-white hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]">
                  <a href="/profile" className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                      <span className="text-sm font-bold">{user?.full_name?.charAt(0) || 'U'}</span>
                    </div>
                    <span className="font-medium">{user?.full_name}</span>
                  </a>
                </Button>
                <Button 
                  onClick={logout} 
                  className="rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(239,68,68,0.8)]"
                >
                  Đăng xuất
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="pt-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
