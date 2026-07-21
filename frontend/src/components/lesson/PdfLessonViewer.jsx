import { useEffect, useRef, useState } from 'react'
import { ExternalLink, FileText, Loader2, Maximize2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { courseService } from '../../services/courseService'

export default function PdfLessonViewer({ lessonId, pdfUrl, title }) {
  const containerRef = useRef(null)
  const [objectUrl, setObjectUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let localUrl = ''

    courseService.getLessonPdfBlob(lessonId)
      .then((blob) => {
        if (!active) return
        localUrl = URL.createObjectURL(blob)
        setObjectUrl(localUrl)
      })
      .catch(() => {
        if (active) setError('Không thể tải trình xem PDF trong trang.')
      })

    return () => {
      active = false
      if (localUrl) URL.revokeObjectURL(localUrl)
    }
  }, [lessonId])

  const openFullscreen = async () => {
    try {
      await containerRef.current?.requestFullscreen?.()
    } catch {
      setError('Trình duyệt không cho phép mở toàn màn hình. Bạn có thể mở PDF trong tab mới.')
    }
  }

  return (
    <section ref={containerRef} className="overflow-hidden rounded-xl border border-slate-300 bg-slate-950">
      <div className="flex flex-col gap-3 border-b border-slate-700 bg-slate-900 p-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-2 text-sm text-slate-200">
          <FileText className="h-4 w-4 shrink-0 text-orange-400" aria-hidden="true" />
          <span className="truncate">{title}</span>
          <span className="hidden text-slate-400 md:inline">Dùng thanh PDF để tìm kiếm, chuyển trang và thu phóng.</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={openFullscreen} className="border-slate-600 bg-slate-800 text-white hover:bg-slate-700 hover:text-white">
            <Maximize2 className="mr-2 h-4 w-4" aria-hidden="true" /> Toàn màn hình
          </Button>
          <a href={objectUrl || pdfUrl} target="_blank" rel="noreferrer" className="inline-flex h-9 items-center justify-center rounded-md border border-slate-600 bg-slate-800 px-3 text-sm font-medium text-white hover:bg-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500">
            <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" /> Mở tab mới
          </a>
        </div>
      </div>

      {error && <p className="border-b border-red-800 bg-red-950 p-3 text-sm text-red-200" role="alert">{error}</p>}
      {!objectUrl && !error && (
        <div className="flex h-[65vh] min-h-96 items-center justify-center gap-2 text-slate-300" role="status">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Đang tải PDF…
        </div>
      )}
      {objectUrl && (
        <iframe
          src={`${objectUrl}#toolbar=1&navpanes=0&view=FitH`}
          title={`PDF bài học: ${title}`}
          className="h-[72vh] min-h-[32rem] w-full bg-white"
        />
      )}
    </section>
  )
}
