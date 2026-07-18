import os

from django.core.management.base import BaseCommand
from apps.courses.models import Course, Lesson
from apps.users.models import User


class Command(BaseCommand):
    help = 'Seed initial courses data'

    def handle(self, *args, **kwargs):
        # Get or create teacher user
        teacher, teacher_created = User.objects.get_or_create(
            email='teacher@intaaneto.com',
            defaults={
                'username': 'teacher',
                'full_name': 'Giáo viên Demo',
                'role': 'teacher',
                'is_active': True
            }
        )
        demo_password = os.getenv('DEMO_TEACHER_PASSWORD', '')
        if demo_password:
            teacher.set_password(demo_password)
            teacher.save(update_fields=['password', 'updated_at'])
        elif teacher_created:
            teacher.set_unusable_password()
            teacher.save(update_fields=['password', 'updated_at'])

        # Create courses
        courses_data = [
            {
                'title': 'Python Cơ Bản - Lập Trình Cho Người Mới Bắt Đầu',
                'slug': 'python-co-ban',
                'description': 'Khóa học Python từ cơ bản đến nâng cao. Học cú pháp, cấu trúc dữ liệu, OOP và xây dựng dự án thực tế.',
                'difficulty': 'beginner',
                'duration_hours': 40,
                'thumbnail': 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=450&fit=crop&fm=webp&q=80',
                'lessons': [
                    {'title': 'Giới thiệu về Python', 'order': 1, 'duration': 30},
                    {'title': 'Biến và kiểu dữ liệu', 'order': 2, 'duration': 45},
                    {'title': 'Cấu trúc điều kiện', 'order': 3, 'duration': 40},
                    {'title': 'Vòng lặp trong Python', 'order': 4, 'duration': 50},
                    {'title': 'Hàm và Module', 'order': 5, 'duration': 60},
                ]
            },
            {
                'title': 'Lập Trình Web với Django Framework',
                'slug': 'django-framework',
                'description': 'Xây dựng ứng dụng web full-stack với Django. Học MTV pattern, ORM, authentication, REST API và deployment.',
                'difficulty': 'intermediate',
                'duration_hours': 60,
                'thumbnail': 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=450&fit=crop&fm=webp&q=80',
                'lessons': [
                    {'title': 'Cài đặt và cấu hình Django', 'order': 1, 'duration': 30},
                    {'title': 'Models và Database', 'order': 2, 'duration': 60},
                    {'title': 'Views và Templates', 'order': 3, 'duration': 55},
                    {'title': 'Forms và Validation', 'order': 4, 'duration': 50},
                    {'title': 'Authentication System', 'order': 5, 'duration': 70},
                ]
            },
            {
                'title': 'JavaScript Modern - ES6+ và React',
                'slug': 'javascript-react',
                'description': 'Nắm vững JavaScript hiện đại và React framework. Học ES6+, async/await, hooks, state management và xây dựng SPA.',
                'difficulty': 'intermediate',
                'thumbnail': 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&h=450&fit=crop&fm=webp&q=80',
                'duration_hours': 50,
                'lessons': [
                    {'title': 'ES6+ Features', 'order': 1, 'duration': 45},
                    {'title': 'React Basics và JSX', 'order': 2, 'duration': 50},
                    {'title': 'Components và Props', 'order': 3, 'duration': 55},
                    {'title': 'State và Lifecycle', 'order': 4, 'duration': 60},
                    {'title': 'React Hooks', 'order': 5, 'duration': 65},
                ]
            },
            {
                'title': 'Data Science với Python',
                'slug': 'data-science-python',
                'description': 'Khám phá Data Science với Python. Học NumPy, Pandas, Matplotlib, Machine Learning cơ bản và phân tích dữ liệu.',
                'difficulty': 'advanced',
                'thumbnail': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=450&fit=crop&fm=webp&q=80',
                'duration_hours': 80,
                'lessons': [
                    {'title': 'NumPy và Arrays', 'order': 1, 'duration': 50},
                    {'title': 'Pandas DataFrame', 'order': 2, 'duration': 60},
                    {'title': 'Data Visualization', 'order': 3, 'duration': 55},
                    {'title': 'Machine Learning Basics', 'order': 4, 'duration': 90},
                    {'title': 'Scikit-learn Tutorial', 'order': 5, 'duration': 80},
                ]
            },
            {
                'title': 'HTML & CSS - Thiết Kế Web Responsive',
                'slug': 'html-css-responsive',
                'description': 'Học HTML5, CSS3, Flexbox, Grid và tạo website responsive đẹp mắt. Thực hành với dự án thực tế.',
                'difficulty': 'beginner',
                'thumbnail': 'https://images.unsplash.com/photo-1507721999472-8ed4421c4af2?w=800&h=450&fit=crop&fm=webp&q=80',
                'duration_hours': 30,
                'lessons': [
                    {'title': 'HTML5 Fundamentals', 'order': 1, 'duration': 40},
                    {'title': 'CSS3 Styling', 'order': 2, 'duration': 50},
                    {'title': 'Flexbox Layout', 'order': 3, 'duration': 45},
                    {'title': 'CSS Grid System', 'order': 4, 'duration': 55},
                    {'title': 'Responsive Design', 'order': 5, 'duration': 60},
                ]
            },
            {
                'title': 'Node.js và Express - Backend Development',
                'slug': 'nodejs-express',
                'description': 'Xây dựng REST API với Node.js và Express. Học async programming, database integration, authentication và best practices.',
                'thumbnail': 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=450&fit=crop&fm=webp&q=80',
                'difficulty': 'intermediate',
                'duration_hours': 50,
                'lessons': [
                    {'title': 'Node.js Basics', 'order': 1, 'duration': 40},
                    {'title': 'Express Framework', 'order': 2, 'duration': 50},
                    {'title': 'REST API Design', 'order': 3, 'duration': 60},
                    {'title': 'MongoDB Integration', 'order': 4, 'duration': 55},
                    {'title': 'JWT Authentication', 'order': 5, 'duration': 65},
                ]
            },
        ]

        for course_data in courses_data:
            lessons_data = course_data.pop('lessons')
            
            course, created = Course.objects.get_or_create(
                slug=course_data['slug'],
                defaults={
                    **course_data,
                    'teacher': teacher,
                    'is_published': True,
                    'total_students': 0,
                }
            )
            
            if created:
                # Create lessons
                for lesson_data in lessons_data:
                    Lesson.objects.create(
                        course=course,
                        title=lesson_data['title'],
                        order=lesson_data['order'],
                        duration_minutes=lesson_data['duration'],
                        is_published=True
                    )
                
                self.stdout.write(self.style.SUCCESS(f'✓ Created course: {course.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Course already exists: {course.title}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding completed!'))
        self.stdout.write(self.style.SUCCESS(f'Total courses: {Course.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total lessons: {Lesson.objects.count()}'))
