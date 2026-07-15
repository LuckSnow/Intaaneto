from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Exercise, Submission
from .serializers import ExerciseSerializer, SubmissionSerializer, SubmissionCreateSerializer


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Exercise.objects.filter(is_published=True)
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get user's submissions for this exercise"""
        exercise = self.get_object()
        submissions = Submission.objects.filter(
            exercise=exercise,
            user=request.user
        ).order_by('-submitted_at')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionCreateSerializer
        return SubmissionSerializer
    
    def perform_create(self, serializer):
        submission = serializer.save(user=self.request.user)
        # TODO: Implement code execution and testing logic
        # This would involve running the code against test cases
        # For now, just set it as pending
        submission.status = 'pending'
        submission.feedback = 'Bài nộp đang được xử lý...'
        submission.save()
