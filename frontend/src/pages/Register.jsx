import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'
import { ROLES } from '../utils/constants'

export default function Register() {
  const navigate = useNavigate()
  const { register: registerUser, isLoading } = useAuthStore()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    password_confirm: '',
    role: ROLES.STUDENT,
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (formData.password !== formData.password_confirm) {
      toast.error('Mật khẩu không khớp')
      return
    }
    try {
      await registerUser(formData)
      toast.success('Đăng ký thành công!')
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Đăng ký thất bại')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="text-center text-3xl font-bold text-gray-900">
            Đăng ký tài khoản
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Đã có tài khoản?{' '}
            <a href="/login" className="text-primary-600 hover:text-primary-500">
              Đăng nhập
            </a>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                required
                className="input mt-1"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Tên đăng nhập</label>
              <input
                type="text"
                required
                className="input mt-1"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Họ và tên</label>
              <input
                type="text"
                required
                className="input mt-1"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Vai trò</label>
              <select
                className="input mt-1"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                <option value={ROLES.STUDENT}>Học sinh</option>
                <option value={ROLES.TEACHER}>Giáo viên</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Mật khẩu</label>
              <input
                type="password"
                required
                minLength={8}
                className="input mt-1"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Xác nhận mật khẩu</label>
              <input
                type="password"
                required
                minLength={8}
                className="input mt-1"
                value={formData.password_confirm}
                onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn btn-primary"
          >
            {isLoading ? 'Đang xử lý...' : 'Đăng ký'}
          </button>
        </form>
      </div>
    </div>
  )
}
