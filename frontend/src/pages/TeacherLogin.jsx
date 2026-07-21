import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  LockKeyhole,
  Mail,
  ShieldCheck,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import logoFull from '../assets/images/logo-full.png'
import teacherLoginIllustration from '../assets/images/teacher-login-illustration.png'
import { authService } from '../services/authService'
import { useAuthStore } from '../store/authStore'


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

export default function TeacherLogin() {
  const navigate = useNavigate()
  const { teacherLogin, teacherGoogleLogin, isLoading } = useAuthStore()
  const [needVerification, setNeedVerification] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [formData, setFormData] = useState({ email: '', password: '' })

  const handleSubmit = async (event) => {
    event.preventDefault()
    setNeedVerification(false)
    setErrorMessage('')
    try {
      await teacherLogin(formData)
      toast.success('Đăng nhập cổng giáo viên thành công')
      navigate('/teacher/upload', { replace: true })
    } catch (error) {
      const response = error.response?.data
      setNeedVerification(Boolean(response?.need_verification))
      setErrorMessage(response?.error || 'Không thể đăng nhập. Vui lòng thử lại.')
    }
  }

  const handleGoogleLogin = async () => {
    setNeedVerification(false)
    setErrorMessage('')
    try {
      await teacherGoogleLogin()
      toast.success('Đăng nhập Google vào cổng giáo viên thành công')
      navigate('/teacher/upload', { replace: true })
    } catch (error) {
      if (error.code === 'auth/popup-closed-by-user') return
      const message = error.code === 'firebase/not-configured'
        ? error.message
        : error.response?.data?.error || 'Không thể đăng nhập giáo viên bằng Google.'
      setErrorMessage(message)
    }
  }

  const handleResend = async () => {
    try {
      const response = await authService.resendVerification(formData.email)
      toast.success(response.message)
    } catch {
      toast.error('Chưa thể xử lý yêu cầu. Vui lòng thử lại sau.')
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-orange-950 px-4 py-7 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute -left-20 -top-20 h-72 w-72 rounded-full bg-orange-500/15" />
      <div className="pointer-events-none absolute -bottom-40 right-16 h-96 w-96 rounded-full bg-orange-600/15" />

      <section className="teacher-auth-shell relative w-full max-w-6xl overflow-hidden rounded-[2rem] border border-orange-200/20 bg-orange-800 shadow-2xl">
        <Link
          to="/"
          className="absolute right-7 top-5 z-30 block h-10 w-40 overflow-hidden rounded-md drop-shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-100 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-800 sm:right-9 sm:top-7"
          aria-label="Về trang chủ Intaaneto"
        >
          <img
            src={logoFull}
            alt="Intaaneto"
            className="pointer-events-none absolute left-1/2 top-1/2 w-40 max-w-none -translate-x-1/2 -translate-y-1/2"
          />
        </Link>

        <div className="teacher-auth-visual relative z-10 flex flex-col overflow-hidden bg-orange-50 p-7 sm:p-9 lg:p-11">
          <div className="pointer-events-none absolute left-10 top-28 h-20 w-20 rounded-full bg-orange-200/35" />
          <div className="pointer-events-none absolute right-[18%] top-16 h-12 w-12 rounded-full bg-orange-200/30" />
          <img
            src={teacherLoginIllustration}
            alt="Giáo viên hướng dẫn học viên học công nghệ cùng máy tính"
            className="relative z-10 my-auto w-full max-w-[620px] object-contain sm:-ml-3 sm:w-[92%] lg:w-full"
          />
          <div className="relative z-10 max-w-sm pb-3 sm:pb-0">
            <p className="text-sm font-semibold text-orange-700">Không gian dành cho giảng viên</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Quản lý học liệu, bài đánh giá và tiến độ học tập tại một nơi.
            </p>
          </div>
        </div>

        <div className="teacher-auth-form relative flex items-center bg-orange-800 p-6 text-white sm:p-7 lg:px-12">
          <div className="mx-auto w-full max-w-sm py-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-orange-100 ring-1 ring-white/15">
              <ShieldCheck aria-hidden="true" size={23} />
            </div>
            <h1 className="mt-5 text-3xl font-bold">Đăng nhập giáo viên</h1>
            <p className="mt-2 text-sm leading-6 text-orange-100">
              Truy cập khu vực quản lý nội dung và lớp học của bạn.
            </p>

            {errorMessage && (
              <div role="alert" className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                <p>{errorMessage}</p>
                {needVerification && (
                  <button
                    type="button"
                    onClick={handleResend}
                    className="mt-2 min-h-11 font-semibold text-orange-700 underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                  >
                    Gửi lại hướng dẫn xác thực
                  </button>
                )}
              </div>
            )}

            <div>
              <div className="flex items-center justify-between gap-4">
                <label htmlFor="teacher-password" className="text-sm font-medium text-slate-800">
                  Mật khẩu
                </label>
                <Link
                  to="/forgot-password?portal=teacher"
                  className="text-sm font-semibold text-orange-700 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                >
                  Quên mật khẩu?
                </Link>
              </div>
              <div className="relative mt-2">
                <LockKeyhole
                  aria-hidden="true"
                  size={18}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                />
                <input
                  id="teacher-password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={(event) => setFormData({
                    ...formData,
                    password: event.target.value,
                  })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 bg-white py-2 pl-10 pr-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20"
                  placeholder="Nhập mật khẩu"
                />
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              disabled={isLoading}
              onClick={handleGoogleLogin}
              className="min-h-12 w-full gap-3 border-white bg-white text-slate-800 hover:bg-orange-50 hover:text-slate-950 focus-visible:ring-orange-100"
            >
              <GoogleIcon />
              Đăng nhập giáo viên với Google
            </Button>
            <p className="mt-3 text-center text-xs leading-5 text-orange-100/75">
              Email Google phải trùng với tài khoản giáo viên đã được phê duyệt.
            </p>

            <p className="mt-7 border-t border-white/20 pt-5 text-center text-sm text-orange-100">
              Bạn là học viên?{' '}
              <Link to="/login" className="font-semibold text-white underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-100">
                Đăng nhập tại đây
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  )
}
