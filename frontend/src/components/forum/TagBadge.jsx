export default function TagBadge({ tag, selected = false, onClick, size = 'sm' }) {
  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px]',
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  }

  return (
    <button
      onClick={() => onClick?.(tag)}
      className={`inline-flex items-center gap-1 rounded-full font-medium transition-all duration-200 ${sizeClasses[size]} ${
        selected
          ? 'ring-1 ring-offset-1 ring-offset-transparent scale-105'
          : 'hover:scale-105'
      }`}
      style={{
        backgroundColor: (tag.color || '#f97316') + (selected ? '40' : '20'),
        color: tag.color || '#f97316',
        ...(selected ? { ringColor: tag.color || '#f97316' } : {}),
      }}
    >
      <span>#</span>
      <span>{tag.name}</span>
      {tag.posts_count !== undefined && (
        <span className="opacity-50 ml-0.5">({tag.posts_count})</span>
      )}
    </button>
  )
}
