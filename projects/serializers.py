from rest_framework import serializers
from .models import Project, Task
from django.contrib.auth import get_user_model

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'organization', 'organization_name',
            'owner', 'owner_email', 'status', 'start_date', 'end_date',
            'task_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        """Get total number of tasks in project"""
        return obj.tasks.count()


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    
    assignee_email = serializers.EmailField(source='assignee.email', read_only=True)
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'assignee', 'assignee_email', 'reporter', 'reporter_email',
            'status', 'priority', 'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate task data"""
        # Ensure assignee belongs to same organization as project
        if attrs.get('assignee'):
            project = attrs.get('project') or (self.instance.project if self.instance else None)
            
            if project:
                assignee = attrs['assignee']
                
                # Check if assignee is a member of the project's organization
                from organizations.models import Membership
                if not Membership.objects.filter(
                    user=assignee, 
                    organization=project.organization
                ).exists():
                    raise serializers.ValidationError({
                        'assignee': 'Assignee must be a member of the project organization'
                    })
        
        return attrs
    
    def create(self, validated_data):
        """Set reporter to current user"""
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)

class TaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status with validation"""
    
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    
    def validate_status(self, value):
        """Validate status transition"""
        task = self.context['task']
        if not task.can_transition_to(value):
            raise serializers.ValidationError(
                f"Cannot transition from {task.status} to {value}. "
                f"Valid transitions: {', '.join(task.can_transition_to.__code__.co_consts[1].get(task.status, []))}"
            )
        return value