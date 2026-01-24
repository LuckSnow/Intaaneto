# Database Schema Documentation

## Overview

Intaaneto sử dụng PostgreSQL làm database chính với các bảng được tổ chức theo modules.

## Tables

### Users Module

#### User
- `id`: BigAutoField (PK)
- `email`: EmailField (unique, indexed)
- `username`: CharField (unique, indexed)
- `full_name`: CharField
- `role`: CharField (choices: student, parent, teacher, admin)
- `phone_number`: CharField
- `date_of_birth`: DateField
- `avatar`: ImageField
- `bio`: TextField
- `is_staff`: BooleanField
- `is_active`: BooleanField
- `is_verified`: BooleanField
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

**Indexes:**
- (email, role)
- (username)

#### Profile
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User) - OneToOne
- `grade_level`: CharField
- `school_name`: CharField
- `learning_style`: CharField
- `student_id`: ForeignKey(User) - for parents
- `specialization`: CharField - for teachers
- `years_of_experience`: PositiveIntegerField
- `notification_enabled`: BooleanField
- `email_notification`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Courses Module

#### Course
- `id`: BigAutoField (PK)
- `title`: CharField
- `slug`: SlugField (unique, indexed)
- `description`: TextField
- `thumbnail`: ImageField
- `difficulty`: CharField (choices: beginner, intermediate, advanced)
- `duration_hours`: PositiveIntegerField
- `objectives`: TextField
- `prerequisites`: TextField
- `teacher_id`: ForeignKey(User)
- `is_published`: BooleanField
- `is_featured`: BooleanField
- `order`: PositiveIntegerField
- `total_students`: PositiveIntegerField
- `average_rating`: DecimalField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

**Indexes:**
- (slug)
- (is_published, difficulty)

#### Lesson
- `id`: BigAutoField (PK)
- `course_id`: ForeignKey(Course)
- `title`: CharField
- `slug`: SlugField
- `description`: TextField
- `lesson_type`: CharField (choices: video, text, interactive, quiz)
- `content`: TextField
- `video_url`: URLField
- `video_file`: FileField
- `attachments`: FileField
- `duration_minutes`: PositiveIntegerField
- `order`: PositiveIntegerField
- `is_preview`: BooleanField
- `is_published`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

**Indexes:**
- (course_id, order)

**Unique Together:** (course, slug)

#### Enrollment
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `course_id`: ForeignKey(Course)
- `enrolled_at`: DateTimeField
- `completed_at`: DateTimeField (nullable)
- `progress_percentage`: DecimalField
- `last_accessed_lesson_id`: ForeignKey(Lesson)

**Unique Together:** (user, course)

#### LessonProgress
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `lesson_id`: ForeignKey(Lesson)
- `is_completed`: BooleanField
- `completed_at`: DateTimeField
- `time_spent_minutes`: PositiveIntegerField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

**Unique Together:** (user, lesson)

#### Review
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `course_id`: ForeignKey(Course)
- `rating`: PositiveSmallIntegerField (1-5)
- `comment`: TextField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

**Unique Together:** (user, course)

### Exercises Module

#### Exercise
- `id`: BigAutoField (PK)
- `lesson_id`: ForeignKey(Lesson)
- `title`: CharField
- `description`: TextField
- `instructions`: TextField
- `difficulty`: CharField (choices: easy, medium, hard)
- `starter_code`: TextField
- `solution_code`: TextField
- `test_cases`: JSONField
- `max_points`: PositiveIntegerField
- `hints`: JSONField
- `order`: PositiveIntegerField
- `is_published`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

#### Submission
- `id`: BigAutoField (PK)
- `exercise_id`: ForeignKey(Exercise)
- `user_id`: ForeignKey(User)
- `code`: TextField
- `status`: CharField (choices: pending, passed, failed, error)
- `points_earned`: PositiveIntegerField
- `feedback`: TextField
- `test_results`: JSONField
- `execution_time_ms`: PositiveIntegerField
- `memory_used_kb`: PositiveIntegerField
- `submitted_at`: DateTimeField

**Indexes:**
- (user_id, exercise_id)
- (status)

### Forum Module

#### Post
- `id`: BigAutoField (PK)
- `author_id`: ForeignKey(User)
- `title`: CharField
- `content`: TextField
- `category`: CharField (choices: question, discussion, showcase, announcement)
- `tags`: JSONField
- `views_count`: PositiveIntegerField
- `likes_count`: PositiveIntegerField
- `is_pinned`: BooleanField
- `is_closed`: BooleanField
- `is_solved`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

**Indexes:**
- (category, -created_at)
- (-is_pinned, -created_at)

#### Comment
- `id`: BigAutoField (PK)
- `post_id`: ForeignKey(Post)
- `author_id`: ForeignKey(User)
- `parent_id`: ForeignKey(Comment) - self-referencing
- `content`: TextField
- `likes_count`: PositiveIntegerField
- `is_solution`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

#### Like
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `post_id`: ForeignKey(Post) (nullable)
- `comment_id`: ForeignKey(Comment) (nullable)
- `created_at`: DateTimeField

**Unique Together:** 
- (user, post)
- (user, comment)

### AI Assistant Module

#### ChatSession
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `title`: CharField
- `context`: JSONField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

#### ChatMessage
- `id`: BigAutoField (PK)
- `session_id`: ForeignKey(ChatSession)
- `role`: CharField (choices: user, assistant, system)
- `content`: TextField
- `tokens_used`: PositiveIntegerField
- `response_time_ms`: PositiveIntegerField
- `created_at`: DateTimeField

### Analytics Module

#### Achievement
- `id`: BigAutoField (PK)
- `name`: CharField
- `description`: TextField
- `icon`: ImageField
- `criteria_type`: CharField
- `criteria_value`: PositiveIntegerField
- `points`: PositiveIntegerField
- `created_at`: DateTimeField

#### UserAchievement
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User)
- `achievement_id`: ForeignKey(Achievement)
- `earned_at`: DateTimeField

**Unique Together:** (user, achievement)

#### LearningAnalytics
- `id`: BigAutoField (PK)
- `user_id`: ForeignKey(User) - OneToOne
- `total_learning_time_minutes`: PositiveIntegerField
- `total_courses_enrolled`: PositiveIntegerField
- `total_courses_completed`: PositiveIntegerField
- `total_exercises_submitted`: PositiveIntegerField
- `total_exercises_passed`: PositiveIntegerField
- `total_forum_posts`: PositiveIntegerField
- `total_forum_comments`: PositiveIntegerField
- `total_ai_interactions`: PositiveIntegerField
- `current_streak_days`: PositiveIntegerField
- `longest_streak_days`: PositiveIntegerField
- `last_activity_date`: DateField
- `total_points`: PositiveIntegerField
- `updated_at`: DateTimeField

## Relationships

### One-to-One
- User ↔ Profile
- User ↔ LearningAnalytics

### One-to-Many
- User → Courses (as teacher)
- Course → Lessons
- Lesson → Exercises
- User → Enrollments
- User → Submissions
- User → Posts
- Post → Comments
- User → ChatSessions
- ChatSession → ChatMessages

### Many-to-Many (through tables)
- User ↔ Course (through Enrollment)
- User ↔ Lesson (through LessonProgress)
- User ↔ Achievement (through UserAchievement)

## Indexes Strategy

1. **Primary Keys**: Tất cả tables có indexed PK
2. **Foreign Keys**: Auto-indexed
3. **Custom Indexes**:
   - User: email, username, (email, role)
   - Course: slug, (is_published, difficulty)
   - Lesson: (course_id, order)
   - Post: (category, created_at), (is_pinned, created_at)

## Data Integrity

- Foreign key constraints với CASCADE/SET_NULL
- Unique constraints cho business logic
- Check constraints trong application layer
- Default values cho boolean fields
