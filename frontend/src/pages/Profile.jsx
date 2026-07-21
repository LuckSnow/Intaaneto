import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  BookOpen,
  Camera,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Edit3,
  Eye,
  GraduationCap,
  Mail,
  MessageCircle,
  Phone,
  ShieldCheck,
  UserRound,
  Users,
  XCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'
import { authService } from '../services/authService'
import { forumService } from '../services/forumService'
import api from '../services/api'

const ROLE_LABELS = {
  student: 'Học viên',
  teacher: 'Giảng viên',
  admin: 'Quản trị viên',
}

const ROLE_BADGES = {
  student: 'bg-blue-50 text-blue-700 border-blue-100',
  teacher: 'bg-orange-50 text-orange-700 border-orange-100',
  admin: 'bg-red-50 text-red-700 border-red-100',
}

const ACTIVITY_LEVELS = [
  'bg-slate-100',
  'bg-emerald-200',
  'bg-emerald-300',
  'bg-emerald-500',
  'bg-emerald-700',
]

const POST_CATEGORY_LABELS = {
  question: 'Câu hỏi',
  discussion: 'Thảo luận',
  showcase: 'Chia sẻ',
  announcement: 'Thông báo',
}

function formatJoinDate(value) {
  if (!value) return 'Chưa rõ'
  return new Date(value).toLocaleDateString('vi-VN', {
    month: 'long',
    year: 'numeric',
  })
}

function shortDate(value) {
  if (!value) return 'Chưa rõ'
  return new Date(value).toLocaleDateString('vi-VN')
}

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function makeActivityCells(activities) {
  const today = new Date()
  today.setHours(12, 0, 0, 0)
  const endOfCurrentWeek = new Date(today)
  endOfCurrentWeek.setDate(today.getDate() + (6 - today.getDay()))
  const gridStart = new Date(endOfCurrentWeek)
  gridStart.setDate(endOfCurrentWeek.getDate() - (53 * 7 - 1))
  const activityByDate = new Map(
    activities.map((activity) => [activity.date, Number(activity.login_count || 0)]),
  )
  const cells = Array.from({ length: 53 * 7 }, (_, index) => {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + index)
    const key = localDateKey(date)
    const isFuture = date > today
    const count = isFuture ? 0 : activityByDate.get(key) || 0
    return {
      key,
      date,
      count,
      isFuture,
      level: count === 0 ? 0 : Math.min(4, count),
    }
  })
  return cells
}

function ActivityGrid({ activities, loading }) {
  const cells = useMemo(() => makeActivityCells(activities), [activities])
  const activeCount = cells.filter((cell) => cell.level > 0).length
  const monthLabels = cells.reduce((labels, cell, index) => {
    if (cell.date.getDate() === 1) {
      labels.push({
        key: cell.key,
        label: cell.date.toLocaleDateString('en-US', { month: 'short' }),
        column: Math.floor(index / 7) + 1,
      })
    }
    return labels
  }, [])

  return (
    <section className="border-b border-slate-200 pb-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">
          {loading ? 'Đang tải hoạt động...' : `${activeCount} ngày hoạt động trong 12 tháng qua`}
        </h2>
        <button className="inline-flex items-center gap-2 self-start text-sm font-medium text-slate-600 hover:text-slate-950">
          Tùy chọn hiển thị
          <ChevronDown size={16} aria-hidden="true" />
        </button>
      </div>

      <div className="mt-7 overflow-x-auto pb-2">
        <div className="min-w-[884px]">
          <div
            className="ml-10 grid text-xs text-slate-700"
            style={{
              gridTemplateColumns: 'repeat(53, 0.75rem)',
              columnGap: '0.25rem',
            }}
          >
            {monthLabels.map((month) => (
              <span
                key={month.key}
                className="whitespace-nowrap"
                style={{ gridColumnStart: month.column }}
              >
                {month.label}
              </span>
            ))}
          </div>
          <div className="mt-2 flex gap-2">
            <div className="grid h-[104px] grid-rows-7 gap-1 text-xs text-slate-700">
              <span />
              <span>Mon</span>
              <span />
              <span>Wed</span>
              <span />
              <span>Fri</span>
              <span />
            </div>
            <div className="grid grid-flow-col grid-rows-7 gap-1">
              {cells.map((cell) => (
                <button
                  type="button"
                  key={cell.key}
                  title={cell.isFuture ? undefined : `${cell.count} lần đăng nhập · ${cell.date.toLocaleDateString('vi-VN', {
                    weekday: 'long',
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                  })}`}
                  aria-label={cell.isFuture ? undefined : `${shortDate(cell.date)}: ${cell.count} lần đăng nhập`}
                  disabled={cell.isFuture}
                  className={`h-3 w-3 rounded-[3px] ${ACTIVITY_LEVELS[cell.level]} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600 focus-visible:ring-offset-1 disabled:cursor-default`}
                />
              ))}
            </div>
          </div>
          <div className="mt-3 flex items-center justify-end gap-2 text-xs text-slate-500">
            <span>Ít hơn</span>
            {ACTIVITY_LEVELS.map((level) => (
              <span key={level} className={`h-3 w-3 rounded-[3px] ${level}`} />
            ))}
            <span>Nhiều hơn</span>
          </div>
        </div>
      </div>
    </section>
  )
}

function Avatar({ user, uploadingAvatar, onPickAvatar }) {
  const fileInputRef = useRef(null)
  const avatar = user?.avatar || user?.google_avatar || null
  const initial = user?.full_name?.trim()?.charAt(0)?.toUpperCase() || 'U'

  return (
    <div className="flex flex-col items-center lg:items-start">
      <div className="relative">
        {avatar ? (
          <img
            src={avatar}
            alt={user?.full_name || 'Ảnh đại diện'}
            className="h-56 w-56 rounded-full border border-slate-200 bg-slate-100 object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex h-56 w-56 items-center justify-center rounded-full border border-slate-200 bg-slate-100 text-6xl font-semibold text-slate-400">
            {initial}
          </div>
        )}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadingAvatar}
          className="absolute bottom-4 right-4 inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
          aria-label="Thay đổi ảnh đại diện"
        >
          <Camera size={19} aria-hidden="true" />
        </button>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="sr-only"
        onChange={onPickAvatar}
      />
      <p className="mt-3 text-sm text-slate-500">
        {uploadingAvatar ? 'Đang tải ảnh lên...' : 'PNG, JPG hoặc WebP tối đa 5MB'}
      </p>
    </div>
  )
}

function CourseCard({ enrollment }) {
  const courseId = enrollment.course
  const progress = Number(enrollment.progress_percentage || 0)

  return (
    <Link
      to={`/courses/${courseId}`}
      className="group overflow-hidden rounded-2xl border border-slate-200 bg-white transition hover:-translate-y-0.5 hover:border-orange-200 hover:shadow-md"
    >
      <div className="flex aspect-[16/9] items-center justify-center bg-gradient-to-br from-cyan-500 via-sky-500 to-blue-600 px-6 text-center">
        <div>
          <p className="text-3xl font-bold text-white">INTAANETO</p>
          <p className="mt-2 text-sm font-medium text-white/80">Khóa học đang theo dõi</p>
        </div>
      </div>
      <div className="space-y-4 p-5">
        <div>
          <h3 className="font-semibold text-slate-950 group-hover:text-orange-700">
            {enrollment.course_title}
          </h3>
          <p className="mt-2 text-sm font-semibold text-orange-700">Đã đăng ký</p>
        </div>
        <div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-orange-600"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
          <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
            <span>{progress.toFixed(0)}% tiến độ</span>
            <span>{Number(enrollment.mastery_percentage || 0).toFixed(0)}% mastery</span>
          </div>
        </div>
      </div>
    </Link>
  )
}

function ProfilePostCard({ post }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className="rounded-full bg-orange-50 px-2.5 py-1 font-semibold text-orange-700">
          {POST_CATEGORY_LABELS[post.category] || 'Bài viết'}
        </span>
        <time dateTime={post.created_at}>{shortDate(post.created_at)}</time>
        {post.is_solved && (
          <span className="font-semibold text-emerald-700">Đã giải quyết</span>
        )}
      </div>

      <Link to={`/forum/${post.id}`} className="mt-3 block rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600">
        <h3 className="text-base font-semibold text-slate-950 transition-colors hover:text-orange-700">
          {post.title}
        </h3>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{post.content}</p>
      </Link>

      <div className="mt-4 flex items-center gap-5 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          <MessageCircle size={15} aria-hidden="true" />
          {post.comments_count || 0} bình luận
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Eye size={15} aria-hidden="true" />
          {post.views_count || 0} lượt xem
        </span>
      </div>
    </article>
  )
}

export default function Profile() {
  const { user, updateUser } = useAuthStore()
  const [activeTab, setActiveTab] = useState('courses')
  const [isEditing, setIsEditing] = useState(false)
  const [showApplication, setShowApplication] = useState(false)
  const [loading, setLoading] = useState(false)
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const [applicationLoading, setApplicationLoading] = useState(false)
  const [teacherApplication, setTeacherApplication] = useState(null)
  const [enrollments, setEnrollments] = useState([])
  const [enrollmentCount, setEnrollmentCount] = useState(0)
  const [enrollmentsLoading, setEnrollmentsLoading] = useState(false)
  const [posts, setPosts] = useState([])
  const [postCount, setPostCount] = useState(0)
  const [postsLoading, setPostsLoading] = useState(false)
  const [dailyActivities, setDailyActivities] = useState([])
  const [activitiesLoading, setActivitiesLoading] = useState(false)
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    phone_number: user?.phone_number || '',
    date_of_birth: user?.date_of_birth || '',
    bio: user?.bio || '',
  })
  const [applicationData, setApplicationData] = useState({
    specialization: '',
    years_of_experience: 0,
    reason: '',
  })

  useEffect(() => {
    setFormData({
      full_name: user?.full_name || '',
      phone_number: user?.phone_number || '',
      date_of_birth: user?.date_of_birth || '',
      bio: user?.bio || '',
    })
  }, [user])

  const loadEnrollments = useCallback(async () => {
    setEnrollmentsLoading(true)
    try {
      const response = await api.get('/courses/enrollments/')
      const data = response.data
      const results = Array.isArray(data) ? data : data.results || []
      setEnrollments(results)
      setEnrollmentCount(Array.isArray(data) ? data.length : data.count ?? results.length)
    } catch {
      toast.error('Không thể tải khóa học đã đăng ký')
    } finally {
      setEnrollmentsLoading(false)
    }
  }, [])

  const loadPosts = useCallback(async () => {
    if (!user?.id) return
    setPostsLoading(true)
    try {
      const response = await forumService.getPosts({
        author: user.id,
        ordering: '-created_at',
      })
      const data = response.data
      const results = Array.isArray(data) ? data : data.results || []
      setPosts(results)
      setPostCount(Array.isArray(data) ? data.length : data.count ?? results.length)
    } catch {
      toast.error('Không thể tải bài viết đã đăng')
    } finally {
      setPostsLoading(false)
    }
  }, [user?.id])

  const loadDailyActivities = useCallback(async () => {
    setActivitiesLoading(true)
    try {
      const data = await authService.getDailyActivity()
      setDailyActivities(data.activities || [])
    } catch {
      toast.error('Không thể tải hoạt động đăng nhập')
    } finally {
      setActivitiesLoading(false)
    }
  }, [])

  useEffect(() => {
    loadEnrollments()
    loadPosts()
    loadDailyActivities()

    const refreshProfileContent = () => {
      loadEnrollments()
      loadPosts()
      loadDailyActivities()
    }
    window.addEventListener('focus', refreshProfileContent)
    return () => {
      window.removeEventListener('focus', refreshProfileContent)
    }
  }, [loadDailyActivities, loadEnrollments, loadPosts])

  useEffect(() => {
    if (user?.role !== 'student') return
    let active = true
    setApplicationLoading(true)
    authService.getTeacherApplication()
      .then((data) => {
        if (!active) return
        setTeacherApplication(data.application)
        if (data.user?.role !== user.role) updateUser(data.user)
      })
      .catch(() => {
        if (active) toast.error('Không thể tải trạng thái hồ sơ giáo viên')
      })
      .finally(() => {
        if (active) setApplicationLoading(false)
      })
    return () => {
      active = false
    }
  }, [updateUser, user?.role])

  const handlePickAvatar = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Ảnh đại diện tối đa 5MB')
      return
    }

    setUploadingAvatar(true)
    try {
      const data = await authService.updateAvatar(file)
      updateUser(data)
      toast.success('Đã cập nhật ảnh đại diện')
    } catch (error) {
      toast.error(error.response?.data?.avatar?.[0] || 'Không thể cập nhật ảnh')
    } finally {
      setUploadingAvatar(false)
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const data = await authService.updateProfile(formData)
      updateUser(data)
      toast.success('Cập nhật hồ sơ thành công')
      setIsEditing(false)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Cập nhật thất bại')
    } finally {
      setLoading(false)
    }
  }

  const handleTeacherApplication = async () => {
    if (!applicationData.specialization.trim()) {
      toast.error('Vui lòng nhập chuyên môn của bạn')
      return
    }
    if (applicationData.reason.trim().length < 20) {
      toast.error('Vui lòng chia sẻ lý do ít nhất 20 ký tự')
      return
    }
    setLoading(true)
    try {
      const data = await authService.submitTeacherApplication(applicationData)
      setTeacherApplication(data.application)
      toast.success(data.message)
      setShowApplication(false)
    } catch (error) {
      toast.error(
        error.response?.data?.error
        || error.response?.data?.reason?.[0]
        || 'Không thể gửi hồ sơ',
      )
    } finally {
      setLoading(false)
    }
  }

  const displayName = user?.full_name || user?.username || 'Người dùng Intaaneto'
  const username = user?.username || user?.email?.split('@')[0] || 'user'

  return (
    <main className="mx-auto max-w-7xl rounded-2xl border border-slate-200 bg-slate-50 px-4 pb-12 pt-6 shadow-sm sm:px-6 lg:rounded-3xl lg:px-8 lg:pt-8">
      <div className="grid gap-10 lg:grid-cols-[420px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <Avatar user={user} uploadingAvatar={uploadingAvatar} onPickAvatar={handlePickAvatar} />

          <div className="mt-5 text-center lg:text-left">
            <h1 className="text-3xl font-bold text-slate-950">{displayName}</h1>
            <p className="mt-1 text-xl text-slate-500">@{username}</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 lg:justify-start">
              <span className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${ROLE_BADGES[user?.role] || 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                {ROLE_LABELS[user?.role] || user?.role}
              </span>
              {user?.is_verified && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
                  <CheckCircle2 size={15} aria-hidden="true" />
                  Đã xác thực
                </span>
              )}
            </div>
          </div>

          <div className="mt-7 space-y-3 text-sm text-slate-700">
            <p className="flex items-center justify-center gap-3 lg:justify-start">
              <Users size={18} className="text-slate-400" aria-hidden="true" />
              <span><strong>0</strong> người theo dõi · <strong>0</strong> đang theo dõi</span>
            </p>
            <p className="flex items-center justify-center gap-3 lg:justify-start">
              <GraduationCap size={18} className="text-slate-400" aria-hidden="true" />
              <span>Tham gia Intaaneto từ {formatJoinDate(user?.created_at)}</span>
            </p>
            <p className="flex items-center justify-center gap-3 lg:justify-start">
              <BookOpen size={18} className="text-slate-400" aria-hidden="true" />
              <span>{enrollmentCount} khóa học đã đăng ký</span>
            </p>
          </div>

          <div className="mt-7 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-950">Thông tin cá nhân</h2>
              <button
                type="button"
                onClick={() => setIsEditing((value) => !value)}
                className="inline-flex items-center gap-2 text-sm font-semibold text-orange-700 hover:text-orange-800"
              >
                <Edit3 size={16} aria-hidden="true" />
                {isEditing ? 'Hủy' : 'Sửa'}
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Họ và tên</span>
                {isEditing ? (
                  <input
                    value={formData.full_name}
                    onChange={(event) => setFormData({ ...formData, full_name: event.target.value })}
                    className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                  />
                ) : (
                  <span className="mt-1 block text-slate-950">{displayName}</span>
                )}
              </label>
              <div className="flex items-center gap-3 text-slate-700">
                <Mail size={17} className="text-slate-400" aria-hidden="true" />
                <span className="truncate">{user?.email || 'Chưa có email'}</span>
              </div>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Số điện thoại</span>
                {isEditing ? (
                  <input
                    value={formData.phone_number}
                    onChange={(event) => setFormData({ ...formData, phone_number: event.target.value })}
                    className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                    placeholder="0912345678"
                  />
                ) : (
                  <span className="mt-1 flex items-center gap-2 text-slate-950">
                    <Phone size={17} className="text-slate-400" aria-hidden="true" />
                    {user?.phone_number || 'Chưa cập nhật'}
                  </span>
                )}
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Ngày sinh</span>
                {isEditing ? (
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(event) => setFormData({ ...formData, date_of_birth: event.target.value })}
                    className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                  />
                ) : (
                  <span className="mt-1 block text-slate-950">{user?.date_of_birth || 'Chưa cập nhật'}</span>
                )}
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Giới thiệu</span>
                {isEditing ? (
                  <textarea
                    value={formData.bio}
                    onChange={(event) => setFormData({ ...formData, bio: event.target.value })}
                    rows={4}
                    className="mt-1 w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                    placeholder="Viết vài dòng về bạn..."
                  />
                ) : (
                  <span className="mt-1 block leading-6 text-slate-700">{user?.bio || 'Chưa có giới thiệu.'}</span>
                )}
              </label>
            </div>

            {isEditing && (
              <Button
                onClick={handleSave}
                disabled={loading}
                className="mt-5 w-full bg-orange-700 text-white hover:bg-orange-800"
              >
                {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
              </Button>
            )}
          </div>
        </aside>

        <section className="min-w-0">
          <ActivityGrid activities={dailyActivities} loading={activitiesLoading} />

          <div className="mt-8">
            <div className="flex gap-8 border-b border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('courses')}
                className={`inline-flex items-center gap-2 border-b-2 px-3 pb-3 text-sm font-semibold ${
                  activeTab === 'courses'
                    ? 'border-orange-600 text-slate-950'
                    : 'border-transparent text-slate-500 hover:text-slate-900'
                }`}
              >
                <BookOpen size={18} aria-hidden="true" />
                Khóa học đã đăng ký ({enrollmentCount})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('posts')}
                className={`inline-flex items-center gap-2 border-b-2 px-3 pb-3 text-sm font-semibold ${
                  activeTab === 'posts'
                    ? 'border-orange-600 text-slate-950'
                    : 'border-transparent text-slate-500 hover:text-slate-900'
                }`}
              >
                <UserRound size={18} aria-hidden="true" />
                Bài viết đã đăng ({postCount})
              </button>
            </div>

            {activeTab === 'courses' && (
              <div className="mt-7">
                {enrollmentsLoading ? (
                  <p className="text-sm text-slate-600" role="status">Đang tải khóa học...</p>
                ) : enrollments.length > 0 ? (
                  <div className="grid gap-6 md:grid-cols-2">
                    {enrollments.map((enrollment) => (
                      <CourseCard key={enrollment.id} enrollment={enrollment} />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
                    <BookOpen className="mx-auto text-slate-400" size={34} aria-hidden="true" />
                    <h3 className="mt-3 font-semibold text-slate-950">Chưa đăng ký khóa học nào</h3>
                    <p className="mt-1 text-sm text-slate-600">Khám phá khóa học để bắt đầu lộ trình học của bạn.</p>
                    <Link
                      to="/courses"
                      className="mt-4 inline-flex h-10 items-center justify-center rounded-md bg-orange-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                    >
                      Xem khóa học
                    </Link>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'posts' && (
              <div className="mt-7">
                {postsLoading ? (
                  <p className="text-sm text-slate-600" role="status">Đang tải bài viết...</p>
                ) : posts.length > 0 ? (
                  <div className="grid gap-4">
                    {posts.map((post) => (
                      <ProfilePostCard key={post.id} post={post} />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
                    <UserRound className="mx-auto text-slate-400" size={34} aria-hidden="true" />
                    <h3 className="mt-3 font-semibold text-slate-950">Chưa có bài viết công khai</h3>
                    <p className="mt-1 text-sm text-slate-600">Đặt câu hỏi hoặc chia sẻ kiến thức với cộng đồng Intaaneto.</p>
                    <Link
                      to="/forum"
                      className="mt-4 inline-flex h-10 items-center justify-center rounded-md bg-orange-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600"
                    >
                      Đến diễn đàn
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>

          {user?.role === 'student' && (
            <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-start gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-orange-50 text-orange-700">
                    <GraduationCap aria-hidden="true" size={22} />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-950">Đăng ký trở thành giảng viên</h2>
                    <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
                      Hồ sơ sẽ được quản trị viên xem xét. Việc gửi hồ sơ không tự động thay đổi quyền tài khoản.
                    </p>
                  </div>
                </div>

                {!applicationLoading && !teacherApplication && (
                  <Button
                    onClick={() => setShowApplication(!showApplication)}
                    className="min-h-11 bg-orange-700 text-white hover:bg-orange-800"
                  >
                    {showApplication ? 'Đóng biểu mẫu' : 'Gửi hồ sơ'}
                  </Button>
                )}
              </div>

              {applicationLoading && (
                <p className="mt-5 text-sm text-slate-600" role="status">Đang tải trạng thái hồ sơ...</p>
              )}

              {teacherApplication?.status === 'pending' && (
                <div className="mt-5 flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
                  <Clock3 aria-hidden="true" className="mt-0.5 shrink-0" size={20} />
                  <div>
                    <p className="font-semibold">Hồ sơ đang chờ admin duyệt</p>
                    <p className="mt-1 text-sm">Bạn vẫn là học viên cho tới khi nhận được quyết định chính thức.</p>
                  </div>
                </div>
              )}

              {teacherApplication?.status === 'rejected' && (
                <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-red-900">
                  <div className="flex gap-3">
                    <XCircle aria-hidden="true" className="mt-0.5 shrink-0" size={20} />
                    <div>
                      <p className="font-semibold">Hồ sơ chưa được chấp thuận</p>
                      <p className="mt-1 text-sm">{teacherApplication.review_note || 'Vui lòng bổ sung thông tin và thử lại.'}</p>
                    </div>
                  </div>
                  <Button
                    onClick={() => setShowApplication(!showApplication)}
                    className="mt-4 min-h-11 bg-orange-700 text-white hover:bg-orange-800"
                  >
                    {showApplication ? 'Đóng biểu mẫu' : 'Gửi hồ sơ mới'}
                  </Button>
                </div>
              )}

              {showApplication && teacherApplication?.status !== 'pending' && (
                <div className="mt-6 border-t border-slate-200 pt-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="block">
                      <span className="text-sm font-medium text-slate-800">Chuyên môn *</span>
                      <input
                        value={applicationData.specialization}
                        onChange={(event) => setApplicationData({ ...applicationData, specialization: event.target.value })}
                        placeholder="VD: Python, Web Development..."
                        className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-slate-800">Số năm kinh nghiệm</span>
                      <input
                        type="number"
                        min="0"
                        max="80"
                        value={applicationData.years_of_experience}
                        onChange={(event) => setApplicationData({ ...applicationData, years_of_experience: parseInt(event.target.value, 10) || 0 })}
                        className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                      />
                    </label>
                  </div>
                  <label className="mt-4 block">
                    <span className="text-sm font-medium text-slate-800">Lý do muốn trở thành giảng viên *</span>
                    <textarea
                      value={applicationData.reason}
                      onChange={(event) => setApplicationData({ ...applicationData, reason: event.target.value })}
                      rows={4}
                      placeholder="Chia sẻ lý do bạn muốn giảng dạy trên nền tảng..."
                      className="mt-2 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-950 focus:outline-none focus:ring-2 focus:ring-orange-600"
                    />
                    <span className="mt-1 block text-xs text-slate-500">Ít nhất 20 ký tự.</span>
                  </label>
                  <Button
                    onClick={handleTeacherApplication}
                    disabled={loading}
                    className="mt-5 min-h-11 bg-orange-700 px-6 text-white hover:bg-orange-800"
                  >
                    {loading ? 'Đang gửi...' : 'Gửi hồ sơ cho admin'}
                  </Button>
                </div>
              )}
            </section>
          )}

          {user?.role === 'teacher' && (
            <section className="mt-8 rounded-2xl border border-orange-100 bg-orange-50 p-6">
              <div className="flex items-start gap-4">
                <ShieldCheck className="mt-0.5 text-orange-700" size={24} aria-hidden="true" />
                <div>
                  <h2 className="font-semibold text-slate-950">Bạn là giảng viên</h2>
                  <p className="mt-1 text-sm text-slate-600">Bạn có thể tạo, quản lý khóa học và theo dõi tiến độ học viên.</p>
                </div>
              </div>
            </section>
          )}
        </section>
      </div>
    </main>
  )
}
