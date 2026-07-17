# Intaaneto database schema

Cập nhật: 2026-07-16. Nguồn chuẩn là Django models và migrations trong
`backend/apps/*`; tài liệu này mô tả các aggregate phục vụ đồ án, không thay thế
migration.

## Users và role workflow

### `users.User`

- Identity: email/username unique, full name, optional phone/avatar/bio.
- Server-owned role: `student`, `teacher`, `admin`.
- Active/verified flags và SHA-256 verification-token digest + creation time.
- Django permission/staff fields và timestamps.

### `users.Profile`

One-to-one với User; lưu thông tin học tập cơ bản hoặc specialization/years of
experience của teacher.

### `users.TeacherApplication`

Applicant, specialization, experience, reason, pending/approved/rejected,
reviewer/note/timestamps. Partial unique constraint chỉ cho một pending request
mỗi learner. Role chỉ đổi trong admin review transaction.

## Course và học tập

### `courses.Course`

Title/unique slug, description/thumbnail, difficulty/duration,
objectives/prerequisites, teacher FK, draft/published/featured, order và denormalized
student/rating counters. API teacher không được ghi featured.

### `courses.Lesson`

Course FK; unique `(course, slug)`; title/description/type/content; PDF upload và
extracted text; optional video fields; processing status/error; duration/order;
preview/published flags. Generated SadTalker output gắn vào `video_file`.

### `courses.Enrollment`

Unique `(user, course)`, enrollment/completion time, authoritative
`progress_percentage`, `mastery_percentage` và `last_accessed_lesson`.

### `courses.LessonProgress`

Unique `(user, lesson)`, completion state/time và time-spent field.

### `courses.Review` và `courses.LessonComment`

Learner-created course rating/comment và nested lesson comment. API ghi owner từ
request; cross-owner/cross-lesson mutation bị chặn.

### `courses.LessonVideoGenerationJob`

Audit record cho SadTalker local: lesson/requester/provider/status, approved
script, input checksums, consent assertion, safe failure code, output file và
timestamps. Check constraint yêu cầu rights/approval confirmation.

## Assessment và exercise

### `exercises.LessonAssessment`

One-to-one lesson; title/instructions; threshold 1–100; version; publish state.

### `exercises.AssessmentQuestion`

Assessment FK; prompt; JSON choices; correct-choice index; mandatory-by-API
learning objective; teacher explanation; unique `(assessment, order)`.

### `exercises.AssessmentAttempt`

Immutable server result: assessment/user, assessment-version + threshold
snapshot, decimal score/pass, counts, weak-objective list và submit time.

### `exercises.AssessmentAnswer`

Audit snapshot cho từng answer: prompt/choices/objective/correct choice tại thời
điểm submit, learner selection và correctness. Điều này giữ kết quả giải thích
được khi dữ liệu nguồn thay đổi.

### `exercises.AssessmentReinforcementEvent`

Audit tối thiểu khi learner lấy reinforcement packet thành công: attempt FK,
safe retrieval status, số objective, objective có evidence, citation count và
thời điểm. Không lưu prompt, excerpt hoặc learner identity lặp lại. Constraint
đảm bảo ready-objective count không vượt tổng objective.

Legacy `Exercise`/`Submission` vẫn tồn tại cho coding-exercise compatibility;
code execution/grading chưa được triển khai.

## RAG và chat

### `ai_assistant.KnowledgeSource`

Lesson/version/checksum, normalized text, ready/archived + active state, embedding
provider/model/revision/dimension và chunker config. Constraints đảm bảo một
active source/lesson và unique lesson version.

### `ai_assistant.KnowledgeChunk`

Source FK, stable ordinal, text/offset/char count và pgvector embedding. Chunk từ
PDF có `page_start/page_end` nullable, được suy ra deterministic từ marker trong
normalized source; constraint yêu cầu cả hai cùng null hoặc `page_end >=
page_start`. Unique `(source, ordinal)`. Retrieval luôn lọc authorized active
source trước ranking.

### `ai_assistant.ChatSession` và `ChatMessage`

Session thuộc user và giữ bounded lesson context. Message lưu role/content,
token/latency tùy provider và bounded retrieval metadata; không lưu embedding,
full prompt, provider error hoặc citation excerpt.

### `courses.LessonIngestionJob`

Trạng thái durable cho PDF worker: lesson/requester, server-owned task UUID,
queued/running/completed/failed, bounded attempt count, safe failure code/error,
source kết quả và timestamps. Conditional unique constraint chỉ cho một job
queued/running trên mỗi lesson. Polling API không trả task UUID hoặc requester.

### `exercises.DialogueKnowledgeCheckEvent`

Audit tối thiểu của knowledge check recommendation-only: passed attempt,
assessment version, question/objective, outcome, HMAC answer digest, selected
chunk IDs và bounded provider usage/latency. Không lưu raw answer, prompt, rubric,
answer key, feedback hoặc citation excerpt; record không tham gia progression.

## Forum

`Tag`, `Post`, nested `Comment`, `Reaction`, `Report`, `Follow` hỗ trợ cộng đồng.
Reaction/report có check constraint “đúng một target” và conditional unique
constraints; privileged pin/status được quản lý qua action riêng.

## Analytics

Legacy `LearningAnalytics`, `Achievement`, `UserAchievement` vẫn phục vụ các
counter/achievement cũ. Progress report mới **không** tin counter này; nó tổng
hợp read-only từ Enrollment, LessonProgress và AssessmentAttempt current-version.

## Quan hệ chính

```text
User ──< Course (teacher)
User ──< Enrollment >── Course ──< Lesson
User ──< LessonProgress >──────── Lesson
Lesson ──1 LessonAssessment ──< AssessmentQuestion
User ──< AssessmentAttempt ──< AssessmentAnswer
AssessmentAttempt ──< AssessmentReinforcementEvent
Lesson ──< KnowledgeSource ──< KnowledgeChunk
User ──< ChatSession ──< ChatMessage
Lesson ──< LessonVideoGenerationJob
```

## Migration quan trọng

- `ai_assistant.0003`: pgvector extension và vector schema path.
- `ai_assistant.0004`: retrieval metadata.
- `courses.0004`: enrollment mastery percentage.
- `courses.0005`: SadTalker audit job.
- `exercises.0002`: lesson assessment/attempt/answer và optional exercise lesson.
- `exercises.0003`: reinforcement audit event và count constraint.
- `forum.0004`: target/duplicate constraints cho reaction/report.

Chạy kiểm tra drift:

```bash
docker compose exec backend python manage.py makemigrations --check --dry-run
```
