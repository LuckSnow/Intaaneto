from rest_framework import serializers
from django.db import transaction

from .models import (
    AssessmentAttempt,
    AssessmentQuestion,
    Exercise,
    LessonAssessment,
    Submission,
)


class ExerciseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'description', 'instructions', 'difficulty',
            'starter_code', 'max_points', 'hints', 'order', 'is_published',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class SubmissionSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ['user', 'status', 'points_earned', 'feedback', 'test_results', 'submitted_at']


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['exercise', 'code']


class AssessmentQuestionLearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = ['id', 'prompt', 'choices', 'learning_objective', 'order']
        read_only_fields = fields


class AssessmentQuestionTeacherSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(
        child=serializers.CharField(max_length=500, trim_whitespace=True),
        min_length=2,
        max_length=6,
    )

    class Meta:
        model = AssessmentQuestion
        fields = [
            'id', 'prompt', 'choices', 'correct_choice',
            'learning_objective', 'explanation', 'order',
        ]
        read_only_fields = ['id']

    def validate_choices(self, value):
        normalized = [choice.strip() for choice in value]
        if any(not choice for choice in normalized):
            raise serializers.ValidationError('Các lựa chọn không được để trống.')
        if len(set(normalized)) != len(normalized):
            raise serializers.ValidationError('Các lựa chọn không được trùng nhau.')
        return normalized

    def validate(self, attrs):
        choices = attrs.get('choices', getattr(self.instance, 'choices', []))
        correct_choice = attrs.get(
            'correct_choice',
            getattr(self.instance, 'correct_choice', None),
        )
        if correct_choice is None or correct_choice >= len(choices):
            raise serializers.ValidationError({
                'correct_choice': 'Đáp án đúng phải là chỉ số hợp lệ trong danh sách lựa chọn.'
            })
        return attrs


class LessonAssessmentLearnerSerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionLearnerSerializer(many=True, read_only=True)
    best_score = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()

    class Meta:
        model = LessonAssessment
        fields = [
            'id', 'lesson', 'title', 'instructions', 'pass_threshold',
            'version', 'questions', 'best_score', 'passed',
        ]
        read_only_fields = fields

    def _attempts(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return obj.attempts.none()
        return obj.attempts.filter(
            user=request.user,
            assessment_version=obj.version,
        )

    def get_best_score(self, obj):
        attempt = self._attempts(obj).order_by('-score', '-submitted_at').first()
        return attempt.score if attempt else None

    def get_passed(self, obj):
        return self._attempts(obj).filter(passed=True).exists()


class LessonAssessmentTeacherSerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionTeacherSerializer(many=True)

    class Meta:
        model = LessonAssessment
        fields = [
            'id', 'lesson', 'title', 'instructions', 'pass_threshold',
            'version', 'is_published', 'questions', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']

    def validate(self, attrs):
        if (
            self.instance
            and 'lesson' in attrs
            and attrs['lesson'].pk != self.instance.lesson_id
        ):
            raise serializers.ValidationError({
                'lesson': 'Không thể chuyển bài đánh giá sang bài học khác.'
            })
        questions = attrs.get('questions')
        will_publish = attrs.get(
            'is_published',
            getattr(self.instance, 'is_published', False),
        )
        has_existing_questions = self.instance and self.instance.questions.exists()
        if will_publish and questions is None and not has_existing_questions:
            raise serializers.ValidationError({
                'questions': 'Bài đánh giá đã xuất bản phải có ít nhất một câu hỏi.'
            })
        if will_publish and questions == []:
            raise serializers.ValidationError({
                'questions': 'Bài đánh giá đã xuất bản phải có ít nhất một câu hỏi.'
            })
        if questions is not None:
            orders = [question['order'] for question in questions]
            if len(orders) != len(set(orders)):
                raise serializers.ValidationError({
                    'questions': 'Thứ tự câu hỏi không được trùng nhau.'
                })
        return attrs

    @staticmethod
    def _create_questions(assessment, questions):
        AssessmentQuestion.objects.bulk_create([
            AssessmentQuestion(assessment=assessment, **question)
            for question in questions
        ])

    @transaction.atomic
    def create(self, validated_data):
        questions = validated_data.pop('questions', [])
        assessment = LessonAssessment.objects.create(**validated_data)
        self._create_questions(assessment, questions)
        return assessment

    @transaction.atomic
    def update(self, instance, validated_data):
        questions = validated_data.pop('questions', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.version += 1
        instance.save()
        if questions is not None:
            instance.questions.all().delete()
            self._create_questions(instance, questions)
        return instance


class AssessmentSubmissionAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(min_value=1)
    selected_choice = serializers.IntegerField(min_value=0)


class AssessmentSubmissionSerializer(serializers.Serializer):
    answers = AssessmentSubmissionAnswerSerializer(many=True, allow_empty=False)

    def validate_answers(self, value):
        question_ids = [answer['question_id'] for answer in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError('Mỗi câu hỏi chỉ được trả lời một lần.')
        return value


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'assessment_version', 'threshold_snapshot',
            'score', 'passed', 'total_questions', 'correct_answers',
            'weak_objectives', 'submitted_at',
        ]
        read_only_fields = fields
