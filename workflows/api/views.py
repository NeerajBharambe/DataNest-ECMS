from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from workflows.models import Task
from .serializers import TaskSerializer


class MyTasksAPI(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user,
            status='PENDING'
        )


class ReviewTaskAPI(generics.UpdateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()

    def update(self, request, *args, **kwargs):
        task = self.get_object()

        if task.assigned_to != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        action = request.data.get('action')
        comments = request.data.get('comments', '')

        if action not in ['APPROVED', 'REJECTED']:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.status = action
        task.comments = comments
        task.save()

        return Response(
            {'message': f'Task {action.lower()} successfully'}
        )
