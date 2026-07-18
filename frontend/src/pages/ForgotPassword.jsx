import { useState } from 'react'
import { ArrowLeft, Mail } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
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
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:py-16">
      <div className="mx-auto w-full max-w-md">
        <Link
          to={loginPath}
          className="mb-8 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600 focus-visible:ring-offset-2"
        >
          <ArrowLeft aria-hidden="true" size={18} />
          Quay lại đăng nhập
        </Link>

        <section className="rounded-xl border border-slate-200 bg-white p-6 sm:p-8">
          <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg bg-orange-50 text-orange-700">
            <Mail aria-hidden="true" size={22} />
          </div>
          <h1 className="text-2xl font-semibold text-slate-950">Quên mật khẩu</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Nhập email tài khoản. Nếu tài khoản có thể đặt lại mật khẩu, chúng
            tôi sẽ gửi một liên kết có thời hạn đến hộp thư đó.
          </p>

          {message ? (
            <div role="status" className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm leading-6 text-emerald-800">
              <p>{message}</p>
              <p className="mt-2">Hãy kiểm tra cả Inbox, Spam và Promotions.</p>
            </div>
          ) : (
            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              {error && (
                <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {error}
                </div>
              )}
              <div>
                <label htmlFor="reset-email" className="text-sm font-medium text-slate-800">
                  Email tài khoản
                </label>
                <input
                  id="reset-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20"
                  placeholder="email@example.com"
                />
              </div>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="min-h-11 w-full bg-orange-700 text-white hover:bg-orange-800 focus-visible:ring-orange-600"
              >
                {isSubmitting ? 'Đang gửi…' : 'Gửi liên kết đặt lại'}
              </Button>
            </form>
          )}
        </section>
      </div>
    </main>
  )
}
