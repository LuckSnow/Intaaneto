import { useState } from 'react'
import { ChevronDown, CheckCircle, MoreHorizontal, Trash2, Flag, Reply as ReplyIcon } from 'lucide-react'
import CommentInput from './CommentInput'
import ReactionButton from './ReactionButton'
import { forumService } from '../../services/forumService'

function timeAgo(dateStr) {
  const now = new Date()
  const date = new Date(dateStr)
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return 'vừa xong'
  if (diff < 3600) return `${Math.floor(diff / 60)}p trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h trước`
  return date.toLocaleDateString('vi-VN')
}

function countCommentTree(items = []) {
  return items.reduce((total, item) => total + 1 + countCommentTree(item.replies || []), 0)
}

function CommentItem({ comment, postId, currentUser, isPostAuthor, onReply, onDelete, onReact, onMarkSolution, onReport, onOpenImage, depth = 0 }) {
  const [showReplies, setShowReplies] = useState(depth === 0)
  const [showMenu, setShowMenu] = useState(false)
  const isAuthor = currentUser?.id === comment.author?.id

  const handleReplyClick = (event) => {
    if (event.target.closest('button, a, input, textarea, select, option')) {
      return
    }
    onReply?.(comment)
  }

  return (
    <div className={`${depth > 0 ? 'ml-8 pl-4 border-l border-white/5' : ''}`}>
      <div className="group py-3">
        <div className="flex gap-3">
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {comment.author?.full_name?.charAt(0) || 'U'}
          </div>

          <div
            className="flex-1 min-w-0 cursor-pointer rounded-xl transition-colors hover:bg-white/[0.03]"
            onClick={handleReplyClick}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                onReply?.(comment)
              }
            }}
          >
            {/* Header */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-white text-sm font-medium">{comment.author?.full_name}</span>
              {comment.is_solution && (
                <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-green-500/20 text-green-400 text-[10px]">
                  <CheckCircle className="w-2.5 h-2.5" /> Giải pháp
                </span>
              )}
              <span className="text-white/30 text-xs">{timeAgo(comment.created_at)}</span>

              {/* Menu */}
              <div className="relative ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    setShowMenu(!showMenu)
                  }}
                  className="p-1 rounded hover:bg-white/10 text-white/30 hover:text-white/60"
                >
                  <MoreHorizontal className="w-3.5 h-3.5" />
                </button>
                {showMenu && (
                  <div className="absolute right-0 top-full mt-1 bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-lg py-1 z-20 min-w-[140px] shadow-xl">
                    {!comment.is_solution && isPostAuthor && (
                      <button
                        onClick={() => { onMarkSolution?.(comment.id); setShowMenu(false) }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-green-400 hover:bg-white/5"
                      >
                        <CheckCircle className="w-3 h-3" /> Đánh dấu giải pháp
                      </button>
                    )}
                    <button
                      onClick={() => { onReport?.('comment', comment.id); setShowMenu(false) }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-yellow-400 hover:bg-white/5"
                    >
                      <Flag className="w-3 h-3" /> Báo cáo
                    </button>
                    {isAuthor && (
                      <button
                        onClick={() => { onDelete?.(comment.id); setShowMenu(false) }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-white/5"
                      >
                        <Trash2 className="w-3 h-3" /> Xóa
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Content */}
            <p className="text-white/70 text-sm whitespace-pre-wrap break-words">{comment.content}</p>

            {/* Image */}
            {comment.image && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation()
                  onOpenImage?.(comment.image)
                }}
                className="mt-2 block text-left"
              >
                <img
                  src={comment.image}
                  alt=""
                  className="max-h-48 rounded-lg border border-white/10 cursor-zoom-in"
                />
              </button>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 mt-2">
              <ReactionButton
                reactions={comment.reactions_summary}
                onReact={(type) => onReact?.(comment.id, type)}
              />
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation()
                  onReply?.(comment)
                }}
                className="flex items-center gap-1 text-white/30 hover:text-white/60 text-xs transition-colors"
              >
                <ReplyIcon className="w-3 h-3" /> Trả lời
              </button>
            </div>

            {/* Replies toggle */}
            {comment.replies?.length > 0 && (
              <button
                onClick={() => setShowReplies(!showReplies)}
                className="flex items-center gap-1 mt-2 text-orange-400/70 hover:text-orange-400 text-xs transition-colors"
              >
                <ChevronDown className={`w-3 h-3 transition-transform ${showReplies ? 'rotate-180' : ''}`} />
                {comment.replies.length} trả lời
              </button>
            )}
          </div>
        </div>

        {/* Nested replies */}
        {showReplies && comment.replies?.map(reply => (
          <CommentItem
            key={reply.id}
            comment={reply}
            postId={postId}
            currentUser={currentUser}
            isPostAuthor={isPostAuthor}
            onReply={onReply}
            onDelete={onDelete}
            onReact={onReact}
            onMarkSolution={onMarkSolution}
            onReport={onReport}
            onOpenImage={onOpenImage}
            depth={depth + 1}
          />
        ))}
      </div>
    </div>
  )
}

export default function CommentSection({ postId, comments = [], currentUser, isPostAuthor, onRefresh, onReport }) {
  const [replyTo, setReplyTo] = useState(null)
  const [lightboxImg, setLightboxImg] = useState(null)
  const commentCount = countCommentTree(comments)

  const handleSubmit = async ({ content, image, parent_id }) => {
    await forumService.createComment({
      post: postId,
      content,
      image: image || undefined,
      parent: parent_id || undefined,
    })
    onRefresh?.()
  }

  const handleDelete = async (commentId) => {
    if (!confirm('Xóa bình luận này?')) return
    await forumService.deleteComment(commentId)
    onRefresh?.()
  }

  const handleReact = async (commentId, type) => {
    await forumService.reactToComment(commentId, type)
    onRefresh?.()
  }

  const handleMarkSolution = async (commentId) => {
    await forumService.markSolution(commentId)
    onRefresh?.()
  }

  return (
    <div className="space-y-1">
      <h3 className="text-white font-semibold text-sm mb-4 flex items-center gap-2">
        💬 Bình luận
        <span className="text-white/30 font-normal">({commentCount})</span>
      </h3>

      {/* Comment input */}
      <div className="mb-4">
        <CommentInput
          onSubmit={handleSubmit}
          replyTo={replyTo}
          onCancelReply={() => setReplyTo(null)}
        />
      </div>

      {/* Comments list */}
      <div className="divide-y divide-white/5">
        {comments.map(comment => (
          <CommentItem
            key={comment.id}
            comment={comment}
            postId={postId}
            currentUser={currentUser}
            isPostAuthor={isPostAuthor}
            onReply={(c) => setReplyTo(c)}
            onDelete={handleDelete}
            onReact={handleReact}
            onMarkSolution={handleMarkSolution}
            onReport={onReport}
            onOpenImage={setLightboxImg}
          />
        ))}
      </div>

      {comments.length === 0 && (
        <div className="text-center py-8 text-white/20 text-sm">
          Chưa có bình luận nào. Hãy là người đầu tiên!
        </div>
      )}

      {lightboxImg && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8 cursor-pointer"
          onClick={() => setLightboxImg(null)}
        >
          <img src={lightboxImg} alt="" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}
    </div>
  )
}
