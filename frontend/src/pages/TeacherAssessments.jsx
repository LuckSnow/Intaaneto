import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Check,
  ClipboardCheck,
  Copy,
  Eye,
  Loader2,
  Plus,
  Save,
  Trash2,
  X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { assessmentService } from '../services/assessmentService'

const newQuestion = (order = 1) => ({
  prompt: '',
  choices: ['', ''],
  correct_choice: 0,
  learning_objective: '',
  explanation: '',
  order,
})

const emptyForm = () => ({
  title: '',
  instructions: '',
  pass_threshold: 70,
  is_published: false,
  questions: [newQuestion()],
})

const firstError = (value) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return firstError(value[0])
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) {
      const message = firstError(item)
      if (message) return message
    }
  }
  return ''
}

const questionIssues = (question) => {
  const issues = []
  if (!question.prompt.trim()) issues.push('Thiếu nội dung')
  if (!question.learning_objective.trim()) issues.push('Thiếu mục tiêu học tập')
  if (question.choices.length < 2 || question.choices.some((choice) => !choice.trim())) issues.push('Thiếu lựa chọn')
  if (new Set(question.choices.map((choice) => choice.trim()).filter(Boolean)).size !== question.choices.filter((choice) => choice.trim()).length) issues.push('Lựa chọn bị trùng')
  if (question.correct_choice < 0 || question.correct_choice >= question.choices.length) issues.push('Chưa chọn đáp án đúng')
  return issues
}

const inputClass = 'mt-2 w-full rounded-lg border border-white/15 bg-black/20 px-3 py-2.5 text-white outline-none transition placeholder:text-white/35 focus:border-orange-400 focus:ring-2 focus:ring-orange-400/20 disabled:opacity-60'
const MAX_QUESTIONS = 50

export default function TeacherAssessments() {
  const { courseId, lessonId } = useParams()
  const [course, setCourse] = useState(null)
  const [lesson, setLesson] = useState(null)
  const [assessmentId, setAssessmentId] = useState(null)
  const [version, setVersion] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [selectedQuestion, setSelectedQuestion] = useState(0)
  const [questionFilter, setQuestionFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [dirty, setDirty] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)

  useEffect(() => {
    let active = true
    Promise.all([
      assessmentService.getManagedCourses(),
      assessmentService.getManagedLessons(courseId),
    ])
      .then(async ([courses, lessons]) => {
        const ownedCourse = courses.find((item) => String(item.id) === String(courseId))
        const ownedLesson = lessons.find((item) => String(item.id) === String(lessonId))
        if (!ownedCourse || !ownedLesson) throw new Error('NOT_OWNED')
        if (!active) return
        setCourse(ownedCourse)
        setLesson(ownedLesson)
        const data = await assessmentService.getForLesson(lessonId)
        if (!active || !data) return
        setAssessmentId(data.id)
        setVersion(data.version)
        setForm({
          title: data.title,
          instructions: data.instructions || '',
          pass_threshold: data.pass_threshold,
          is_published: data.is_published,
          questions: data.questions.length
            ? data.questions.map((question, index) => ({
              prompt: question.prompt,
              choices: [...question.choices],
              correct_choice: question.correct_choice,
              learning_objective: question.learning_objective || '',
              explanation: question.explanation || '',
              order: index + 1,
            }))
            : [newQuestion()],
        })
      })
      .catch((requestError) => {
        if (!active) return
        setError(requestError.message === 'NOT_OWNED'
          ? 'Không tìm thấy bài học trong khóa học bạn được quyền quản lý.'
          : firstError(requestError.response?.data) || 'Không thể tải bài đánh giá.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [courseId, lessonId])

  useEffect(() => {
    const warnBeforeLeaving = (event) => {
      if (!dirty) return
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', warnBeforeLeaving)
    return () => window.removeEventListener('beforeunload', warnBeforeLeaving)
  }, [dirty])

  const setFormDirty = (updater) => {
    setForm(updater)
    setDirty(true)
  }

  const statuses = useMemo(() => form.questions.map(questionIssues), [form.questions])
  const visibleQuestionIndexes = useMemo(() => statuses
    .map((issues, index) => ({ issues, index }))
    .filter(({ issues }) => questionFilter === 'all' || (questionFilter === 'complete' ? issues.length === 0 : issues.length > 0))
    .map(({ index }) => index), [questionFilter, statuses])
  const currentQuestion = form.questions[selectedQuestion]

  const updateQuestion = (index, changes) => {
    setFormDirty((current) => ({
      ...current,
      questions: current.questions.map((question, questionIndex) => (
        questionIndex === index ? { ...question, ...changes } : question
      )),
    }))
  }

  const updateChoice = (choiceIndex, value) => {
    const choices = [...currentQuestion.choices]
    choices[choiceIndex] = value
    updateQuestion(selectedQuestion, { choices })
  }

  const addChoice = () => {
    if (currentQuestion.choices.length >= 6) return
    updateQuestion(selectedQuestion, { choices: [...currentQuestion.choices, ''] })
  }

  const removeChoice = (choiceIndex) => {
    if (currentQuestion.choices.length <= 2) return
    const choices = currentQuestion.choices.filter((_, index) => index !== choiceIndex)
    let correctChoice = currentQuestion.correct_choice
    if (choiceIndex === correctChoice) correctChoice = 0
    if (choiceIndex < correctChoice) correctChoice -= 1
    updateQuestion(selectedQuestion, { choices, correct_choice: correctChoice })
  }

  const addQuestion = () => {
    if (form.questions.length >= MAX_QUESTIONS) return
    const nextIndex = form.questions.length
    setFormDirty((current) => ({ ...current, questions: [...current.questions, newQuestion(nextIndex + 1)] }))
    setSelectedQuestion(nextIndex)
    setQuestionFilter('all')
  }

  const duplicateQuestion = () => {
    if (form.questions.length >= MAX_QUESTIONS) return
    const clone = { ...currentQuestion, choices: [...currentQuestion.choices] }
    const questions = [...form.questions]
    questions.splice(selectedQuestion + 1, 0, clone)
    setFormDirty((current) => ({ ...current, questions: questions.map((question, index) => ({ ...question, order: index + 1 })) }))
    setSelectedQuestion(selectedQuestion + 1)
  }

  const removeQuestion = () => {
    if (form.questions.length <= 1) return
    setFormDirty((current) => ({
      ...current,
      questions: current.questions
        .filter((_, index) => index !== selectedQuestion)
        .map((question, index) => ({ ...question, order: index + 1 })),
    }))
    setSelectedQuestion(Math.max(0, selectedQuestion - 1))
  }

  const moveQuestion = (direction) => {
    const destination = selectedQuestion + direction
    if (destination < 0 || destination >= form.questions.length) return
    const questions = [...form.questions]
    ;[questions[selectedQuestion], questions[destination]] = [questions[destination], questions[selectedQuestion]]
    setFormDirty((current) => ({ ...current, questions: questions.map((question, index) => ({ ...question, order: index + 1 })) }))
    setSelectedQuestion(destination)
  }

  const validate = (publishing) => {
    if (!form.title.trim()) return { message: 'Tiêu đề bài đánh giá không được để trống.' }
    if (form.pass_threshold < 1 || form.pass_threshold > 100) return { message: 'Ngưỡng đạt phải từ 1 đến 100.' }
    const invalidIndex = statuses.findIndex((issues) => issues.length > 0)
    if (invalidIndex >= 0) {
      const count = statuses.filter((issues) => issues.length > 0).length
      return { message: `${count} câu hỏi chưa hoàn chỉnh${publishing ? ', chưa thể xuất bản.' : '.'}`, questionIndex: invalidIndex }
    }
    return null
  }

  const saveAssessment = async (published) => {
    const validationError = validate(published)
    if (validationError) {
      setError(validationError.message)
      if (validationError.questionIndex !== undefined) {
        setQuestionFilter('all')
        setSelectedQuestion(validationError.questionIndex)
      }
      toast.error(validationError.message)
      return
    }
    setSaving(true)
    setError('')
    const payload = {
      lesson: Number(lessonId),
      title: form.title.trim(),
      instructions: form.instructions.trim(),
      pass_threshold: Number(form.pass_threshold),
      is_published: published,
      questions: form.questions.map((question, index) => ({
        prompt: question.prompt.trim(),
        choices: question.choices.map((choice) => choice.trim()),
        correct_choice: Number(question.correct_choice),
        learning_objective: question.learning_objective.trim(),
        explanation: question.explanation.trim(),
        order: index + 1,
      })),
    }
    try {
      const saved = assessmentId
        ? await assessmentService.update(assessmentId, payload)
        : await assessmentService.create(payload)
      setAssessmentId(saved.id)
      setVersion(saved.version)
      setForm((current) => ({ ...current, is_published: saved.is_published }))
      setDirty(false)
      toast.success(published ? 'Đã xuất bản bài đánh giá.' : 'Đã lưu bản nháp.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể lưu bài đánh giá.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!assessmentId || !window.confirm('Xóa bài đánh giá này? Hành động không thể hoàn tác.')) return
    setSaving(true)
    try {
      await assessmentService.remove(assessmentId)
      setAssessmentId(null)
      setVersion(null)
      setForm(emptyForm())
      setSelectedQuestion(0)
      setDirty(false)
      toast.success('Đã xóa bài đánh giá.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể xóa bài đánh giá.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="flex min-h-[50vh] items-center justify-center gap-2 text-white/70" role="status"><Loader2 className="h-5 w-5 animate-spin" />Đang tải trình biên soạn…</div>
  }

  if (error && (!course || !lesson)) {
    return <div className="mx-auto max-w-3xl py-10 text-white"><div className="rounded-2xl border border-white/15 bg-white/10 p-6"><h1 className="text-xl font-bold">Không thể mở trình biên soạn</h1><p className="mt-2 text-white/65">{error}</p><Link to="/teacher/courses" className="mt-5 inline-flex min-h-11 items-center font-semibold text-orange-300"><ArrowLeft className="mr-2 h-4 w-4" />Quản lý khóa học</Link></div></div>
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] pb-24 text-white">
      <nav aria-label="Breadcrumb" className="overflow-x-auto text-sm text-white/55">
        <ol className="flex min-h-11 items-center gap-2 whitespace-nowrap">
          <li><Link to="/" className="hover:text-orange-300">Trang chủ</Link></li><li>/</li>
          <li><Link to="/teacher/courses" className="hover:text-orange-300">Quản lý khóa học</Link></li><li>/</li>
          <li><Link to={`/teacher/courses/${course.id}`} className="hover:text-orange-300">{course.title}</Link></li><li>/</li>
          <li><Link to={`/lessons/${lesson.id}`} className="hover:text-orange-300">{lesson.title}</Link></li><li>/</li>
          <li className="font-semibold text-white" aria-current="page">Biên soạn bài đánh giá</li>
        </ol>
      </nav>

      <header className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div><div className="flex items-center gap-3"><ClipboardCheck className="h-7 w-7 text-orange-300" /><h1 className="text-2xl font-bold">Biên soạn bài đánh giá</h1></div><p className="mt-2 text-white/60">{course.title} · {lesson.title}</p></div>
        <Link to={`/teacher/courses/${course.id}`} className="inline-flex min-h-11 items-center rounded-lg border border-white/15 px-4 text-sm font-semibold hover:bg-white/10"><ArrowLeft className="mr-2 h-4 w-4" />Quay lại chi tiết khóa học</Link>
      </header>

      {error && <div className="mt-5 flex gap-3 rounded-xl border border-red-300/30 bg-red-950/40 p-4 text-sm text-red-100" role="alert"><AlertCircle className="h-5 w-5 shrink-0" /><span>{error}</span></div>}

      <div className="mt-6 grid gap-5 lg:grid-cols-[minmax(260px,30%)_minmax(0,1fr)]">
        <aside className="self-start rounded-2xl border border-white/15 bg-[#26192a]/85 p-4 lg:sticky lg:top-24">
          <div className="flex items-center justify-between"><div><h2 className="font-bold">Danh sách câu hỏi</h2><p className="mt-1 text-xs text-white/50">{form.questions.length} câu hỏi</p></div><Button type="button" size="sm" onClick={addQuestion} disabled={form.questions.length >= MAX_QUESTIONS} className="bg-orange-600 text-white hover:bg-orange-700"><Plus className="mr-1.5 h-4 w-4" />Thêm câu</Button></div>
          <div className="mt-4 grid grid-cols-3 gap-1 rounded-lg bg-black/20 p-1 text-xs">
            {[['all', 'Tất cả'], ['complete', 'Hoàn chỉnh'], ['incomplete', 'Còn thiếu']].map(([value, label]) => <button key={value} type="button" onClick={() => setQuestionFilter(value)} className={`min-h-9 rounded-md px-2 ${questionFilter === value ? 'bg-orange-600 font-semibold text-white' : 'text-white/60 hover:bg-white/10'}`}>{label}</button>)}
          </div>
          <div className="mt-3 max-h-[58vh] space-y-1 overflow-y-auto">
            {visibleQuestionIndexes.map((index) => {
              const question = form.questions[index]
              const issues = statuses[index]
              return <button key={index} type="button" onClick={() => setSelectedQuestion(index)} className={`w-full rounded-lg border p-3 text-left transition ${selectedQuestion === index ? 'border-orange-400 bg-orange-500/15' : 'border-transparent hover:bg-white/5'}`}><div className="flex items-center justify-between gap-2"><strong className="text-sm">Câu {index + 1}</strong>{issues.length ? <AlertCircle className="h-4 w-4 text-orange-300" /> : <Check className="h-4 w-4 text-emerald-300" />}</div><p className="mt-1 truncate text-xs text-white/55">{question.prompt || 'Chưa có nội dung câu hỏi'}</p><p className={`mt-2 text-xs ${issues.length ? 'text-orange-200' : 'text-emerald-200'}`}>{issues[0] || `${question.choices.length} lựa chọn · Hoàn chỉnh`}</p></button>
            })}
            {!visibleQuestionIndexes.length && <p className="py-5 text-center text-sm text-white/50">Không có câu hỏi phù hợp.</p>}
          </div>
        </aside>

        <main className="space-y-5">
          <section className="rounded-2xl border border-white/15 bg-[#26192a]/85 p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-bold">Thông tin bài đánh giá</h2><p className="mt-1 text-sm text-white/50">{assessmentId ? `Phiên bản ${version}` : 'Bài đánh giá mới'}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${form.is_published ? 'bg-emerald-400/15 text-emerald-200' : 'bg-white/10 text-white/65'}`}>{form.is_published ? 'Đã xuất bản' : 'Bản nháp'}</span></div>
            <div className="mt-5 grid gap-4">
              <label className="text-sm font-medium">Tiêu đề<input className={inputClass} maxLength={255} value={form.title} onChange={(event) => setFormDirty((current) => ({ ...current, title: event.target.value }))} /></label>
              <label className="text-sm font-medium">Hướng dẫn cho học viên<textarea className={inputClass} rows={2} maxLength={2000} value={form.instructions} onChange={(event) => setFormDirty((current) => ({ ...current, instructions: event.target.value }))} /></label>
              <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium">Ngưỡng đạt (%)<input className={inputClass} type="number" min="1" max="100" value={form.pass_threshold} onChange={(event) => setFormDirty((current) => ({ ...current, pass_threshold: Number(event.target.value) }))} /></label><div className="rounded-lg border border-white/10 p-3 text-sm"><p className="font-medium">Trạng thái làm bài</p><p className="mt-1 text-white/55">{form.is_published ? 'Học viên có thể làm phiên bản đã xuất bản.' : 'Học viên chưa thể làm bản nháp.'}</p></div></div>
            </div>
          </section>

          <section className="rounded-2xl border border-white/15 bg-[#26192a]/85 p-5 sm:p-6">
            <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-300">Câu {selectedQuestion + 1}</p><h2 className="mt-1 text-lg font-bold">Chỉnh sửa câu hỏi</h2></div>
            <div className="mt-5 grid gap-5">
              <label className="text-sm font-medium">Nội dung câu hỏi<textarea className={inputClass} rows={3} maxLength={2000} value={currentQuestion.prompt} onChange={(event) => updateQuestion(selectedQuestion, { prompt: event.target.value })} /></label>
              <label className="text-sm font-medium">Mục tiêu học tập được đánh giá<input className={inputClass} maxLength={255} placeholder="Ví dụ: Phân biệt được tín hiệu Analog và Digital." value={currentQuestion.learning_objective} onChange={(event) => updateQuestion(selectedQuestion, { learning_objective: event.target.value })} /></label>
              <fieldset><legend className="text-sm font-medium">Các lựa chọn và đáp án đúng</legend><div className="mt-3 space-y-2">{currentQuestion.choices.map((choice, choiceIndex) => {
                const correct = currentQuestion.correct_choice === choiceIndex
                return <div key={choiceIndex} className={`flex flex-wrap items-center gap-2 rounded-lg border p-2 ${correct ? 'border-orange-400 bg-orange-500/10' : 'border-white/10'}`}><input type="radio" name={`correct-${selectedQuestion}`} checked={correct} onChange={() => updateQuestion(selectedQuestion, { correct_choice: choiceIndex })} className="h-4 w-4 accent-orange-500" aria-label={`Chọn lựa chọn ${choiceIndex + 1} là đáp án đúng`} /><input value={choice} onChange={(event) => updateChoice(choiceIndex, event.target.value)} className="min-h-10 min-w-40 flex-1 rounded-md border border-white/15 bg-black/20 px-3 text-sm outline-none focus:border-orange-400" aria-label={`Lựa chọn ${choiceIndex + 1}`} />{correct && <span className="text-xs font-semibold text-orange-200">Đáp án đúng</span>}<button type="button" onClick={() => removeChoice(choiceIndex)} disabled={currentQuestion.choices.length <= 2} className="flex h-10 w-10 items-center justify-center rounded-md text-white/45 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-30" aria-label={`Xóa lựa chọn ${choiceIndex + 1}`}><Trash2 className="h-4 w-4" /></button></div>
              })}</div><Button type="button" variant="ghost" size="sm" onClick={addChoice} disabled={currentQuestion.choices.length >= 6} className="mt-3 text-orange-300 hover:bg-white/10 hover:text-orange-200"><Plus className="mr-2 h-4 w-4" />Thêm lựa chọn</Button></fieldset>
              <label className="text-sm font-medium">Giải thích đáp án<textarea className={inputClass} rows={2} maxLength={2000} value={currentQuestion.explanation} onChange={(event) => updateQuestion(selectedQuestion, { explanation: event.target.value })} /><span className="mt-1 block text-xs font-normal text-white/45">Hiện được lưu cho giảng viên theo contract hiện tại.</span></label>
              <div className="flex flex-wrap gap-2 border-t border-white/10 pt-4"><Button type="button" variant="outline" onClick={duplicateQuestion} disabled={form.questions.length >= MAX_QUESTIONS} className="border-white/15 bg-transparent text-white hover:bg-white/10"><Copy className="mr-2 h-4 w-4" />Nhân bản</Button><Button type="button" variant="outline" onClick={() => moveQuestion(-1)} disabled={selectedQuestion === 0} className="border-white/15 bg-transparent text-white hover:bg-white/10"><ArrowUp className="mr-2 h-4 w-4" />Lên</Button><Button type="button" variant="outline" onClick={() => moveQuestion(1)} disabled={selectedQuestion === form.questions.length - 1} className="border-white/15 bg-transparent text-white hover:bg-white/10"><ArrowDown className="mr-2 h-4 w-4" />Xuống</Button><Button type="button" variant="ghost" onClick={removeQuestion} disabled={form.questions.length <= 1} className="ml-auto text-red-300 hover:bg-red-500/10 hover:text-red-200"><Trash2 className="mr-2 h-4 w-4" />Xóa câu hỏi</Button></div>
            </div>
          </section>
        </main>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/15 bg-[#211424]/95 px-4 py-3 backdrop-blur-md"><div className="mx-auto flex max-w-7xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><p className="text-xs text-white/55">{saving ? 'Đang lưu…' : dirty ? 'Có thay đổi chưa lưu' : 'Đã lưu'}</p><div className="flex flex-wrap gap-2"><Button type="button" variant="outline" onClick={() => setPreviewOpen(true)} className="border-white/15 bg-transparent text-white hover:bg-white/10"><Eye className="mr-2 h-4 w-4" />Xem trước</Button>{assessmentId && <Button type="button" variant="ghost" onClick={handleDelete} disabled={saving} className="text-red-300 hover:bg-red-500/10 hover:text-red-200"><Trash2 className="mr-2 h-4 w-4" />Xóa bài</Button>}<Button type="button" onClick={() => saveAssessment(false)} disabled={saving} className="bg-white/10 text-white hover:bg-white/20"><Save className="mr-2 h-4 w-4" />Lưu nháp</Button><Button type="button" onClick={() => saveAssessment(true)} disabled={saving} className="bg-orange-600 text-white hover:bg-orange-700">{saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}Xuất bản</Button></div></div></div>

      {previewOpen && <div className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/80 p-3 sm:p-6" onMouseDown={(event) => event.target === event.currentTarget && setPreviewOpen(false)}><section role="dialog" aria-modal="true" aria-labelledby="preview-title" className="max-h-[94vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-slate-50 p-5 text-slate-950 shadow-2xl sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-700">Xem trước giao diện học viên</p><h2 id="preview-title" className="mt-1 text-2xl font-bold">{form.title || 'Bài đánh giá chưa có tiêu đề'}</h2><p className="mt-2 text-sm text-slate-600">{form.instructions || 'Không có hướng dẫn.'}</p></div><button type="button" onClick={() => setPreviewOpen(false)} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg hover:bg-slate-200" aria-label="Đóng xem trước"><X className="h-5 w-5" /></button></div><div className="mt-6 space-y-5">{form.questions.map((question, index) => <article key={index} className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">Câu {index + 1}. {question.prompt || 'Chưa có nội dung'}</h3><div className="mt-3 grid gap-2">{question.choices.map((choice, choiceIndex) => <label key={choiceIndex} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-sm"><input type="radio" disabled />{choice || `Lựa chọn ${choiceIndex + 1}`}</label>)}</div></article>)}</div><Button type="button" onClick={() => setPreviewOpen(false)} className="mt-6 bg-orange-700 text-white hover:bg-orange-800"><ArrowLeft className="mr-2 h-4 w-4" />Quay lại biên soạn</Button></section></div>}
    </div>
  )
}
