import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { Button } from '@/components/ui/button'
import api from '../services/api'
import toast from 'react-hot-toast'

const ROLE_LABELS = {
  student: 'Học sinh',
  teacher: 'Giáo viên',
  admin: 'Quản trị viên',
}

const ROLE_COLORS = {
  student: 'bg-blue-100 text-blue-700',
  teacher: 'bg-orange-100 text-orange-700',
  admin: 'bg-red-100 text-red-700',
}

export default function Profile() {
  const { user, updateUser } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)
  const [showUpgrade, setShowUpgrade] = useState(false)
  const [loading, setLoading] = useState(false)

  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    phone_number: user?.phone_number || '',
    date_of_birth: user?.date_of_birth || '',
    bio: user?.bio || '',
  })

  const [upgradeData, setUpgradeData] = useState({
    specialization: '',
    years_of_experience: 0,
    reason: '',
  })

  const userAvatar = user?.google_avatar || user?.avatar || null

  const handleSave = async () => {
    setLoading(true)
    try {
      const res = await api.patch('/auth/users/update_profile/', formData)
      updateUser(res.data)
      toast.success('Cập nhật hồ sơ thành công!')
      setIsEditing(false)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Cập nhật thất bại')
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = async () => {
    if (!upgradeData.specialization.trim()) {
      toast.error('Vui lòng nhập chuyên môn của bạn')
      return
    }
    setLoading(true)
    try {
      const res = await api.post('/auth/users/upgrade_to_teacher/', upgradeData)
      updateUser(res.data.user)
      toast.success(res.data.message)
      setShowUpgrade(false)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Nâng cấp thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Profile Header Card */}
      <div className="bg-orange-50 rounded-2xl shadow-md overflow-hidden">
        {/* Cover */}
        <div className="h-32 bg-gradient-to-r from-orange-400 via-amber-400 to-yellow-300 relative">
          <div className="absolute inset-0 bg-black/10"></div>
        </div>
        {/* Avatar + Info */}
        <div className="px-8 pb-8 -mt-16 relative">
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-6">
            {/* Avatar */}
            <div className="relative">
              {userAvatar ? (
                <img
                  src={userAvatar}
                  alt={user?.full_name}
                  className="w-28 h-28 rounded-2xl object-cover border-4 border-white shadow-lg"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-28 h-28 rounded-2xl bg-gradient-to-br from-orange-400 to-amber-400 flex items-center justify-center border-4 border-white shadow-lg">
                  <span className="text-4xl font-bold text-white">
                    {user?.full_name?.charAt(0) || 'U'}
                  </span>
                </div>
              )}
              {user?.is_verified && (
                <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-green-500 rounded-full flex items-center justify-center border-2 border-white">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </div>
            {/* Name + Role */}
            <div className="flex-1">
              <h1 className="text-2xl font-heading font-bold text-gray-900">{user?.full_name}</h1>
              <p className="text-gray-500 text-sm">@{user?.username}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${ROLE_COLORS[user?.role] || 'bg-gray-100 text-gray-600'}`}>
                  {ROLE_LABELS[user?.role] || user?.role}
                </span>
                {user?.is_verified && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                    ✓ Đã xác thực
                  </span>
                )}
              </div>
            </div>
            {/* Edit Button */}
            <Button
              onClick={() => setIsEditing(!isEditing)}
              className="rounded-full bg-black hover:bg-gray-800 text-white font-semibold px-6 border-0 shadow-md"
            >
              {isEditing ? 'Hủy' : 'Chỉnh sửa'}
            </Button>
          </div>
        </div>
      </div>

      {/* Info Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Personal Info */}
        <div className="bg-orange-50 rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-heading font-bold text-gray-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Thông tin cá nhân
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Họ và tên</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 font-medium mt-1">{user?.full_name || '—'}</p>
              )}
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Email</label>
              <p className="text-gray-900 font-medium mt-1">{user?.email}</p>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Số điện thoại</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  placeholder="0912345678"
                  className="w-full mt-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 font-medium mt-1">{user?.phone_number || '—'}</p>
              )}
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Ngày sinh</label>
              {isEditing ? (
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 font-medium mt-1">{user?.date_of_birth || '—'}</p>
              )}
            </div>
          </div>
          {isEditing && (
            <Button
              onClick={handleSave}
              disabled={loading}
              className="mt-6 w-full rounded-full bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white font-bold border-0 shadow-md"
            >
              {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          )}
        </div>

        {/* Bio & Account */}
        <div className="space-y-6">
          {/* Bio */}
          <div className="bg-orange-50 rounded-2xl shadow-md p-6">
            <h2 className="text-lg font-heading font-bold text-gray-800 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Giới thiệu
            </h2>
            {isEditing ? (
              <textarea
                value={formData.bio}
                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                rows={4}
                placeholder="Viết vài dòng về bạn..."
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent resize-none"
              />
            ) : (
              <p className="text-gray-700 leading-relaxed">{user?.bio || 'Chưa có thông tin giới thiệu.'}</p>
            )}
          </div>

          {/* Account Stats */}
          <div className="bg-orange-50 rounded-2xl shadow-md p-6">
            <h2 className="text-lg font-heading font-bold text-gray-800 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Tài khoản
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-orange-500">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString('vi-VN') : '—'}
                </p>
                <p className="text-xs text-gray-500 mt-1">Ngày tham gia</p>
              </div>
              <div className="bg-white rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-orange-500">
                  {ROLE_LABELS[user?.role] || '—'}
                </p>
                <p className="text-xs text-gray-500 mt-1">Vai trò</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Teacher Upgrade Module */}
      {user?.role === 'student' && (
        <div className="bg-orange-50 rounded-2xl shadow-md overflow-hidden">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-amber-400 rounded-xl flex items-center justify-center shadow-md">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-heading font-bold text-gray-800">Trở thành Giáo viên</h2>
                  <p className="text-sm text-gray-500">Nâng cấp tài khoản để tạo và quản lý khóa học</p>
                </div>
              </div>
              <Button
                onClick={() => setShowUpgrade(!showUpgrade)}
                className="rounded-full bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white font-bold border-0 shadow-md px-6"
              >
                {showUpgrade ? 'Đóng' : 'Nâng cấp'}
              </Button>
            </div>

            {showUpgrade && (
              <div className="mt-6 pt-6 border-t border-orange-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Chuyên môn *</label>
                    <input
                      type="text"
                      value={upgradeData.specialization}
                      onChange={(e) => setUpgradeData({ ...upgradeData, specialization: e.target.value })}
                      placeholder="VD: Lập trình Python, Web Development..."
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Số năm kinh nghiệm</label>
                    <input
                      type="number"
                      min="0"
                      value={upgradeData.years_of_experience}
                      onChange={(e) => setUpgradeData({ ...upgradeData, years_of_experience: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Lý do muốn trở thành giáo viên</label>
                  <textarea
                    value={upgradeData.reason}
                    onChange={(e) => setUpgradeData({ ...upgradeData, reason: e.target.value })}
                    rows={3}
                    placeholder="Chia sẻ lý do bạn muốn giảng dạy trên nền tảng..."
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-orange-400 focus:border-transparent resize-none"
                  />
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <Button
                    onClick={handleUpgrade}
                    disabled={loading}
                    className="rounded-full bg-black hover:bg-gray-800 text-white font-bold border-0 shadow-md px-8"
                  >
                    {loading ? 'Đang xử lý...' : 'Xác nhận nâng cấp'}
                  </Button>
                  <p className="text-xs text-gray-500">Sau khi nâng cấp, bạn có thể tạo và quản lý khóa học.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Teacher Info (if already teacher) */}
      {user?.role === 'teacher' && (
        <div className="bg-orange-50 rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-amber-400 rounded-xl flex items-center justify-center shadow-md">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-heading font-bold text-gray-800">Bạn là Giáo viên</h2>
              <p className="text-sm text-gray-500">Bạn có thể tạo và quản lý các khóa học trên nền tảng</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
