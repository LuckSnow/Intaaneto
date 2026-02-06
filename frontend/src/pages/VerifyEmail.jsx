import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function VerifyEmail() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('verifying') // verifying, success, error

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        await api.post('/auth/verify_email/', { token })
        setStatus('success')
        toast.success('Email đã được xác thực thành công!')
        setTimeout(() => navigate('/login'), 3000)
      } catch (error) {
        setStatus('error')
        toast.error(error.response?.data?.error || 'Xác thực thất bại')
      }
    }

    if (token) {
      verifyEmail()
    }
  }, [token, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8 text-center">
          {status === 'verifying' && (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold text-white mb-2">Đang xác thực...</h2>
              <p className="text-white/80">Vui lòng đợi trong giây lát</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Xác thực thành công!</h2>
              <p className="text-white/80 mb-4">Email của bạn đã được xác thực. Đang chuyển đến trang đăng nhập...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Xác thực thất bại</h2>
              <p className="text-white/80 mb-6">Link xác thực không hợp lệ hoặc đã hết hạn</p>
              <Button
                onClick={() => navigate('/login')}
                className="w-full py-3 rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold shadow-lg border-0 transition-all duration-300"
              >
                Về trang đăng nhập
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
