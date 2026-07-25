import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Upload } from 'lucide-react'
import logoFull from '../../assets/images/logo-full.png'
import { useAuthStore } from '../../store/authStore'
import { getUserAvatar } from '../../utils/avatar'
import AppBreadcrumbs from '../navigation/AppBreadcrumbs'
import DashboardLayout from './DashboardLayout'

export default function MainLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = async () => {
    await logout()
    window.location.href = '/'
  }

  const userAvatar = getUserAvatar(user)

  const isActive = (href) => location.pathname === href || location.pathname.startsWith(href + '/')

  if (isAuthenticated && (user?.role === 'teacher' || user?.role === 'admin')) {
    return <DashboardLayout />
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Image */}
      <div 
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      ></div>

      {/* Header */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-white/20 backdrop-blur-xl shadow-lg shadow-black/5 border-b border-white/30'
          : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-14 items-center">
            <div className="flex-shrink-0">
              <a href="/" className="block transition-all duration-300 hover:drop-shadow-[0_0_15px_rgba(249,115,22,0.8)]">
                <img 
                  src={logoFull} 
                  alt="Intaaneto" 
                  className="h-16 w-auto"
                />
              </a>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" asChild className={`transition-all duration-300 ${
                scrolled
                  ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                  : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
              }`}>
                <a href="/courses" className="relative">
                  Khóa học
                  {isActive('/courses') && (
                    <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-orange-400 rounded-full" />
                  )}
                </a>
              </Button>
              <Button variant="ghost" asChild className={`transition-all duration-300 ${
                scrolled
                  ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                  : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
              }`}>
                <a href="/forum" className="relative">
                  Diễn đàn
                  {isActive('/forum') && (
                    <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-orange-400 rounded-full" />
                  )}
                </a>
              </Button>
              
              {isAuthenticated ? (
                <>
                  {(user?.role === 'teacher' || user?.role === 'admin') && (
                    <Button variant="ghost" asChild className={`transition-all duration-300 ${
                      scrolled
                        ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                        : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
                    }`}>
                      <a href="/teacher/upload" className="flex items-center gap-2"><Upload className="h-4 w-4" aria-hidden="true" />Tải bài giảng</a>
                    </Button>
                  )}
                  <Button variant="ghost" asChild className={`transition-all duration-300 ${
                    scrolled
                      ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                      : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
                  }`}>
                    <a href="/dashboard" className="relative">
                      Dashboard
                      {isActive('/dashboard') && (
                        <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-orange-400 rounded-full" />
                      )}
                    </a>
                  </Button>
                  <a href="/profile" className="flex items-center space-x-2 group">
                    {userAvatar ? (
                      <img 
                        src={userAvatar} 
                        alt={user?.full_name || 'Avatar'} 
                        className="w-9 h-9 rounded-full object-cover border-2 border-white/50 group-hover:border-orange-400 transition-all shadow-md"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all ${
                        scrolled
                          ? 'bg-black text-white border-black/30'
                          : 'bg-gradient-to-r from-orange-400 to-amber-400 text-white border-white/50'
                      }`}>
                        {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                      </div>
                    )}
                    <span className={`text-sm font-medium transition-all duration-300 ${
                      scrolled ? 'text-black' : 'text-white'
                    }`}>
                      {user?.full_name || user?.username}
                    </span>
                  </a>
                  <Button 
                    onClick={handleLogout}
                    className={`rounded-full font-bold border-0 transition-all duration-300 ${
                      scrolled
                        ? 'bg-black hover:bg-gray-800 text-white shadow-md'
                        : 'bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white shadow-lg hover:shadow-[0_0_20px_rgba(251,191,36,0.6)]'
                    }`}
                  >
                    Đăng xuất
                  </Button>
                </>
              ) : (
                <Button asChild className={`rounded-full font-bold border-0 transition-all duration-300 ${
                  scrolled
                    ? 'bg-black hover:bg-gray-800 text-white shadow-md'
                    : 'bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white shadow-lg hover:shadow-[0_0_20px_rgba(251,191,36,0.6)]'
                }`}>
                  <a href="/login">Đăng nhập</a>
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="pt-14">
        <AppBreadcrumbs className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" />
        <Outlet />
      </main>
    </div>
  )
}
