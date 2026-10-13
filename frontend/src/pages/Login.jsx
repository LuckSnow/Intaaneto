import { useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Bot,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  Sparkles,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import AuthLayout from '../components/auth/AuthLayout'
import studentAiTutorIllustration from '../assets/images/student-ai-tutor-login.webp'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { getPostLoginPath } from '../utils/authNavigation'

function GoogleIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.56c2.08-1.92 3.28-4.74 3.28-8.09Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.56-2.76c-.99.66-2.24 1.05-3.72 1.05-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1A6.6 6.6 0 0 1 5.49 12c0-.73.13-1.43.35-2.1V7.07H2.18A11 11 0 0 0 1 12c0 1.78.43 3.45 1.18 4.93l3.66-2.83Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A10.58 10.58 0 0 0 12 1a11 11 0 0 0-9.82 6.07L5.84 9.9A6.57 6.57 0 0 1 12 5.38Z" />
    </svg>
  )
}

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const emailInputRef = useRef(null)
  const { login, googleLogin, isLoading } = useAuthStore()
  const [needVerification, setNeedVerification] = useState(false)
  const [verifyEmail, setVerifyEmail] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [formData, setFormData] = useState({ email: '', password: '' })

  const handleSubmit = async (event) => {
    event.preventDefault()
    setNeedVerification(false)
    try {
      const data = await login({ ...formData, remember })
      toast.success('Đăng nhập thành công!')
      navigate(getPostLoginPath(data.user, location.state?.from), { replace: true })
    } catch (error) {
      const errorData = error.response?.data
      if (errorData?.need_verification) {
        setNeedVerification(true)
        setVerifyEmail(errorData.email || formData.email)
        toast.error(errorData.error)
      } else if (errorData?.email) {
        toast.error(`Email: ${errorData.email[0]}`)
      } else if (errorData?.password) {
        toast.error(`Mật khẩu: ${errorData.password[0]}`)
      } else {
        toast.error(errorData?.error || 'Đăng nhập thất bại')
      }
    }
  }

  const handleGoogleLogin = async () => {
    try {
      const data = await googleLogin(remember)
      toast.success('Đăng nhập Google thành công!')
      navigate(getPostLoginPath(data.user, location.state?.from), { replace: true })
    } catch (error) {
      if (error.code === 'auth/popup-closed-by-user') return
      toast.error(
        error.code === 'firebase/not-configured'
          ? error.message
          : error.response?.data?.error || 'Đăng nhập Google thất bại',
      )
    }
  }

  const handleResendVerification = async () => {
    try {
      await api.post('/auth/resend_verification/', { email: verifyEmail })
      toast.success('Email xác thực đã được gửi lại!')
    } catch {
      toast.error('Chưa thể gửi lại email. Vui lòng thử lại sau.')
    }
  }

  return (
    <AuthLayout>
      <section className="auth-surface student-auth-shell relative w-full max-w-6xl bg-black/25 backdrop-blur-md">
        <div className="student-auth-visual order-2 relative overflow-hidden bg-[#FFF8EF]/95 p-6 sm:p-8 md:order-1 lg:p-10">
          <div className="pointer-events-none absolute -left-12 top-16 h-32 w-32 rounded-full bg-orange-200/35" />
          <div className="pointer-events-none absolute right-10 top-10 h-14 w-14 rounded-full bg-orange-100" />

          <div className="relative z-10 mx-auto max-w-xl">
            <div className="relative">
              <img
                src={studentAiTutorIllustration}
                alt="Học viên học trên laptop cùng trợ giảng AI"
                className="mx-auto max-h-[350px] w-full object-contain"
              />

              <aside className="mx-auto -mt-3 max-w-md rounded-2xl border border-orange-200 bg-white p-4 shadow-[0_10px_32px_rgba(249,115,22,0.12)] sm:absolute sm:bottom-2 sm:right-0 sm:mx-0 sm:w-[min(78%,22rem)]">
                <div className="flex items-center gap-2 text-orange-700">
                  <Bot size={19} aria-hidden="true" />
                  <p className="text-sm font-bold">AI Tutor</p>
                </div>
                <p className="mt-2 text-sm leading-5 text-slate-700">
                  “Sẵn sàng tiếp tục bài học của bạn?”
                </p>
                <button
                  type="button"
                  onClick={() => emailInputRef.current?.focus()}
                  className="mt-3 inline-flex min-h-10 items-center rounded-lg bg-orange-100 px-3 text-sm font-semibold text-orange-800 transition hover:bg-orange-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                >
                  Tiếp tục học
                </button>
              </aside>
            </div>

            <div className="mt-6 max-w-lg sm:mt-8">
              <h2 className="text-xl font-bold text-slate-950">Học thông minh hơn cùng AI Tutor</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Hỏi đáp và theo dõi tiến độ trong cùng một không gian học tập.
              </p>
            </div>
          </div>
        </div>

        <div className="student-auth-form order-1 relative flex items-center bg-[#A93612]/90 p-6 text-white backdrop-blur-md sm:p-8 md:order-2 lg:px-11">
          <div className="mx-auto w-full max-w-sm py-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-orange-100 ring-1 ring-white/15">
              <Sparkles aria-hidden="true" size={22} />
            </div>
            <h1 className="mt-4 text-3xl font-bold">Chào mừng bạn trở lại</h1>

            {needVerification && (
              <div role="alert" className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
                <p>Email chưa được xác thực. Vui lòng kiểm tra hộp thư của bạn.</p>
                <button
                  type="button"
                  onClick={handleResendVerification}
                  className="mt-2 font-semibold text-orange-800 underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                >
                  Gửi lại email xác thực
                </button>
              </div>
            )}

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="student-email" className="text-sm font-semibold text-white">
                  Email hoặc mã học viên
                </label>
                <div className="relative mt-2">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                  <input
                    ref={emailInputRef}
                    id="student-email"
                    name="email"
                    type="text"
                    autoComplete="username"
                    required
                    value={formData.email}
                    onChange={(event) => setFormData({ ...formData, email: event.target.value })}
                    className="auth-input pl-10 pr-3"
                    placeholder="Nhập email hoặc mã học viên"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="student-password" className="text-sm font-semibold text-white">
                  Mật khẩu
                </label>
                <div className="relative mt-2">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                  <input
                    id="student-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={(event) => setFormData({ ...formData, password: event.target.value })}
                    className="auth-input pl-10 pr-12"
                    placeholder="Nhập mật khẩu"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute right-1 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  >
                    {showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 text-sm">
                <label className="flex min-h-11 cursor-pointer items-center gap-2 text-white/85">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(event) => setRemember(event.target.checked)}
                    className="h-4 w-4 rounded border-white/40 accent-orange-500"
                  />
                  Ghi nhớ đăng nhập
                </label>
                <Link to="/forgot-password" className="font-semibold text-orange-100 underline-offset-4 hover:text-white hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-100">
                  Quên mật khẩu?
                </Link>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="auth-primary-button"
              >
                {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
              </Button>
            </form>

            <div className="my-5 flex items-center gap-3" aria-hidden="true">
              <span className="h-px flex-1 bg-white/25" />
              <span className="text-xs font-medium uppercase text-white/70">Hoặc</span>
              <span className="h-px flex-1 bg-white/25" />
            </div>

            <Button
              type="button"
              variant="outline"
              disabled={isLoading}
              onClick={handleGoogleLogin}
              className="min-h-12 w-full gap-3 border-white bg-white text-slate-800 hover:bg-orange-50 hover:text-slate-950 focus-visible:ring-orange-100"
            >
              <GoogleIcon />
              Đăng nhập với Google
            </Button>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-3 gap-y-2 border-t border-white/20 pt-5 text-sm text-white/80">
              <span>
                Chưa có tài khoản?{' '}
                <Link to="/register" className="auth-link text-white">
                  Đăng ký
                </Link>
              </span>
              <span aria-hidden="true" className="text-white/35">•</span>
              <Link to="/teacher/login" className="auth-link">
                Cổng giáo viên
              </Link>
            </div>
          </div>
        </div>
      </section>
    </AuthLayout>
  )
}
