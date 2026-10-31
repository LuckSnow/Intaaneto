import { useEffect, useId, useRef, useState } from 'react'
import { Check, Upload } from 'lucide-react'

export default function TutorAvatarPicker({ library, disabled, busy, onSelect, onUpload }) {
  const inputId = useId()
  const fileInput = useRef(null)
  const [file, setFile] = useState(null)
  const [label, setLabel] = useState('')
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!file) {
      setPreview('')
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const chooseFile = (event) => {
    const selected = event.target.files?.[0]
    if (!selected) return
    setError('')
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(selected.type) || selected.size > 5 * 1024 * 1024) {
      setError('Chọn ảnh PNG, JPEG hoặc WebP, tối đa 5 MB.')
      event.target.value = ''
      return
    }
    setFile(selected)
    setLabel(selected.name.replace(/\.[^.]+$/, '').slice(0, 80))
  }

  const saveUpload = async () => {
    if (!file) return
    if (await onUpload(file, label)) {
      setFile(null)
      setLabel('')
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  if (!library) {
    return <p className="mt-4 text-sm text-white/70">Chưa tải được thư viện avatar. Hãy mở lại phần biên soạn.</p>
  }

  const options = [
    ...library.presets.map((item) => ({ ...item, key: `preset-${item.id}`, selection: { preset_id: item.id }, selected: !library.selected.upload_id && library.selected.preset_id === item.id })),
    ...library.uploads.map((item) => ({ ...item, key: `upload-${item.id}`, selection: { upload_id: item.id }, selected: library.selected.upload_id === item.id })),
  ]
  const chosen = options.find((item) => item.selected)

  return (
    <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 text-slate-950">
      <fieldset disabled={disabled}>
        <legend className="font-medium">Ảnh AI Tutor trong video</legend>
        <p className="mt-1 text-sm text-slate-600">Chọn một trong 6 mẫu hoặc dùng ảnh của bạn. Lựa chọn được lưu cho bài học này.</p>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {options.map((item, index) => (
            <label key={item.key} className={`relative flex min-w-0 cursor-pointer flex-col rounded-lg border p-2 focus-within:ring-2 focus-within:ring-orange-600 ${item.selected ? 'border-orange-700 bg-orange-50' : 'border-slate-200 hover:border-slate-400'} ${disabled ? 'cursor-default opacity-60' : ''}`}>
              <input
                type="radio"
                name={`${inputId}-avatar`}
                value={item.key}
                checked={item.selected}
                onChange={() => onSelect(item.selection)}
                className="sr-only"
              />
              <img src={item.preview_url} alt="" className="h-24 w-full rounded object-contain" loading={index < 6 ? 'eager' : 'lazy'} />
              <span className="mt-2 break-words text-center text-sm">{item.label}</span>
              {item.selected && <Check className="absolute right-1 top-1 h-5 w-5 rounded bg-orange-700 text-white" aria-hidden="true" />}
            </label>
          ))}
        </div>
        <p className="mt-3 text-sm text-slate-600" role="status">{busy ? 'Đang lưu avatar…' : `Đang chọn: ${chosen?.label || 'AI Tutor'}`}</p>

        <div className="mt-4 border-t border-slate-200 pt-4">
          <label htmlFor={inputId} className="block text-sm font-medium">Tải avatar riêng</label>
          <p id={`${inputId}-help`} className="mt-1 text-sm text-slate-600">PNG, JPEG hoặc WebP · tối đa 5 MB · ảnh tĩnh 64–4096 px. Ảnh tải lên được lưu trong thư viện của bạn.</p>
          <input ref={fileInput} id={inputId} type="file" accept="image/png,image/jpeg,image/webp" onChange={chooseFile} aria-describedby={`${inputId}-help`} className="mt-2 block w-full min-w-0 rounded text-sm file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-slate-50 file:px-3 file:py-3 file:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-600" />
          {error && <p className="mt-2 text-sm text-red-700" role="alert">{error}</p>}
          {file && (
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
              <img src={preview} alt="Xem trước avatar tải lên" className="h-24 w-24 rounded-lg border border-slate-200 object-contain" />
              <label className="min-w-0 flex-1 text-sm font-medium">
                Tên avatar
                <input value={label} onChange={(event) => setLabel(event.target.value)} maxLength={80} className="mt-1 block min-h-11 w-full rounded-md border border-slate-300 px-3 font-normal focus:outline-none focus:ring-2 focus:ring-orange-600" />
              </label>
              <button type="button" onClick={saveUpload} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-slate-300 px-4 text-sm font-medium hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-600 disabled:opacity-50">
                <Upload className="h-4 w-4" aria-hidden="true" />
                Tải lên và sử dụng
              </button>
            </div>
          )}
        </div>
      </fieldset>
    </div>
  )
}
