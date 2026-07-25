import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../../store/authStore'
import { Button } from '@/components/ui/button'
import logoFull from '../../assets/images/logo-full.png'
import { getUserAvatar } from '../../utils/avatar'
import AppBreadcrumbs from '../navigation/AppBreadcrumbs'

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  const userAvatar = getUserAvatar(user)

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard' },
    ...((user?.role === 'teacher' || user?.role === 'admin')
      ? [{ href: '/teacher/upload', label: 'Tải PDF' }]
      : []),
    ...(user?.role === 'teacher'
      ? [{ href: '/teacher/courses', label: 'Quản lý khóa' }]
      : []),
    { href: '/courses', label: 'Khóa học' },
    { href: '/forum', label: 'Diễn đàn' },
  ]

  const isActive = (href) => location.pathname === href || location.pathname.startsWith(href + '/')

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
          <div className="flex min-h-14 flex-wrap items-center justify-between gap-x-4">
            <div className="flex-shrink-0">
              <Link to="/dashboard" className="block transition-all duration-300 hover:drop-shadow-[0_0_15px_rgba(249,115,22,0.8)]">
                <img 
                  src={logoFull} 
                  alt="Intaaneto" 
                  className="h-10 w-auto sm:h-12"
                />
              </Link>
            </div>
            <div className="order-3 flex w-full items-center gap-1 overflow-x-auto border-t border-white/15 py-1 sm:order-none sm:w-auto sm:flex-1 sm:justify-end sm:border-0 sm:py-0">
              {navLinks.map(link => (
                <Button key={link.href} variant="ghost" asChild className={`transition-all duration-300 relative ${
                  scrolled
                    ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                    : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
                } px-2 text-xs sm:px-3 sm:text-sm`}>
                  <Link to={link.href} className="relative whitespace-nowrap">
                    {link.label}
                    {isActive(link.href) && (
                      <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-orange-400 rounded-full" />
                    )}
                  </Link>
                </Button>
              ))}
              
            </div>

            <div className="flex items-center gap-2 sm:gap-4 sm:border-l sm:border-white/20 sm:pl-4">
                <Link to="/profile" className="flex items-center gap-2 group">
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
                  <span className={`hidden text-sm font-medium transition-all duration-300 lg:inline ${
                    scrolled ? 'text-black' : 'text-white'
                  }`}>
                    {user?.full_name || user?.username}
                  </span>
                </Link>
                <Button 
                  onClick={handleLogout}
                  className={`rounded-full border-0 px-3 text-xs font-bold transition-all duration-300 sm:px-4 sm:text-sm ${
                    scrolled
                      ? 'bg-black hover:bg-gray-800 text-white shadow-md'
                      : 'bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white shadow-lg hover:shadow-[0_0_20px_rgba(251,191,36,0.6)]'
                  }`}
                >
                  Đăng xuất
                </Button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 pb-8 pt-28 sm:px-6 sm:pt-20 lg:px-8">
        <AppBreadcrumbs className="mb-4" />
        <Outlet />
      </main>
    </div>
  )
}
