import { useState } from 'react'
import { ArrowLeft, CheckCircle2, Mail } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import AuthLayout from '../components/auth/AuthLayout'
import { authService } from '../services/authService'

export default function ForgotPassword() {
  const [searchParams] = useSearchParams()
  const teacherPortal = searchParams.get('portal') === 'teacher'
  const loginPath = teacherPortal ? '/teacher/login' : '/login'
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)
    setError('')
    try {
      const response = await authService.requestPasswordReset(email)
      setMessage(response.message)
    } catch {
      setError('Chưa thể xử lý yêu cầu. Vui lòng thử lại sau.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="relative z-10 w-full max-w-[460px]">
        <section className="auth-card p-6 sm:p-8">
          <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${message ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'}`}>
            {message
              ? <CheckCircle2 aria-hidden="true" size={24} />
              : <Mail aria-hidden="true" size={24} />}
          </div>

          <h1 className="mt-5 text-2xl font-bold text-slate-900">
            {message ? 'Kiểm tra hộp thư của bạn' : 'Quên mật khẩu?'}
          </h1>

          {message ? (
            <div role="status" className="mt-3">
              <p className="text-sm leading-6 text-slate-600">
                Đã gửi liên kết đặt lại mật khẩu. Vui lòng kiểm tra hộp thư của bạn.
              </p>
              <Link
                to={loginPath}
                className="mt-6 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-orange-700 underline-offset-4 hover:text-orange-800 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
              >
                <ArrowLeft aria-hidden="true" size={17} />
                Quay lại đăng nhập
              </Link>
            </div>
          ) : (
            <>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Nhập email đã đăng ký. Chúng tôi sẽ gửi cho bạn liên kết để đặt lại mật khẩu.
              </p>

              <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
                {error && (
                  <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    {error}
                  </div>
                )}

                <div>
                  <label htmlFor="reset-email" className="text-sm font-semibold text-slate-800">
                    Email tài khoản
                  </label>
                  <div className="relative mt-2">
                    <Mail
                      aria-hidden="true"
                      size={18}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                    />
                    <input
                      id="reset-email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className="auth-input min-h-[52px] pl-10 pr-3"
                      placeholder="Nhập địa chỉ email"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="auth-primary-button"
                >
                  {isSubmitting ? 'Đang gửi…' : 'Gửi liên kết đặt lại'}
                </Button>
              </form>

              <Link
                to={loginPath}
                className="mt-5 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-orange-700 underline-offset-4 hover:text-orange-800 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
              >
                <ArrowLeft aria-hidden="true" size={17} />
                Quay lại đăng nhập
              </Link>
            </>
          )}
        </section>
      </div>
    </AuthLayout>
  )
}
