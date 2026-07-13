import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../services/api'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/button'

export default function Login() {
  const navigate = useNavigate()
  const { login, googleLogin, isLoading } = useAuthStore()
  const [needVerification, setNeedVerification] = useState(false)
  const [verifyEmail, setVerifyEmail] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setNeedVerification(false)
    try {
      await login(formData)
      toast.success('Đăng nhập thành công!')
      navigate('/dashboard')
    } catch (error) {
      const errorData = error.response?.data
      if (errorData) {
        if (errorData.need_verification) {
          setNeedVerification(true)
          setVerifyEmail(errorData.email || formData.email)
          toast.error(errorData.error)
        } else if (errorData.email) {
          toast.error(`Email: ${errorData.email[0]}`)
        } else if (errorData.password) {
          toast.error(`Password: ${errorData.password[0]}`)
        } else if (errorData.error) {
          toast.error(errorData.error)
        } else {
          toast.error('Đăng nhập thất bại')
        }
      } else {
        toast.error('Đăng nhập thất bại')
      }
    }
  }

  const handleResendVerification = async () => {
    try {
      await api.post('/auth/resend_verification/', { email: verifyEmail })
      toast.success('Email xác thực đã được gửi lại!')
    } catch {
      toast.error('Gửi lại thất bại')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Glass Card */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8">
          <div className="mb-8">
            <h2 className="text-center text-4xl font-bold text-white" style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}>
              Đăng nhập
            </h2>
            <p className="mt-3 text-center text-sm text-white/80">
              Hoặc{' '}
              <a href="/register" className="text-orange-400 hover:text-orange-300 font-semibold transition-colors">
                đăng ký tài khoản mới
              </a>
            </p>
          </div>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Verification warning */}
            {needVerification && (
              <div className="bg-orange-500/20 border border-orange-400/50 rounded-lg p-4">
                <p className="text-white/90 text-sm mb-2">Email chưa được xác thực. Kiểm tra hộp thư của bạn.</p>
                <button
                  type="button"
                  onClick={handleResendVerification}
                  className="text-sm text-orange-400 hover:text-orange-300 underline font-semibold"
                >
                  Gửi lại email xác thực
                </button>
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white/90 mb-2">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                placeholder="admin@intaaneto.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white/90 mb-2">
                Mật khẩu
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-full bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(251,191,36,0.6)]"
            >
              {isLoading ? 'Đang xử lý...' : 'Đăng nhập'}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/30"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white/10 text-white/80">Hoặc</span>
            </div>
          </div>

          {/* Google Login */}
          <Button
            type="button"
            disabled={isLoading}
            className="w-full py-3 rounded-full bg-white hover:bg-gray-100 text-gray-900 font-bold shadow-lg border-0 transition-all duration-300 flex items-center justify-center space-x-2"
            onClick={async () => {
              try {
                await googleLogin()
                toast.success('Đăng nhập Google thành công!')
                navigate('/dashboard')
              } catch (error) {
                if (error.code === 'auth/popup-closed-by-user') {
                  return // user đóng popup, không cần báo lỗi
                }
                if (error.code === 'firebase/not-configured') {
                  toast.error(error.message)
                  return
                }
                toast.error(error.response?.data?.error || 'Đăng nhập Google thất bại')
              }
            }}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Đăng nhập với Google</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
