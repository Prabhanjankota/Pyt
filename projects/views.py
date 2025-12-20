from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Project, Task, Comment, ActivityLog
from .serializers import (
    ProjectSerializer, TaskSerializer, TaskStatusUpdateSerializer,
    CommentSerializer, ActivityLogSerializer
)
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
        old_status = task.status
        
        serializer = TaskStatusUpdateSerializer(
            data=request.data,
            context={'task': task}
        )
        
        if serializer.is_valid():
            task.status = serializer.validated_data['status']
            task.save()
            
            # Create activity log with correct actor
            ActivityLog.objects.create(
                actor=request.user,
                action='STATUS_CHANGED',
                description=f'Changed status from {old_status} to {task.status}',
                task=task,
                project=task.project,
                metadata={
                    'old_status': old_status,
                    'new_status': task.status,
                }
            )
            
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


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment CRUD operations
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return comments for tasks in user's organizations"""
        user = self.request.user
        
        if user.is_superuser:
            return Comment.objects.all()
        
        user_orgs = Membership.objects.filter(user=user).values_list('organization', flat=True)
        return Comment.objects.filter(task__project__organization__in=user_orgs)
    
    @action(detail=False, methods=['get'])
    def task_comments(self, request):
        """Get all comments for a specific task"""
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'error': 'task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comments = self.get_queryset().filter(task_id=task_id)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Activity Logs (read-only)
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return activity logs for user's organizations"""
        user = self.request.user
        
        if user.is_superuser:
            return ActivityLog.objects.all()
        
        user_orgs = Membership.objects.filter(user=user).values_list('organization', flat=True)
        return ActivityLog.objects.filter(project__organization__in=user_orgs)
    
    @action(detail=False, methods=['get'])
    def task_activity(self, request):
        """Get all activity for a specific task"""
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'error': 'task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activities = self.get_queryset().filter(task_id=task_id)
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def project_activity(self, request):
        """Get all activity for a specific project"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': 'project_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activities = self.get_queryset().filter(project_id=project_id)
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_activity(self, request):
        """Get current user's activity"""
        activities = self.get_queryset().filter(actor=request.user)
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)