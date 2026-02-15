import { useState } from 'react'
import { X, Flag, AlertTriangle } from 'lucide-react'

const REASONS = [
  { value: 'spam', label: 'Spam / Quảng cáo', icon: '🚫' },
  { value: 'inappropriate', label: 'Nội dung không phù hợp', icon: '⚠️' },
  { value: 'harassment', label: 'Quấy rối / Bắt nạt', icon: '😤' },
  { value: 'misinformation', label: 'Thông tin sai lệch', icon: '❌' },
  { value: 'other', label: 'Lý do khác', icon: '📝' },
]

export default function ReportModal({ isOpen, onClose, onSubmit, targetType = 'post' }) {
  const [reason, setReason] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (!reason) return
    setIsSubmitting(true)
    try {
      await onSubmit({ reason, description: description.trim() })
      setReason('')
      setDescription('')
      onClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-md bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
              <Flag className="w-4 h-4 text-red-400" />
            </div>
            <h2 className="text-white font-bold">
              Báo cáo {targetType === 'post' ? 'bài viết' : 'bình luận'}
            </h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <p className="text-white/50 text-sm">Chọn lý do báo cáo:</p>

          <div className="space-y-2">
            {REASONS.map(r => (
              <button
                key={r.value}
                onClick={() => setReason(r.value)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border transition-all text-left ${
                  reason === r.value
                    ? 'bg-orange-500/10 border-orange-500/30 text-orange-400'
                    : 'bg-white/5 border-white/5 text-white/70 hover:bg-white/10 hover:border-white/10'
                }`}
              >
                <span className="text-lg">{r.icon}</span>
                <span className="text-sm font-medium">{r.label}</span>
              </button>
            ))}
          </div>

          {reason && (
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả thêm (không bắt buộc)..."
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-orange-500/30 placeholder:text-white/20 resize-none"
            />
          )}

          <div className="flex items-start gap-2 p-3 bg-yellow-500/5 border border-yellow-500/10 rounded-xl">
            <AlertTriangle className="w-4 h-4 text-yellow-500/60 mt-0.5 flex-shrink-0" />
            <p className="text-yellow-500/60 text-xs">
              Báo cáo sai có thể dẫn đến hạn chế tài khoản. Chỉ báo cáo khi thực sự vi phạm.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-5 border-t border-white/5">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white/60 hover:bg-white/10 text-sm font-medium transition-all"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={!reason || isSubmitting}
            className="flex-1 px-4 py-2.5 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white text-sm font-medium hover:shadow-[0_0_15px_rgba(239,68,68,0.4)] disabled:opacity-40 transition-all"
          >
            {isSubmitting ? 'Đang gửi...' : 'Gửi báo cáo'}
          </button>
        </div>
      </div>
    </div>
  )
}
