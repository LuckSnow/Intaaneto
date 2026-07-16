import { useEffect, useState } from 'react'
import {
  AlertCircle,
  ClipboardCheck,
  Loader2,
  Plus,
  Save,
  Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'

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

const inputClass = 'mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20 disabled:bg-slate-100'
const MAX_QUESTIONS = 50

export default function TeacherAssessments() {
  const [courses, setCourses] = useState([])
  const [lessons, setLessons] = useState([])
  const [courseId, setCourseId] = useState('')
  const [lessonId, setLessonId] = useState('')
  const [assessmentId, setAssessmentId] = useState(null)
  const [version, setVersion] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loadingCourses, setLoadingCourses] = useState(true)
  const [loadingLessons, setLoadingLessons] = useState(false)
  const [loadingAssessment, setLoadingAssessment] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const data = await assessmentService.getManagedCourses()
        if (!active) return
        setCourses(data)
        setCourseId(data[0] ? String(data[0].id) : '')
      } catch (requestError) {
        if (active) setError(firstError(requestError.response?.data) || 'Không thể tải khóa học được quản lý.')
      } finally {
        if (active) setLoadingCourses(false)
      }
    }
    load()
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    setLessonId('')
    setAssessmentId(null)
    setVersion(null)
    setForm(emptyForm())
    if (!courseId) {
      setLessons([])
      return () => { active = false }
    }
    setLoadingLessons(true)
    setError('')
    assessmentService.getManagedLessons(courseId)
      .then((data) => {
        if (!active) return
        setLessons(data)
        setLessonId(data[0] ? String(data[0].id) : '')
      })
      .catch((requestError) => {
        if (active) setError(firstError(requestError.response?.data) || 'Không thể tải danh sách bài học.')
      })
      .finally(() => {
        if (active) setLoadingLessons(false)
      })
    return () => { active = false }
  }, [courseId])

  useEffect(() => {
    let active = true
    setAssessmentId(null)
    setVersion(null)
    setForm(emptyForm())
    if (!lessonId) return () => { active = false }
    setLoadingAssessment(true)
    setError('')
    assessmentService.getForLesson(lessonId)
      .then((data) => {
        if (!active || !data) return
        setAssessmentId(data.id)
        setVersion(data.version)
        setForm({
          title: data.title,
          instructions: data.instructions || '',
          pass_threshold: data.pass_threshold,
          is_published: data.is_published,
          questions: data.questions.length > 0
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
        if (active) setError(firstError(requestError.response?.data) || 'Không thể tải bài đánh giá.')
      })
      .finally(() => {
        if (active) setLoadingAssessment(false)
      })
    return () => { active = false }
  }, [lessonId])

  const updateQuestion = (index, changes) => {
    setForm((current) => ({
      ...current,
      questions: current.questions.map((question, questionIndex) => (
        questionIndex === index ? { ...question, ...changes } : question
      )),
    }))
  }

  const updateChoice = (questionIndex, choiceIndex, value) => {
    const choices = [...form.questions[questionIndex].choices]
    choices[choiceIndex] = value
    updateQuestion(questionIndex, { choices })
  }

  const addChoice = (questionIndex) => {
    const question = form.questions[questionIndex]
    if (question.choices.length >= 6) return
    updateQuestion(questionIndex, { choices: [...question.choices, ''] })
  }

  const removeChoice = (questionIndex, choiceIndex) => {
    const question = form.questions[questionIndex]
    if (question.choices.length <= 2) return
    const choices = question.choices.filter((_, index) => index !== choiceIndex)
    let correctChoice = question.correct_choice
    if (choiceIndex === correctChoice) correctChoice = 0
    if (choiceIndex < correctChoice) correctChoice -= 1
    updateQuestion(questionIndex, {
      choices,
      correct_choice: correctChoice,
    })
  }

  const addQuestion = () => {
    if (form.questions.length >= MAX_QUESTIONS) return
    setForm((current) => ({
      ...current,
      questions: [
        ...current.questions,
        newQuestion(current.questions.length + 1),
      ],
    }))
  }

  const removeQuestion = (index) => {
    if (form.questions.length <= 1) return
    setForm((current) => ({
      ...current,
      questions: current.questions
        .filter((_, questionIndex) => questionIndex !== index)
        .map((question, questionIndex) => ({
          ...question,
          order: questionIndex + 1,
        })),
    }))
  }

  const validate = () => {
    if (!lessonId) return 'Hãy chọn một bài học.'
    if (!form.title.trim()) return 'Tiêu đề bài đánh giá không được để trống.'
    if (form.pass_threshold < 1 || form.pass_threshold > 100) return 'Ngưỡng đạt phải từ 1 đến 100.'
    for (const [index, question] of form.questions.entries()) {
      if (!question.prompt.trim()) return `Câu ${index + 1} chưa có nội dung.`
      if (!question.learning_objective.trim()) return `Câu ${index + 1} chưa có mục tiêu học tập.`
      const choices = question.choices.map((choice) => choice.trim())
      if (choices.some((choice) => !choice)) return `Câu ${index + 1} có lựa chọn trống.`
      if (new Set(choices).size !== choices.length) return `Câu ${index + 1} có lựa chọn trùng nhau.`
    }
    return ''
  }

  const handleSave = async (event) => {
    event.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setSaving(true)
    setError('')
    const payload = {
      lesson: Number(lessonId),
      title: form.title.trim(),
      instructions: form.instructions.trim(),
      pass_threshold: Number(form.pass_threshold),
      is_published: form.is_published,
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
      toast.success(assessmentId ? 'Đã cập nhật bài đánh giá.' : 'Đã tạo bài đánh giá.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể lưu bài đánh giá.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!assessmentId) return
    if (!window.confirm('Xóa bài đánh giá này? Hành động không thể hoàn tác.')) return
    setSaving(true)
    setError('')
    try {
      await assessmentService.remove(assessmentId)
      setAssessmentId(null)
      setVersion(null)
      setForm(emptyForm())
      toast.success('Đã xóa bài đánh giá.')
    } catch (requestError) {
      const message = firstError(requestError.response?.data) || 'Không thể xóa bài đánh giá.'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const busy = loadingCourses || loadingLessons || loadingAssessment

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 py-8">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <ClipboardCheck className="h-7 w-7 text-orange-700" aria-hidden="true" />
            <h1 className="text-2xl font-bold text-slate-950">Biên soạn bài đánh giá</h1>
          </div>
          <p className="mt-2 max-w-3xl text-slate-600">
            Tạo câu hỏi trắc nghiệm theo mục tiêu học tập. Điểm, ngưỡng đạt và tiến độ được backend xác định.
          </p>
        </header>

        <section className="mb-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 sm:grid-cols-2" aria-label="Chọn bài học">
          <label className="text-sm font-medium text-slate-800">
            Khóa học quản lý
            <select className={inputClass} value={courseId} onChange={(event) => setCourseId(event.target.value)} disabled={loadingCourses || courses.length === 0}>
              {courses.length === 0 && <option value="">Chưa có khóa học</option>}
              {courses.map((course) => <option key={course.id} value={course.id}>{course.title}{course.is_published ? '' : ' — Bản nháp'}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-800">
            Bài học
            <select className={inputClass} value={lessonId} onChange={(event) => setLessonId(event.target.value)} disabled={loadingLessons || lessons.length === 0}>
              {lessons.length === 0 && <option value="">Chưa có bài học</option>}
              {lessons.map((lesson) => <option key={lesson.id} value={lesson.id}>{lesson.order}. {lesson.title}{lesson.is_published ? '' : ' — Bản nháp'}</option>)}
            </select>
          </label>
        </section>

        {error && (
          <div className="mb-6 flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {busy ? (
          <div className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white p-12 text-slate-600" role="status">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            Đang tải dữ liệu biên soạn…
          </div>
        ) : !lessonId ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-600">
            Hãy tạo hoặc tải lên ít nhất một bài học trước khi biên soạn đánh giá.
          </div>
        ) : (
          <form onSubmit={handleSave} className="space-y-6">
            <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Thông tin chung</h2>
                  <p className="text-sm text-slate-600">{assessmentId ? `Đang chỉnh sửa phiên bản ${version}` : 'Chưa có bài đánh giá cho lesson này'}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-sm font-medium ${form.is_published ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}`}>
                  {form.is_published ? 'Đã xuất bản' : 'Bản nháp'}
                </span>
              </div>
              <div className="grid gap-5">
                <label className="text-sm font-medium text-slate-800">
                  Tiêu đề
                  <input className={inputClass} maxLength={255} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
                </label>
                <label className="text-sm font-medium text-slate-800">
                  Hướng dẫn cho học viên
                  <textarea className={inputClass} rows={3} maxLength={2000} value={form.instructions} onChange={(event) => setForm({ ...form, instructions: event.target.value })} />
                </label>
                <div className="grid gap-5 sm:grid-cols-2">
                  <label className="text-sm font-medium text-slate-800">
                    Ngưỡng đạt (%)
                    <input className={inputClass} type="number" min="1" max="100" value={form.pass_threshold} onChange={(event) => setForm({ ...form, pass_threshold: Number(event.target.value) })} required />
                  </label>
                  <label className="flex min-h-11 items-center gap-3 self-end rounded-lg border border-slate-200 px-4 py-3 text-sm font-medium text-slate-800">
                    <input type="checkbox" className="h-4 w-4 accent-orange-700" checked={form.is_published} onChange={(event) => setForm({ ...form, is_published: event.target.checked })} />
                    Cho phép học viên làm bài
                  </label>
                </div>
              </div>
            </section>

            {form.questions.map((question, questionIndex) => (
              <section key={questionIndex} className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <h2 className="font-semibold text-slate-950">Câu {questionIndex + 1}</h2>
                  <Button type="button" variant="ghost" size="sm" className="text-red-700 hover:bg-red-50 hover:text-red-800" onClick={() => removeQuestion(questionIndex)} disabled={form.questions.length === 1}>
                    <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" /> Xóa câu
                  </Button>
                </div>
                <div className="grid gap-5">
                  <label className="text-sm font-medium text-slate-800">
                    Nội dung câu hỏi
                    <textarea className={inputClass} rows={2} maxLength={2000} value={question.prompt} onChange={(event) => updateQuestion(questionIndex, { prompt: event.target.value })} required />
                  </label>
                  <label className="text-sm font-medium text-slate-800">
                    Mục tiêu học tập được đánh giá
                    <input className={inputClass} maxLength={255} value={question.learning_objective} onChange={(event) => updateQuestion(questionIndex, { learning_objective: event.target.value })} required />
                  </label>
                  <fieldset>
                    <legend className="text-sm font-medium text-slate-800">Các lựa chọn và đáp án đúng</legend>
                    <div className="mt-3 space-y-3">
                      {question.choices.map((choice, choiceIndex) => (
                        <div key={choiceIndex} className="flex items-center gap-3">
                          <input type="radio" name={`correct-${questionIndex}`} aria-label={`Chọn lựa chọn ${choiceIndex + 1} làm đáp án đúng`} checked={question.correct_choice === choiceIndex} onChange={() => updateQuestion(questionIndex, { correct_choice: choiceIndex })} className="h-4 w-4 shrink-0 accent-orange-700" />
                          <input className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-slate-950 outline-none focus:border-orange-600 focus:ring-2 focus:ring-orange-600/20" value={choice} onChange={(event) => updateChoice(questionIndex, choiceIndex, event.target.value)} aria-label={`Lựa chọn ${choiceIndex + 1}`} maxLength={500} required />
                          <Button type="button" variant="ghost" size="icon" className="shrink-0 text-slate-500 hover:bg-red-50 hover:text-red-700" onClick={() => removeChoice(questionIndex, choiceIndex)} disabled={question.choices.length <= 2} aria-label={`Xóa lựa chọn ${choiceIndex + 1}`}>
                            <Trash2 className="h-4 w-4" aria-hidden="true" />
                          </Button>
                        </div>
                      ))}
                    </div>
                    <Button type="button" variant="outline" size="sm" className="mt-3" onClick={() => addChoice(questionIndex)} disabled={question.choices.length >= 6}>
                      <Plus className="mr-2 h-4 w-4" aria-hidden="true" /> Thêm lựa chọn
                    </Button>
                  </fieldset>
                  <label className="text-sm font-medium text-slate-800">
                    Giải thích đáp án (hiện chỉ dùng cho giáo viên)
                    <textarea className={inputClass} rows={2} maxLength={2000} value={question.explanation} onChange={(event) => updateQuestion(questionIndex, { explanation: event.target.value })} />
                  </label>
                </div>
              </section>
            ))}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Button type="button" variant="outline" onClick={addQuestion} disabled={form.questions.length >= MAX_QUESTIONS} className="border-slate-300 bg-white text-slate-800">
                <Plus className="mr-2 h-4 w-4" aria-hidden="true" /> Thêm câu hỏi
              </Button>
              <div className="flex flex-col gap-3 sm:flex-row">
                {assessmentId && (
                  <Button type="button" variant="outline" onClick={handleDelete} disabled={saving} className="border-red-300 bg-white text-red-700 hover:bg-red-50">
                    <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" /> Xóa bài
                  </Button>
                )}
                <Button type="submit" disabled={saving} className="bg-orange-700 text-white hover:bg-orange-800">
                  {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <Save className="mr-2 h-4 w-4" aria-hidden="true" />}
                  {assessmentId ? 'Lưu thay đổi' : 'Tạo bài đánh giá'}
                </Button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
