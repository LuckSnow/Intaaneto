import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LockKeyhole, Mail, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import { authService } from '../services/authService'
import { useAuthStore } from '../store/authStore'


export default function TeacherLogin() {
  const navigate = useNavigate()
  const { teacherLogin, isLoading } = useAuthStore()
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

  const handleResend = async () => {
    try {
      const response = await authService.resendVerification(formData.email)
      toast.success(response.message)
    } catch {
      toast.error('Chưa thể xử lý yêu cầu. Vui lòng thử lại sau.')
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:py-16">
      <div className="mx-auto w-full max-w-md">
        <Link
          to="/"
          className="mb-8 inline-flex min-h-11 items-center text-lg font-semibold text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600 focus-visible:ring-offset-2"
        >
          Intaaneto
        </Link>

        <section className="rounded-xl border border-slate-200 bg-white p-6 sm:p-8">
          <div className="mb-6">
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-orange-50 text-orange-700">
              <ShieldCheck aria-hidden="true" size={22} />
            </div>
            <h1 className="text-2xl font-semibold text-slate-950">
              Đăng nhập giáo viên
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Truy cập khu vực tải và quản lý học liệu. Tài khoản giáo viên phải
              được quản trị viên cấp quyền và xác thực email trước khi đăng nhập.
            </p>
          </div>

          {errorMessage && (
            <div
              role="alert"
              className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
            >
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

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="teacher-email" className="text-sm font-medium text-slate-800">
                Email công việc
              </label>
              <div className="relative mt-2">
                <Mail
                  aria-hidden="true"
                  size={18}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                />
                <input
                  id="teacher-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={(event) => setFormData({
                    ...formData,
                    email: event.target.value,
                  })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 bg-white py-2 pl-10 pr-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20"
                  placeholder="giaovien@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="teacher-password" className="text-sm font-medium text-slate-800">
                Mật khẩu
              </label>
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
              type="submit"
              disabled={isLoading}
              className="min-h-11 w-full bg-orange-700 text-white hover:bg-orange-800 focus-visible:ring-orange-600"
            >
              {isLoading ? 'Đang đăng nhập…' : 'Đăng nhập cổng giáo viên'}
            </Button>
          </form>

          <p className="mt-6 border-t border-slate-200 pt-5 text-center text-sm text-slate-600">
            Bạn là học viên?{' '}
            <Link
              to="/login"
              className="font-semibold text-orange-700 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
            >
              Đăng nhập tại đây
            </Link>
          </p>
        </section>
      </div>
    </main>
  )
}
