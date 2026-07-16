import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { getDefaultAuthenticatedPath } from './utils/authNavigation'

// Layouts
import MainLayout from './components/layouts/MainLayout'
import DashboardLayout from './components/layouts/DashboardLayout'

// Pages
import Landing from './pages/Landing'
import Login from './pages/Login'
import TeacherLogin from './pages/TeacherLogin'
import Register from './pages/Register'
import VerifyEmail from './pages/VerifyEmail'
import Dashboard from './pages/Dashboard'
import Courses from './pages/Courses'
import CourseDetail from './pages/CourseDetail'
import LessonPage from './pages/LessonPage'
import TeacherUpload from './pages/TeacherUpload'
import TeacherAssessments from './pages/TeacherAssessments'
import TeacherCourses from './pages/TeacherCourses'
import ExercisePage from './pages/ExercisePage'
import Forum from './pages/Forum'
import ForumPost from './pages/ForumPost'
import Profile from './pages/Profile'

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const location = useLocation()
  return isAuthenticated
    ? children
    : <Navigate to="/login" replace state={{ from: location.pathname }} />
}

const GuestRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore()
  return isAuthenticated
    ? <Navigate to={getDefaultAuthenticatedPath(user)} replace />
    : children
}

const RoleRoute = ({ roles, children }) => {
  const user = useAuthStore((state) => state.user)
  return roles.includes(user?.role)
    ? children
    : <Navigate to="/dashboard" replace />
}

function App() {
  const { initializeAuth, isInitializing } = useAuthStore()

  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-600" role="status">Đang kiểm tra phiên đăng nhập...</p>
      </div>
    )
  }

  return (
    <Routes>
      <Route
        path="/teacher/login"
        element={<GuestRoute><TeacherLogin /></GuestRoute>}
      />
      {/* Public Routes */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
        <Route path="/verify-email/:token" element={<VerifyEmail />} />
        <Route path="/courses" element={<Courses />} />
        <Route path="/courses/:id" element={<CourseDetail />} />
        <Route path="/lessons/:id" element={<LessonPage />} />
        <Route path="/forum" element={<Forum />} />
        <Route path="/forum/:id" element={<ForumPost />} />
      </Route>

      {/* Protected Routes */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/teacher/upload"
          element={<RoleRoute roles={['teacher', 'admin']}><TeacherUpload /></RoleRoute>}
        />
        <Route
          path="/teacher/courses"
          element={<RoleRoute roles={['teacher']}><TeacherCourses /></RoleRoute>}
        />
        <Route
          path="/teacher/assessments"
          element={<RoleRoute roles={['teacher', 'admin']}><TeacherAssessments /></RoleRoute>}
        />
        <Route path="/exercises/:id" element={<ExercisePage />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<div>404 - Page Not Found</div>} />
    </Routes>
  )
}

export default App
