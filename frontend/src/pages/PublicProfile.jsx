import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  BookOpen,
  CalendarDays,
  Eye,
  FileText,
  MessageCircle,
  X,
  UserCheck,
  UserPlus,
  Users,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { forumService } from '../services/forumService'
import { useAuthStore } from '../store/authStore'
import { getUserAvatar } from '../utils/avatar'

const ROLE_LABELS = {
  student: 'Học viên',
  teacher: 'Giảng viên',
  admin: 'Quản trị viên',
}

const ACTIVITY_LEVELS = [
  'bg-white/10',
  'bg-emerald-200',
  'bg-emerald-300',
  'bg-emerald-500',
  'bg-emerald-700',
]

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function PublicActivityGrid({ activity = [] }) {
  const cells = useMemo(() => {
    const today = new Date()
    today.setHours(12, 0, 0, 0)
    const endOfWeek = new Date(today)
    endOfWeek.setDate(today.getDate() + (6 - today.getDay()))
    const start = new Date(endOfWeek)
    start.setDate(endOfWeek.getDate() - (53 * 7 - 1))
    const counts = new Map(activity.map((item) => [item.date, Number(item.count || 0)]))
    return Array.from({ length: 53 * 7 }, (_, index) => {
      const date = new Date(start)
      date.setDate(start.getDate() + index)
      const key = localDateKey(date)
      const isFuture = date > today
      const count = isFuture ? 0 : counts.get(key) || 0
      return { key, date, count, isFuture, level: count === 0 ? 0 : Math.min(4, count) }
    })
  }, [activity])
  const activeDays = cells.filter((cell) => cell.count > 0).length
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
    <section className="border-b border-white/25 pb-8" aria-labelledby="public-activity-title">
      <h2 id="public-activity-title" className="font-semibold">{activeDays} ngày hoạt động công khai trong 12 tháng qua</h2>
      <p className="mt-1 text-xs text-white/55">Chỉ tính những ngày người dùng đăng bài trên diễn đàn.</p>
      <div className="mt-6 overflow-x-auto pb-2">
        <div className="min-w-[884px]">
          <div className="ml-10 grid text-xs font-medium text-white/75" style={{ gridTemplateColumns: 'repeat(53, 0.75rem)', columnGap: '0.25rem' }}>
            {monthLabels.map((month) => <span key={month.key} className="whitespace-nowrap" style={{ gridColumnStart: month.column }}>{month.label}</span>)}
          </div>
          <div className="mt-2 flex gap-2">
            <div className="grid h-[104px] grid-rows-7 gap-1 text-xs font-medium text-white/70"><span /><span>Mon</span><span /><span>Wed</span><span /><span>Fri</span><span /></div>
            <div className="grid grid-flow-col grid-rows-7 gap-1">
              {cells.map((cell) => (
                <span key={cell.key} title={cell.isFuture ? undefined : `${cell.count} bài viết · ${cell.date.toLocaleDateString('vi-VN')}`} className={`h-3 w-3 rounded-[3px] ${ACTIVITY_LEVELS[cell.level]}`} />
              ))}
            </div>
          </div>
          <div className="mt-3 flex items-center justify-end gap-2 text-xs font-medium text-white/65">
            <span>Ít hơn</span>
            {ACTIVITY_LEVELS.map((level) => <span key={level} className={`h-3 w-3 rounded-[3px] ${level}`} />)}
            <span>Nhiều hơn</span>
          </div>
        </div>
      </div>
    </section>
  )
}

function joinDate(value) {
  if (!value) return 'Chưa cập nhật'
  return new Intl.DateTimeFormat('vi-VN', { month: 'long', year: 'numeric' }).format(new Date(value))
}

export default function PublicProfile() {
  const { userId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const currentUser = useAuthStore((state) => state.user)
  const [profile, setProfile] = useState(null)
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [followLoading, setFollowLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('courses')
  const [people, setPeople] = useState([])
  const [peopleLoading, setPeopleLoading] = useState(false)
  const peopleType = searchParams.get('list')

  const loadProfile = useCallback(async () => {
    setLoading(true)
    try {
      const [profileResponse, postsResponse] = await Promise.all([
        forumService.getPublicProfile(userId),
        forumService.getPosts({ author: userId, ordering: '-created_at' }),
      ])
      setProfile(profileResponse.data)
      const data = postsResponse.data
      setPosts(Array.isArray(data) ? data : data.results || [])
    } catch {
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    if (!['followers', 'following'].includes(peopleType)) {
      setPeople([])
      return
    }
    setPeopleLoading(true)
    forumService.getProfilePeople(userId, peopleType)
      .then((response) => setPeople(response.data.results || []))
      .catch(() => {
        setPeople([])
        toast.error('Không thể tải danh sách theo dõi')
      })
      .finally(() => setPeopleLoading(false))
  }, [peopleType, userId])

  const toggleFollow = async () => {
    if (!currentUser || !profile || currentUser.id === profile.id) return
    setFollowLoading(true)
    try {
      const response = await forumService.toggleFollow(profile.id)
      const following = Boolean(response.data.following)
      setProfile((current) => ({
        ...current,
        is_following: following,
        followers_count: Math.max(0, current.followers_count + (following ? 1 : -1)),
      }))
    } catch {
      toast.error('Không thể cập nhật theo dõi')
    } finally {
      setFollowLoading(false)
    }
  }

  if (loading) {
    return <main className="flex min-h-[60vh] items-center justify-center text-white/70" role="status">Đang tải hồ sơ...</main>
  }

  if (!profile) {
    return (
      <main className="mx-auto min-h-[60vh] max-w-3xl px-4 py-16 text-center text-white">
        <h1 className="text-2xl font-bold">Không tìm thấy người dùng</h1>
        <Link to="/forum" className="mt-4 inline-block font-semibold text-orange-300 hover:text-orange-200">Quay lại diễn đàn</Link>
      </main>
    )
  }

  const avatar = getUserAvatar(profile)
  const isOwnProfile = currentUser?.id === profile.id

  return (
    <main className="mx-auto grid min-h-[calc(100vh-7rem)] max-w-7xl gap-10 px-4 py-8 text-white sm:px-6 lg:grid-cols-[380px_minmax(0,1fr)] lg:px-8">
      <aside className="lg:sticky lg:top-24 lg:self-start">
        <div className="mx-auto h-56 w-56 rounded-full border-4 border-white/80 p-1 shadow-lg lg:mx-0">
          {avatar ? (
            <img src={avatar} alt={`Ảnh đại diện của ${profile.full_name}`} className="h-full w-full rounded-full object-cover" referrerPolicy="no-referrer" />
          ) : (
            <div className="flex h-full w-full items-center justify-center rounded-full bg-orange-500/20 text-6xl font-bold text-orange-200">{profile.full_name?.charAt(0) || 'U'}</div>
          )}
        </div>

        <div className="mt-6 text-center lg:text-left">
          <h1 className="text-3xl font-bold">{profile.full_name || profile.username}</h1>
          <p className="mt-1 text-xl text-white/70">@{profile.username}</p>
          <span className="mt-4 inline-flex rounded-full border border-orange-300/30 bg-orange-500/10 px-3 py-1 text-sm font-semibold text-orange-200">{ROLE_LABELS[profile.role] || profile.role}</span>
          {profile.bio && <p className="mt-5 whitespace-pre-wrap leading-7 text-white/85">{profile.bio}</p>}
        </div>

        {!isOwnProfile && (
          currentUser ? (
            <button type="button" onClick={toggleFollow} disabled={followLoading} className={`mt-6 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border px-5 font-semibold transition-colors disabled:opacity-60 ${profile.is_following ? 'border-white/20 bg-white/10 text-white hover:bg-white/15' : 'border-orange-500 bg-orange-600 text-white hover:bg-orange-700'}`}>
              {profile.is_following ? <UserCheck className="h-5 w-5" aria-hidden="true" /> : <UserPlus className="h-5 w-5" aria-hidden="true" />}
              {followLoading ? 'Đang cập nhật...' : profile.is_following ? 'Đang theo dõi' : 'Theo dõi'}
            </button>
          ) : (
            <Link to="/login" className="mt-6 inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-orange-600 px-5 font-semibold hover:bg-orange-700">Đăng nhập để theo dõi</Link>
          )
        )}

        <div className="mt-6 space-y-4 border-t border-white/20 pt-5 text-sm text-white/80">
          <div className="flex flex-wrap items-center justify-center gap-2 lg:justify-start">
            <Users className="h-5 w-5 text-white/60" aria-hidden="true" />
            <button type="button" onClick={() => setSearchParams({ list: 'followers' })} className="rounded font-semibold hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"><strong>{profile.followers_count}</strong> người theo dõi</button>
            <span aria-hidden="true">·</span>
            <button type="button" onClick={() => setSearchParams({ list: 'following' })} className="rounded font-semibold hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"><strong>{profile.following_count}</strong> đang theo dõi</button>
          </div>
          <p className="flex items-center justify-center gap-3 lg:justify-start"><CalendarDays className="h-5 w-5 text-white/60" aria-hidden="true" />Tham gia Intaaneto từ {joinDate(profile.created_at)}</p>
        </div>
      </aside>

      <section className="min-w-0">
        <PublicActivityGrid activity={profile.forum_activity} />

        <div className="mt-8 flex items-center gap-6 border-b border-white/25">
          <button type="button" onClick={() => setActiveTab('courses')} className={`inline-flex min-h-12 items-center gap-2 border-b-2 px-3 text-sm font-semibold ${activeTab === 'courses' ? 'border-orange-300 text-white' : 'border-transparent text-white/60 hover:text-white'}`}>
            <BookOpen className="h-4 w-4" aria-hidden="true" /> Khóa học đã đăng ký ({profile.enrolled_courses?.length || 0})
          </button>
          <button type="button" onClick={() => setActiveTab('posts')} className={`inline-flex min-h-12 items-center gap-2 border-b-2 px-3 text-sm font-semibold ${activeTab === 'posts' ? 'border-orange-300 text-white' : 'border-transparent text-white/60 hover:text-white'}`}>
            <FileText className="h-4 w-4" aria-hidden="true" /> Bài viết đã đăng ({profile.posts_count})
          </button>
        </div>
        <div className="mt-5 space-y-4">
          {activeTab === 'courses' && (
            profile.enrolled_courses?.length ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {profile.enrolled_courses.map((course) => (
                  <Link key={course.id} to={`/courses/${course.id}`} className="group overflow-hidden rounded-2xl border border-slate-200 bg-white text-slate-950 transition hover:-translate-y-0.5 hover:border-orange-300 hover:shadow-md">
                    {course.thumbnail ? <img src={course.thumbnail} alt="" className="aspect-[16/8] w-full object-cover" /> : <div className="flex aspect-[16/8] items-center justify-center bg-gradient-to-br from-cyan-500 to-blue-600 text-2xl font-bold text-white">INTAANETO</div>}
                    <div className="p-5">
                      <h3 className="font-semibold group-hover:text-orange-700">{course.title}</h3>
                      <p className="mt-2 text-sm text-slate-500">Giảng viên: {course.teacher_name}</p>
                      <p className="mt-3 text-sm font-semibold text-orange-700">Đã đăng ký</p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : <div className="rounded-2xl border border-white/15 bg-slate-950/45 px-6 py-12 text-center text-white/65">Người dùng này chưa đăng ký khóa học công khai nào.</div>
          )}
          {activeTab === 'posts' && (posts.length === 0 ? (
            <div className="rounded-2xl border border-white/15 bg-slate-950/45 px-6 py-12 text-center text-white/65">Người dùng này chưa đăng bài viết nào.</div>
          ) : posts.map((post) => (
            <Link key={post.id} to={`/forum/${post.id}`} className="block rounded-2xl border border-white/15 bg-slate-950/45 p-5 transition-colors hover:border-orange-400/40 hover:bg-slate-950/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-lg font-bold hover:text-orange-300">{post.title}</h3>
                {post.course && <span className="rounded-full border border-orange-400/30 bg-orange-500/10 px-2.5 py-1 text-xs font-semibold text-orange-300">#{post.course.slug}</span>}
              </div>
              <p className="mt-2 line-clamp-3 text-sm leading-6 text-white/65">{post.content}</p>
              <div className="mt-4 flex gap-5 border-t border-white/10 pt-3 text-xs text-white/50">
                <span className="inline-flex items-center gap-1.5"><MessageCircle className="h-4 w-4" aria-hidden="true" />{post.comments_count || 0} bình luận</span>
                <span className="inline-flex items-center gap-1.5"><Eye className="h-4 w-4" aria-hidden="true" />{post.views_count || 0} lượt xem</span>
              </div>
            </Link>
          )))}
        </div>
      </section>

      {['followers', 'following'].includes(peopleType) && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="people-title">
          <button type="button" className="absolute inset-0 bg-black/70" onClick={() => setSearchParams({})} aria-label="Đóng danh sách" />
          <div className="relative max-h-[80vh] w-full max-w-md overflow-y-auto rounded-2xl border border-white/15 bg-slate-950 p-5 shadow-2xl">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-4">
              <h2 id="people-title" className="text-lg font-bold">{peopleType === 'followers' ? 'Người theo dõi' : 'Đang theo dõi'}</h2>
              <button type="button" onClick={() => setSearchParams({})} className="flex h-11 w-11 items-center justify-center rounded-lg text-white/65 hover:bg-white/10 hover:text-white" aria-label="Đóng"><X className="h-5 w-5" /></button>
            </div>
            <div className="mt-3 space-y-1">
              {peopleLoading ? <p className="py-8 text-center text-white/60">Đang tải...</p> : people.length === 0 ? <p className="py-8 text-center text-white/60">Chưa có người dùng nào.</p> : people.map((person) => {
                const personAvatar = getUserAvatar(person)
                return (
                  <Link key={person.id} to={`/users/${person.id}`} onClick={() => setSearchParams({})} className="flex min-h-14 items-center gap-3 rounded-xl px-3 py-2 hover:bg-white/10">
                    {personAvatar ? <img src={personAvatar} alt="" className="h-10 w-10 rounded-full object-cover" referrerPolicy="no-referrer" /> : <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20 font-bold text-orange-200">{person.full_name?.charAt(0) || 'U'}</div>}
                    <div className="min-w-0"><p className="truncate font-semibold">{person.full_name || person.username}</p><p className="truncate text-sm text-white/50">@{person.username}</p></div>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
