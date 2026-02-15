import { useState, useRef } from 'react'
import { Send, Image, X, Reply } from 'lucide-react'

export default function CommentInput({ onSubmit, replyTo = null, onCancelReply, placeholder = 'Viết bình luận...' }) {
  const [content, setContent] = useState('')
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileRef = useRef(null)

  const handleImage = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImage(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const removeImage = () => {
    setImage(null)
    setImagePreview(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleSubmit = async () => {
    if (!content.trim() && !image) return
    setIsSubmitting(true)
    try {
      await onSubmit({ content: content.trim(), image, parent_id: replyTo?.id })
      setContent('')
      removeImage()
      onCancelReply?.()
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="space-y-2">
      {/* Reply indicator */}
      {replyTo && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-lg text-xs text-orange-400">
          <Reply className="w-3 h-3" />
          <span>Trả lời <strong>{replyTo.author?.full_name}</strong></span>
          <button onClick={onCancelReply} className="ml-auto hover:text-white transition-colors">
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Image preview */}
      {imagePreview && (
        <div className="relative inline-block">
          <img src={imagePreview} alt="" className="h-20 rounded-lg border border-white/10" />
          <button
            onClick={removeImage}
            className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2">
        <div className="flex-1 bg-white/5 border border-white/10 rounded-xl focus-within:border-orange-500/30 transition-colors">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className="w-full bg-transparent text-white text-sm px-4 py-2.5 resize-none focus:outline-none placeholder:text-white/30 max-h-32"
            style={{ minHeight: '40px' }}
          />
        </div>

        <input ref={fileRef} type="file" accept="image/*" onChange={handleImage} className="hidden" />

        <button
          onClick={() => fileRef.current?.click()}
          className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-white/40 hover:text-white/70 hover:bg-white/10 transition-all"
        >
          <Image className="w-4 h-4" />
        </button>

        <button
          onClick={handleSubmit}
          disabled={isSubmitting || (!content.trim() && !image)}
          className="p-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 text-white hover:shadow-[0_0_15px_rgba(249,115,22,0.4)] disabled:opacity-40 disabled:hover:shadow-none transition-all"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
