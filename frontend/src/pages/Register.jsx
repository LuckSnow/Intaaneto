import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../services/api'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { getDefaultAuthenticatedPath } from '../utils/authNavigation'

const PASSWORD_RULES = [
  { key: 'length', label: 'Ít nhất 8 ký tự', test: (p) => p.length >= 8 },
  { key: 'upper', label: '1 chữ cái viết hoa', test: (p) => /[A-Z]/.test(p) },
  { key: 'lower', label: '1 chữ cái viết thường', test: (p) => /[a-z]/.test(p) },
  { key: 'digit', label: '1 chữ số', test: (p) => /\d/.test(p) },
  { key: 'special', label: '1 ký tự đặc biệt (!@#$%...)', test: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
]

export default function Register() {
  const navigate = useNavigate()
  const { register: registerUser, googleLogin, isLoading } = useAuthStore()
  const [registered, setRegistered] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    password_confirm: '',
  })

  const passwordStrength = useMemo(() => {
    const passed = PASSWORD_RULES.filter(r => r.test(formData.password)).length
    return { passed, total: PASSWORD_RULES.length, percent: Math.round((passed / PASSWORD_RULES.length) * 100) }
  }, [formData.password])

  const strengthColor = passwordStrength.percent <= 40 ? 'bg-red-500' : passwordStrength.percent <= 80 ? 'bg-yellow-500' : 'bg-green-500'
  const strengthLabel = passwordStrength.percent <= 40 ? 'Yếu' : passwordStrength.percent <= 80 ? 'Trung bình' : 'Mạnh'

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (formData.password !== formData.password_confirm) {
      toast.error('Mật khẩu không khớp')
      return
    }
    if (passwordStrength.passed < PASSWORD_RULES.length) {
      toast.error('Mật khẩu chưa đủ yêu cầu')
      return
    }
    try {
      const response = await registerUser(formData)
      if (!response?.email_sent) {
        toast.error('Đã tạo tài khoản nhưng chưa gửi được email xác thực. Vui lòng thử lại sau.')
        return
      }
      setRegistered(true)
    } catch (error) {
      const errorData = error.response?.data
      if (errorData) {
        if (errorData.email) {
          toast.error(`Email: ${errorData.email[0]}`)
        } else if (errorData.username) {
          toast.error(`Username: ${errorData.username[0]}`)
        } else if (errorData.password) {
          toast.error(`Mật khẩu: ${errorData.password[0]}`)
        } else if (errorData.error) {
          toast.error(errorData.error)
        } else {
          toast.error('Đăng ký thất bại')
        }
      } else {
        toast.error('Đăng ký thất bại')
      }
    }
  }

  // After successful registration — show verification message
  if (registered) {
    return (
      <div className="min-h-screen flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8 text-center">
            <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-heading font-bold text-white mb-2">Kiểm tra email của bạn!</h2>
            <p className="text-white/80 mb-2">
              Chúng tôi đã gửi một email xác thực đến <strong className="text-orange-400">{formData.email}</strong>
            </p>
            <p className="text-white/60 text-sm mb-6">Vui lòng nhấn vào link trong email để kích hoạt tài khoản.</p>
            <div className="space-y-3">
              <Button
                onClick={() => navigate('/login')}
                className="w-full rounded-full bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white font-bold border-0 shadow-md"
              >
                Đi đến trang Đăng nhập
              </Button>
              <button
                onClick={async () => {
                  try {
                      const response = await api.post('/auth/resend_verification/', { email: formData.email })
                      if (response.data?.email_sent) {
                        toast.success('Email xác thực đã được gửi lại!')
                      } else {
                        toast.error('Chưa gửi được email xác thực. Vui lòng thử lại sau.')
                      }
                  } catch {
                    toast.error('Gửi lại thất bại')
                  }
                }}
                className="text-sm text-orange-400 hover:text-orange-300 underline"
              >
                Gửi lại email xác thực
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Glass Card */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8">
          <div className="mb-8">
            <h2 className="text-center text-4xl font-heading font-bold text-white" style={{ textShadow: '0 0 20px rgba(249,115,22,0.6)' }}>
              Đăng ký tài khoản
            </h2>
            <p className="mt-3 text-center text-sm text-white/80">
              Đã có tài khoản?{' '}
              <Link to="/login" className="text-orange-400 hover:text-orange-300 font-semibold transition-colors">
                Đăng nhập
              </Link>
            </p>
          </div>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-white/90 mb-2">Email</label>
              <input
                type="email"
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/90 mb-2">Tên đăng nhập</label>
              <input
                type="text"
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                placeholder="username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/90 mb-2">Họ và tên</label>
              <input
                type="text"
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                placeholder="Nguyễn Văn A"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/90 mb-2">Mật khẩu</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="w-full px-4 py-3 pr-12 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white/80 transition-colors"
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {/* Password Strength */}
              {formData.password && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-white/20 rounded-full overflow-hidden">
                      <div className={`h-full ${strengthColor} rounded-full transition-all duration-300`} style={{ width: `${passwordStrength.percent}%` }} />
                    </div>
                    <span className={`text-xs font-semibold ${strengthColor === 'bg-red-500' ? 'text-red-400' : strengthColor === 'bg-yellow-500' ? 'text-yellow-400' : 'text-green-400'}`}>
                      {strengthLabel}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-1">
                    {PASSWORD_RULES.map(rule => (
                      <div key={rule.key} className="flex items-center gap-1.5">
                        {rule.test(formData.password) ? (
                          <svg className="w-3.5 h-3.5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <svg className="w-3.5 h-3.5 text-white/40 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" strokeWidth="2" />
                          </svg>
                        )}
                        <span className={`text-xs ${rule.test(formData.password) ? 'text-green-400' : 'text-white/50'}`}>{rule.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-white/90 mb-2">Xác nhận mật khẩu</label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  required
                  className="w-full px-4 py-3 pr-12 bg-white/10 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent backdrop-blur-sm transition-all"
                  placeholder="••••••••"
                  value={formData.password_confirm}
                  onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white/80 transition-colors"
                >
                  {showConfirm ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {formData.password_confirm && formData.password !== formData.password_confirm && (
                <p className="text-red-400 text-xs mt-1">Mật khẩu xác nhận không khớp</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-full bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white font-bold shadow-lg border-0 transition-all duration-300 hover:shadow-[0_0_20px_rgba(251,191,36,0.6)] mt-6"
            >
              {isLoading ? 'Đang xử lý...' : 'Đăng ký'}
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

          {/* Google Sign Up */}
          <Button
            type="button"
            disabled={isLoading}
            className="w-full py-3 rounded-full bg-white hover:bg-gray-100 text-gray-900 font-bold shadow-lg border-0 transition-all duration-300 flex items-center justify-center space-x-2"
            onClick={async () => {
              try {
                const data = await googleLogin()
                toast.success('Đăng ký Google thành công!')
                navigate(getDefaultAuthenticatedPath(data.user), { replace: true })
              } catch (error) {
                if (error.code === 'auth/popup-closed-by-user') {
                  return
                }
                if (error.code === 'firebase/not-configured') {
                  toast.error(error.message)
                  return
                }
                toast.error(error.response?.data?.error || 'Đăng ký Google thất bại')
              }
            }}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Đăng ký với Google</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
