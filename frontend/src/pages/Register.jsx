import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Bot,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  UserRound,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import AuthLayout from '../components/auth/AuthLayout'
import studentAiTutorIllustration from '../assets/images/student-ai-tutor-login.png'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { getDefaultAuthenticatedPath } from '../utils/authNavigation'

const PASSWORD_RULES = [
  { key: 'length', label: 'Ít nhất 8 ký tự', test: (password) => password.length >= 8 },
  { key: 'upper', label: '1 chữ cái viết hoa', test: (password) => /[A-Z]/.test(password) },
  { key: 'lower', label: '1 chữ cái viết thường', test: (password) => /[a-z]/.test(password) },
  { key: 'digit', label: '1 chữ số', test: (password) => /\d/.test(password) },
  { key: 'special', label: '1 ký tự đặc biệt', test: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password) },
]

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

export default function Register() {
  const navigate = useNavigate()
  const { register: registerUser, googleLogin, isLoading } = useAuthStore()
  const [registrationResult, setRegistrationResult] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    password_confirm: '',
  })

  const passwordStrength = useMemo(() => {
    const passed = PASSWORD_RULES.filter((rule) => rule.test(formData.password)).length
    return {
      passed,
      total: PASSWORD_RULES.length,
      percent: Math.round((passed / PASSWORD_RULES.length) * 100),
    }
  }, [formData.password])

  const strengthColor = passwordStrength.percent <= 40
    ? 'bg-red-500'
    : passwordStrength.percent <= 80
      ? 'bg-amber-400'
      : 'bg-emerald-500'
  const strengthLabel = passwordStrength.percent <= 40
    ? 'Yếu'
    : passwordStrength.percent <= 80
      ? 'Trung bình'
      : 'Mạnh'

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (formData.password !== formData.password_confirm) {
      toast.error('Mật khẩu không khớp')
      return
    }
    if (passwordStrength.passed < PASSWORD_RULES.length) {
      toast.error('Mật khẩu chưa đủ yêu cầu')
      return
    }
    try {
      const result = await registerUser(formData)
      setRegistrationResult({ emailSent: result.email_sent === true })
    } catch (error) {
      const errorData = error.response?.data
      if (errorData?.email) {
        toast.error(`Email: ${errorData.email[0]}`)
      } else if (errorData?.username) {
        toast.error(`Tên đăng nhập: ${errorData.username[0]}`)
      } else if (errorData?.password) {
        toast.error(`Mật khẩu: ${errorData.password[0]}`)
      } else {
        toast.error(errorData?.error || 'Đăng ký thất bại')
      }
    }
  }

  const handleGoogleRegistration = async () => {
    try {
      const data = await googleLogin()
      toast.success('Đăng ký Google thành công!')
      navigate(getDefaultAuthenticatedPath(data.user), { replace: true })
    } catch (error) {
      if (error.code === 'auth/popup-closed-by-user') return
      toast.error(
        error.code === 'firebase/not-configured'
          ? error.message
          : error.response?.data?.error || 'Đăng ký Google thất bại',
      )
    }
  }

  if (registrationResult) {
    const emailSent = registrationResult.emailSent
    return (
      <AuthLayout>
        <section className="auth-surface relative w-full max-w-lg bg-[#A93612]/90 p-7 text-center text-white backdrop-blur-md sm:p-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
            <Mail size={27} aria-hidden="true" />
          </div>
          <h1 className="mt-5 text-2xl font-bold">
            {emailSent ? 'Kiểm tra email của bạn!' : 'Tài khoản đã được tạo'}
          </h1>
          <p className="mt-3 text-sm leading-6 text-white/80">
            {emailSent ? 'Chúng tôi đã gửi email xác thực đến ' : 'Chưa thể gửi email xác thực đến '}
            <strong className="text-orange-100">{formData.email}</strong>
          </p>
          <p className="mt-2 text-sm leading-6 text-white/65">
            {emailSent
              ? 'Vui lòng mở liên kết trong email để kích hoạt tài khoản.'
              : 'Tài khoản vẫn cần được xác thực trước khi đăng nhập. Bạn có thể thử gửi lại email.'}
          </p>
          <div className="mt-7 space-y-3">
            <Button onClick={() => navigate('/login')} className="min-h-12 w-full bg-gradient-to-r from-orange-500 to-orange-400 font-bold text-white hover:from-orange-600 hover:to-orange-500">
              Đi đến trang đăng nhập
            </Button>
            <button
              type="button"
              onClick={async () => {
                try {
                  await api.post('/auth/resend_verification/', { email: formData.email })
                  toast.success('Nếu tài khoản đang chờ xác thực, email hướng dẫn sẽ được gửi.')
                } catch {
                  toast.error('Chưa thể gửi lại email. Vui lòng thử lại sau.')
                }
              }}
              className="min-h-11 text-sm font-semibold text-orange-100 underline underline-offset-4 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-100"
            >
              Gửi lại email xác thực
            </button>
          </div>
        </section>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <section className="auth-surface register-auth-shell relative w-full max-w-7xl bg-black/25 backdrop-blur-md">
        <div className="register-auth-visual order-2 relative overflow-hidden bg-[#FFF8EF]/95 p-6 sm:p-8 md:order-1 lg:p-10">
          <div className="pointer-events-none absolute -left-10 top-16 h-28 w-28 rounded-full bg-orange-200/35" />
          <div className="pointer-events-none absolute right-12 top-10 h-14 w-14 rounded-full bg-orange-100" />

          <div className="relative z-10 mx-auto max-w-xl">
            <div className="relative">
              <img
                src={studentAiTutorIllustration}
                alt="Học viên bắt đầu học cùng trợ giảng AI"
                className="mx-auto max-h-[330px] w-full object-contain"
              />
              <aside className="mx-auto -mt-2 max-w-sm rounded-2xl border border-orange-200 bg-white p-4 shadow-[0_10px_30px_rgba(249,115,22,0.1)] sm:absolute sm:bottom-2 sm:right-0 sm:mx-0 sm:w-[min(74%,21rem)]">
                <div className="flex items-center gap-2 text-orange-700">
                  <Bot size={18} aria-hidden="true" />
                  <p className="text-sm font-bold">AI Tutor</p>
                </div>
                <p className="mt-2 text-sm leading-5 text-slate-700">
                  “Tạo tài khoản và bắt đầu bài học đầu tiên.”
                </p>
              </aside>
            </div>

            <div className="mt-7 max-w-lg sm:mt-8">
              <h2 className="text-xl font-bold text-slate-950">Bắt đầu hành trình học tập thông minh</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Học, hỏi đáp và theo dõi tiến độ cùng AI Tutor.
              </p>
            </div>
          </div>
        </div>

        <div className="register-auth-form order-1 relative flex items-center bg-[#A93612]/90 p-6 text-white backdrop-blur-md sm:p-8 md:order-2 lg:px-10">
          <div className="mx-auto w-full max-w-xl py-2">
            <h1 className="text-3xl font-bold">Tạo tài khoản học viên</h1>
            <p className="mt-2 text-sm text-white/75">
              Đã có tài khoản?{' '}
              <Link to="/login" className="auth-link text-white">
                Đăng nhập
              </Link>
            </p>

            <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="register-email" className="text-sm font-semibold">Email</label>
                <div className="relative mt-1.5">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                    <input id="register-email" name="email" type="email" autoComplete="email" required value={formData.email} onChange={(event) => setFormData({ ...formData, email: event.target.value })} className="auth-input pl-10 pr-3" placeholder="Nhập địa chỉ email" />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="register-username" className="text-sm font-semibold">Tên đăng nhập</label>
                  <div className="relative mt-1.5">
                    <UserRound className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                    <input id="register-username" name="username" type="text" autoComplete="username" required value={formData.username} onChange={(event) => setFormData({ ...formData, username: event.target.value })} className="auth-input pl-10 pr-3" placeholder="Nhập tên đăng nhập" />
                  </div>
                </div>
                <div>
                  <label htmlFor="register-full-name" className="text-sm font-semibold">Họ và tên</label>
                  <div className="relative mt-1.5">
                    <UserRound className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                    <input id="register-full-name" name="full_name" type="text" autoComplete="name" required value={formData.full_name} onChange={(event) => setFormData({ ...formData, full_name: event.target.value })} className="auth-input pl-10 pr-3" placeholder="Nhập họ và tên" />
                  </div>
                </div>
              </div>

              <div>
                <label htmlFor="register-password" className="text-sm font-semibold">Mật khẩu</label>
                <div className="relative mt-1.5">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                  <input id="register-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="new-password" required value={formData.password} onChange={(event) => setFormData({ ...formData, password: event.target.value })} className="auth-input pl-10 pr-12" placeholder="Tạo mật khẩu" />
                  <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-1 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}>
                    {showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
                  </button>
                </div>
                <p className="mt-1.5 text-xs text-white/70">Tối thiểu 8 ký tự, gồm chữ và số.</p>
                {formData.password && (
                  <div className="mt-2 flex items-center gap-2" aria-label={`Mức độ mạnh mật khẩu: ${strengthLabel}`}>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/20">
                      <div className={`h-full rounded-full ${strengthColor} transition-[width] duration-200`} style={{ width: `${passwordStrength.percent}%` }} />
                    </div>
                    <span className="text-xs font-medium text-white/80">{strengthLabel}</span>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="register-confirm-password" className="text-sm font-semibold">Xác nhận mật khẩu</label>
                <div className="relative mt-1.5">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} aria-hidden="true" />
                  <input id="register-confirm-password" name="password_confirm" type={showConfirm ? 'text' : 'password'} autoComplete="new-password" required value={formData.password_confirm} onChange={(event) => setFormData({ ...formData, password_confirm: event.target.value })} aria-invalid={Boolean(formData.password_confirm && formData.password !== formData.password_confirm)} aria-describedby="confirm-password-error" className="auth-input pl-10 pr-12" placeholder="Nhập lại mật khẩu" />
                  <button type="button" onClick={() => setShowConfirm((value) => !value)} className="absolute right-1 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600" aria-label={showConfirm ? 'Ẩn mật khẩu xác nhận' : 'Hiện mật khẩu xác nhận'}>
                    {showConfirm ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
                  </button>
                </div>
                <p id="confirm-password-error" className="mt-1 min-h-4 text-xs text-orange-100" aria-live="polite">
                  {formData.password_confirm && formData.password !== formData.password_confirm ? 'Mật khẩu xác nhận không khớp' : ''}
                </p>
              </div>

              <label className="flex cursor-pointer items-start gap-2 text-xs leading-5 text-white/80">
                <input type="checkbox" required checked={acceptedTerms} onChange={(event) => setAcceptedTerms(event.target.checked)} className="mt-0.5 h-4 w-4 shrink-0 rounded border-white/40 accent-orange-500" />
                <span>Tôi đồng ý với <span className="font-semibold text-orange-100">Điều khoản sử dụng</span> và <span className="font-semibold text-orange-100">Chính sách bảo mật</span>.</span>
              </label>

              <Button type="submit" disabled={isLoading || !acceptedTerms} className="auth-primary-button disabled:opacity-55">
                {isLoading ? 'Đang xử lý...' : 'Tạo tài khoản'}
              </Button>
            </form>

            <div className="my-4 flex items-center gap-3" aria-hidden="true">
              <span className="h-px flex-1 bg-white/25" />
              <span className="text-xs font-medium uppercase text-white/70">Hoặc</span>
              <span className="h-px flex-1 bg-white/25" />
            </div>

            <Button type="button" disabled={isLoading} onClick={handleGoogleRegistration} variant="outline" className="min-h-12 w-full gap-3 border-white bg-white text-slate-800 hover:bg-orange-50 hover:text-slate-950 focus-visible:ring-orange-100">
              <GoogleIcon />
              Đăng ký với Google
            </Button>

            <p className="mt-5 border-t border-white/20 pt-4 text-center text-sm text-white/80">
              <Link to="/teacher/login" className="auth-link text-white">
                Mở cổng giáo viên
              </Link>
            </p>
          </div>
        </div>
      </section>
    </AuthLayout>
  )
}
