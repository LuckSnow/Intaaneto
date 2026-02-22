import { Outlet, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../../store/authStore'
import { Button } from '@/components/ui/button'
import logoFull from '../../assets/images/logo-full.png'

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
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

  // Get user avatar - prefer Google avatar, fallback to uploaded avatar
  const userAvatar = user?.google_avatar || user?.avatar || null

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard' },
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
          <div className="flex justify-between h-14 items-center">
            <div className="flex-shrink-0">
              <a href="/dashboard" className="block transition-all duration-300 hover:drop-shadow-[0_0_15px_rgba(249,115,22,0.8)]">
                <img 
                  src={logoFull} 
                  alt="Intaaneto" 
                  className="h-12 w-auto"
                />
              </a>
            </div>
            <div className="flex items-center space-x-4">
              {navLinks.map(link => (
                <Button key={link.href} variant="ghost" asChild className={`transition-all duration-300 relative ${
                  scrolled
                    ? 'text-black hover:text-black hover:bg-black/10 font-semibold'
                    : 'text-white hover:text-white hover:bg-white/10 hover:shadow-[0_0_15px_rgba(249,115,22,0.6)]'
                }`}>
                  <a href={link.href} className="relative">
                    {link.label}
                    {isActive(link.href) && (
                      <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-orange-400 rounded-full" />
                    )}
                  </a>
                </Button>
              ))}
              
              <div className="flex items-center space-x-4 border-l border-white/20 pl-4">
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
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="pt-14 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
