import { useState, useRef } from 'react'
import { X, ImagePlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { forumService } from '../../services/forumService'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const CATEGORIES = [
  { value: 'question', label: 'Câu hỏi', icon: '❓' },
  { value: 'discussion', label: 'Thảo luận', icon: '💬' },
  { value: 'showcase', label: 'Chia sẻ dự án', icon: '🚀' },
  { value: 'announcement', label: 'Thông báo', icon: '📢' },
]

export default function CreatePostModal({ isOpen, onClose, onCreated, tags = [] }) {
  const { user } = useAuthStore()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('question')
  const [selectedTags, setSelectedTags] = useState([])
  const [images, setImages] = useState([null, null, null, null])
  const [previews, setPreviews] = useState([null, null, null, null])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef(null)

  if (!isOpen) return null

  const handleImageAdd = (e) => {
    const files = Array.from(e.target.files)
    const newImages = [...images]
    const newPreviews = [...previews]
    let slotIdx = newImages.findIndex(img => img === null)

    files.forEach(file => {
      if (slotIdx > 3) return
      newImages[slotIdx] = file
      newPreviews[slotIdx] = URL.createObjectURL(file)
      slotIdx = newImages.findIndex((img, i) => i > slotIdx && img === null)
      if (slotIdx === -1) slotIdx = 4
    })

    setImages(newImages)
    setPreviews(newPreviews)
    e.target.value = ''
  }

  const removeImage = (idx) => {
    const newImages = [...images]
    const newPreviews = [...previews]
    if (newPreviews[idx]) URL.revokeObjectURL(newPreviews[idx])
    newImages[idx] = null
    newPreviews[idx] = null
    setImages(newImages)
    setPreviews(newPreviews)
  }

  const toggleTag = (tagId) => {
    setSelectedTags(prev =>
      prev.includes(tagId) ? prev.filter(id => id !== tagId) : [...prev, tagId]
    )
  }

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) {
      toast.error('Vui lòng nhập tiêu đề và nội dung')
      return
    }
    setIsSubmitting(true)
    try {
      await forumService.createPost({
        title, content, category,
        tag_ids: selectedTags,
        image_1: images[0],
        image_2: images[1],
        image_3: images[2],
        image_4: images[3],
      })
      toast.success('Đăng bài thành công!')
      onCreated?.()
      onClose()
      // Reset
      setTitle(''); setContent(''); setCategory('question')
      setSelectedTags([]); setImages([null,null,null,null]); setPreviews([null,null,null,null])
    } catch (err) {
      toast.error('Đăng bài thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-bold text-white">Tạo bài viết mới</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/10 transition-colors">
            <X className="w-5 h-5 text-white/70" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Author info */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="text-white font-medium">{user?.full_name}</p>
              <p className="text-white/50 text-xs">@{user?.username}</p>
            </div>
          </div>

          {/* Category */}
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map(cat => (
              <button
                key={cat.value}
                onClick={() => setCategory(cat.value)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  category === cat.value
                    ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/25'
                    : 'bg-white/10 text-white/70 hover:bg-white/20'
                }`}
              >
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>

          {/* Title */}
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Tiêu đề bài viết..."
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-transparent transition-all"
          />

          {/* Content */}
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="Viết nội dung bài viết... (Hỗ trợ Markdown)"
            rows={6}
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-transparent resize-none transition-all"
          />

          {/* Tags */}
          {tags.length > 0 && (
            <div>
              <p className="text-white/60 text-sm mb-2">Tags</p>
              <div className="flex flex-wrap gap-2">
                {tags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => toggleTag(tag.id)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      selectedTags.includes(tag.id)
                        ? 'text-white shadow-md'
                        : 'bg-white/10 text-white/60 hover:bg-white/20'
                    }`}
                    style={selectedTags.includes(tag.id) ? { backgroundColor: tag.color } : {}}
                  >
                    #{tag.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Image previews */}
          <div className="flex flex-wrap gap-3">
            {previews.map((preview, idx) => preview && (
              <div key={idx} className="relative w-24 h-24 rounded-xl overflow-hidden border border-white/10">
                <img src={preview} alt="" className="w-full h-full object-cover" />
                <button
                  onClick={() => removeImage(idx)}
                  className="absolute top-1 right-1 w-5 h-5 bg-black/60 rounded-full flex items-center justify-center"
                >
                  <X className="w-3 h-3 text-white" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-white/10">
          <div className="flex gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageAdd}
              accept="image/*"
              multiple
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={images.filter(Boolean).length >= 4}
              className="p-2 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors disabled:opacity-30"
            >
              <ImagePlus className="w-5 h-5" />
            </button>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !content.trim()}
            className="px-6 py-2 rounded-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold border-0 shadow-lg disabled:opacity-50 transition-all"
          >
            {isSubmitting ? 'Đang đăng...' : 'Đăng bài'}
          </Button>
        </div>
      </div>
    </div>
  )
}
