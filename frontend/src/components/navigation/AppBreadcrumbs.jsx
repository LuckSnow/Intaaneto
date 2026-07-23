import { ChevronRight, Home } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

const staticRoutes = {
  '/courses': [{ label: 'Khóa học' }],
  '/forum': [{ label: 'Diễn đàn' }],
  '/dashboard': [{ label: 'Dashboard' }],
  '/profile': [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Hồ sơ' },
  ],
  '/teacher/upload': [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Biên soạn học liệu' },
  ],
  '/teacher/courses': [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Quản lý khóa học' },
  ],
  '/teacher/assessments': [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Bài đánh giá' },
  ],
}

function resolveItems(pathname) {
  if (staticRoutes[pathname]) return staticRoutes[pathname]
  if (/^\/courses\/[^/]+$/.test(pathname)) {
    return [
      { label: 'Khóa học', to: '/courses' },
      { label: 'Chi tiết khóa học' },
    ]
  }
  if (/^\/lessons\/[^/]+$/.test(pathname)) {
    return [
      { label: 'Khóa học', to: '/courses' },
      { label: 'Bài học' },
    ]
  }
  if (/^\/forum\/[^/]+$/.test(pathname)) {
    return [
      { label: 'Diễn đàn', to: '/forum' },
      { label: 'Bài viết' },
    ]
  }
  if (/^\/users\/[^/]+$/.test(pathname)) {
    return [
      { label: 'Diễn đàn', to: '/forum' },
      { label: 'Hồ sơ thành viên' },
    ]
  }
  if (/^\/exercises\/[^/]+$/.test(pathname)) {
    return [
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Bài tập' },
    ]
  }
  return []
}

export default function AppBreadcrumbs({ className = '' }) {
  const { pathname } = useLocation()
  const items = resolveItems(pathname)

  if (pathname === '/' || items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className={`text-sm ${className}`}>
      <ol className="flex min-h-11 min-w-0 items-center gap-1.5 overflow-x-auto whitespace-nowrap text-slate-300">
        <li>
          <Link
            to="/"
            className="inline-flex min-h-11 items-center gap-1.5 rounded px-1 font-medium hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            Trang chủ
          </Link>
        </li>
        {items.map((item, index) => {
          const current = index === items.length - 1
          return (
            <li key={`${item.label}-${index}`} className="flex min-w-0 items-center gap-1.5">
              <ChevronRight className="h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
              {item.to && !current ? (
                <Link
                  to={item.to}
                  className="inline-flex min-h-11 items-center rounded px-1 font-medium hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
                >
                  {item.label}
                </Link>
              ) : (
                <span className="max-w-[15rem] truncate px-1 font-semibold text-white" aria-current="page">
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
