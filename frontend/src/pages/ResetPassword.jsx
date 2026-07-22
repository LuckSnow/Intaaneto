import { useState } from 'react'
import { CheckCircle2, LockKeyhole } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import AuthLayout from '../components/auth/AuthLayout'
import { authService } from '../services/authService'


export default function ResetPassword() {
  const { uid, token } = useParams()
  const [formData, setFormData] = useState({ password: '', password_confirm: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [loginPath, setLoginPath] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    if (formData.password !== formData.password_confirm) {
      setError('Mật khẩu xác nhận không khớp.')
      return
    }
    setIsSubmitting(true)
    try {
      const response = await authService.confirmPasswordReset({
        uid,
        token,
        ...formData,
      })
      setLoginPath(response.login_path || '/login')
    } catch (requestError) {
      const response = requestError.response?.data
      const passwordError = Array.isArray(response?.password)
        ? response.password[0]
        : response?.password
      setError(passwordError || response?.error || 'Không thể đặt lại mật khẩu. Vui lòng yêu cầu liên kết mới.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loginPath) {
    return (
      <AuthLayout>
        <section className="auth-card w-full max-w-md p-6 text-center sm:p-8">
          <CheckCircle2 aria-hidden="true" className="mx-auto text-emerald-700" size={40} />
          <h1 className="mt-4 text-2xl font-semibold text-slate-950">Đã đặt lại mật khẩu</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Các phiên đăng nhập cũ đã mất hiệu lực. Hãy đăng nhập lại bằng mật khẩu mới.
          </p>
          <Link
            to={loginPath}
            className="mt-6 inline-flex min-h-11 w-full items-center justify-center rounded-md bg-orange-700 px-4 py-2 text-sm font-medium text-white hover:bg-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600 focus-visible:ring-offset-2"
          >
            Đi đến trang đăng nhập
          </Link>
        </section>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <section className="auth-card w-full max-w-md p-6 sm:p-8">
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-orange-50 text-orange-700">
          <LockKeyhole aria-hidden="true" size={22} />
        </div>
        <h1 className="text-2xl font-semibold text-slate-950">Đặt mật khẩu mới</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Dùng ít nhất 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt.
        </p>

        <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
          {error && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="new-password" className="text-sm font-medium text-slate-800">Mật khẩu mới</label>
            <input
              id="new-password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              maxLength={128}
              value={formData.password}
              onChange={(event) => setFormData({ ...formData, password: event.target.value })}
              className="auth-input mt-2 px-3"
            />
          </div>
          <div>
            <label htmlFor="confirm-password" className="text-sm font-medium text-slate-800">Xác nhận mật khẩu</label>
            <input
              id="confirm-password"
              name="password_confirm"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              maxLength={128}
              value={formData.password_confirm}
              onChange={(event) => setFormData({ ...formData, password_confirm: event.target.value })}
              className="auth-input mt-2 px-3"
            />
          </div>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="auth-primary-button"
          >
            {isSubmitting ? 'Đang cập nhật…' : 'Đặt mật khẩu mới'}
          </Button>
        </form>
      </section>
    </AuthLayout>
  )
}
