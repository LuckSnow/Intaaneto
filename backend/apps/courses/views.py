from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, Enrollment, LessonProgress, Review
from .serializers import (
    CourseSerializer, CourseDetailSerializer, LessonSerializer,
    EnrollmentSerializer, LessonProgressSerializer, ReviewSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_published=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll in a course"""
        course = self.get_object()
        user = request.user
        
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course
        )
        
        if created:
            course.total_students += 1
            course.save()
            return Response(
                {'message': 'Enrolled successfully'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """Get user's progress in this course"""
        course = self.get_object()
        enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.filter(is_published=True)
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        progress.is_completed = True
        progress.save()
        
        return Response({'message': 'Lesson marked as completed'})


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            course_id = self.request.query_params.get('course')
            if course_id:
                return Review.objects.filter(course_id=course_id)
        return Review.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
