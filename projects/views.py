from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer, TaskStatusUpdateSerializer
from .permissions import CanManageProject, CanManageTask
from organizations.models import Membership


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, CanManageProject]
    
    def get_queryset(self):
        """Return projects for user's organizations only"""
        user = self.request.user
        
        if user.is_superuser:
            return Project.objects.all()
        
        # Get all organizations where user is a member
        user_orgs = Membership.objects.filter(user=user).values_list('organization', flat=True)
        return Project.objects.filter(organization__in=user_orgs)
    
    def perform_create(self, serializer):
        """Set owner to current user"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a project"""
        project = self.get_object()
        tasks = project.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, CanManageTask]
    
    def get_queryset(self):
        """Return tasks for user's organizations only"""
        user = self.request.user
        
        if user.is_superuser:
            return Task.objects.all()
        
        user_orgs = Membership.objects.filter(user=user).values_list('organization', flat=True)
        return Task.objects.filter(project__organization__in=user_orgs)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status with validation"""
        task = self.get_object()
        serializer = TaskStatusUpdateSerializer(
            data=request.data,
            context={'task': task}
        )
        
        if serializer.is_valid():
            task.status = serializer.validated_data['status']
            task.save()
            return Response({
                'message': 'Status updated successfully',
                'task': TaskSerializer(task).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get tasks grouped by status"""
        queryset = self.get_queryset()
        grouped_tasks = {
            'TODO': TaskSerializer(queryset.filter(status='TODO'), many=True).data,
            'IN_PROGRESS': TaskSerializer(queryset.filter(status='IN_PROGRESS'), many=True).data,
            'DONE': TaskSerializer(queryset.filter(status='DONE'), many=True).data,
        }
        return Response(grouped_tasks)