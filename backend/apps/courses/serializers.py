from rest_framework import serializers
from django.conf import settings

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
                  'video_url', 'ai_video_url', 'ai_summary', 'processing_status',
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
            'slug', 'teacher', 'total_students', 'average_rating', 'created_at',
            'updated_at',
        ]
    
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
        fields = '__all__'
        read_only_fields = ['enrolled_at', 'completed_at', 'progress_percentage']


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
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
