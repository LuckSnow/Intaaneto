from rest_framework import serializers
from django.conf import settings
from django.db.models import Q
from django.utils.text import slugify

from .models import Course, Lesson, Enrollment, LessonProgress, Review, LessonComment


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'title', 'slug', 'description', 'lesson_type',
            'duration_minutes', 'order', 'is_preview', 'is_published',
        ]
        read_only_fields = fields


class LessonUploadSerializer(serializers.ModelSerializer):
    """Validate the public contract for a teacher-uploaded PDF lesson."""
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'description', 'uploaded_file', 'order', 'is_preview']
    
    def validate_uploaded_file(self, value):
        if value:
            ext = value.name.lower().rsplit('.', 1)[-1] if '.' in value.name else ''
            if ext != 'pdf':
                raise serializers.ValidationError('Chỉ hỗ trợ file PDF')
            if value.size > settings.LESSON_PDF_MAX_BYTES:
                raise serializers.ValidationError('File PDF vượt quá dung lượng cho phép')
            content_type = getattr(value, 'content_type', '')
            if content_type and content_type not in ('application/pdf', 'application/octet-stream'):
                raise serializers.ValidationError('Nội dung tải lên không phải PDF')

            position = value.tell()
            try:
                value.seek(0)
                if value.read(5) != b'%PDF-':
                    raise serializers.ValidationError('Nội dung tải lên không phải PDF hợp lệ')
            finally:
                value.seek(position)
        return value


class LessonDetailSerializer(serializers.ModelSerializer):
    """Full lesson detail including AI content for student view."""
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'slug', 'description', 'lesson_type', 'content',
                  'video_url', 'video_file', 'ai_video_url', 'ai_summary', 'processing_status',
                  'duration_minutes', 'order', 'is_preview', 'is_published',
                  'uploaded_file', 'comments_count', 'created_at']
        read_only_fields = ['slug', 'created_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class LessonCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonComment
        fields = ['id', 'lesson', 'user', 'user_name', 'user_avatar', 'parent',
                  'content', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, attrs):
        lesson = attrs.get('lesson', getattr(self.instance, 'lesson', None))
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        if parent is not None and (
            lesson is None or parent.lesson_id != lesson.id
        ):
            raise serializers.ValidationError(
                {'parent': 'Phản hồi phải thuộc cùng một bài học.'}
            )
        if self.instance is not None:
            if 'lesson' in attrs and lesson.pk != self.instance.lesson_id:
                raise serializers.ValidationError(
                    {'lesson': 'Không thể chuyển bình luận sang bài học khác.'}
                )
            if 'parent' in attrs and getattr(parent, 'pk', None) != self.instance.parent_id:
                raise serializers.ValidationError(
                    {'parent': 'Không thể thay đổi bình luận cha.'}
                )
        return attrs
    
    def get_user_avatar(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
        return None
    
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all()[:10]
            return LessonCommentSerializer(replies, many=True, context=self.context).data
        return []


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    lessons_count = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail', 'difficulty',
            'duration_hours', 'objectives', 'prerequisites', 'teacher',
            'teacher_name', 'is_published', 'is_featured', 'order',
            'total_students', 'average_rating', 'lessons_count', 'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'slug', 'teacher', 'is_featured', 'total_students',
            'average_rating', 'created_at', 'updated_at',
        ]

    def validate_title(self, value):
        if self.instance is None:
            generated_slug = slugify(value)
            if not generated_slug:
                raise serializers.ValidationError(
                    'Tiêu đề phải tạo được đường dẫn hợp lệ.'
                )
            if Course.objects.filter(slug=generated_slug).exists():
                raise serializers.ValidationError(
                    'Đã có khóa học với tiêu đề hoặc đường dẫn này.'
                )
        return value

    def validate(self, attrs):
        will_publish = attrs.get(
            'is_published',
            getattr(self.instance, 'is_published', False),
        )
        if will_publish:
            if self.instance is None:
                raise serializers.ValidationError({
                    'is_published': (
                        'Hãy tạo khóa học ở trạng thái nháp và thêm bài học '
                        'sẵn sàng trước khi xuất bản.'
                    )
                })
            has_usable_lesson = self.instance.lessons.filter(
                is_published=True,
            ).filter(
                Q(content__gt='')
                | Q(
                    knowledge_sources__is_active=True,
                    knowledge_sources__status='ready',
                )
            ).exists()
            if not has_usable_lesson:
                raise serializers.ValidationError({
                    'is_published': (
                        'Khóa học cần ít nhất một bài học đã xuất bản có nội '
                        'dung hoặc chỉ mục RAG sẵn sàng.'
                    )
                })
        return attrs
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()
    
    def get_thumbnail(self, obj):
        if not obj.thumbnail:
            return None
        url = str(obj.thumbnail)
        # External URL (Unsplash, etc.) → return as-is
        if url.startswith('http'):
            return url
        # Local file → build full URL
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return obj.thumbnail.url


class CourseDetailSerializer(CourseSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = [*CourseSerializer.Meta.fields, 'lessons']

    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_published=True)
        return LessonSerializer(lessons, many=True, context=self.context).data


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'user_name', 'course', 'course_title', 'enrolled_at',
            'completed_at', 'progress_percentage', 'mastery_percentage',
            'last_accessed_lesson',
        ]
        read_only_fields = fields


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'user_avatar', 'course', 'rating',
            'comment', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_course(self, value):
        if self.instance is not None and value.pk != self.instance.course_id:
            raise serializers.ValidationError(
                'Không thể chuyển đánh giá sang khóa học khác.'
            )
        return value
