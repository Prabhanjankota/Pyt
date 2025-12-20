from django.db import models
from django.conf import settings
from organizations.models import Organization

User = settings.AUTH_USER_MODEL


class Project(models.Model):
    """Project model - container for tasks"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_projects'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class Task(models.Model):
    """Task model - individual work items"""
    
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_tasks'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def can_transition_to(self, new_status):
        """Validate status transitions"""
        valid_transitions = {
            'TODO': ['IN_PROGRESS'],
            'IN_PROGRESS': ['TODO', 'DONE'],
            'DONE': ['IN_PROGRESS'],
        }
        return new_status in valid_transitions.get(self.status, [])
    def save(self, *args, **kwargs):
        """Override save to create activity logs and feed items"""
        is_update = self.pk is not None
        old_status = None
        
        if is_update:
            try:
                old_task = Task.objects.get(pk=self.pk)
                old_status = old_task.status
            except Task.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Import here to avoid circular imports
        from .feed_utils import create_feed_item
        
        if not is_update:
            # New task created
            ActivityLog.objects.create(
                actor=self.reporter,
                action='TASK_CREATED',
                description=f'Created task "{self.title}"',
                task=self,
                project=self.project,
                metadata={
                    'task_id': self.id,
                    'task_title': self.title,
                    'priority': self.priority,
                }
            )
            
            # Create feed item
            create_feed_item(
                actor=self.reporter,
                activity_type='TASK_CREATED',
                title=f'created task "{self.title}"',
                description=f'Created a new task in project {self.project.name}',
                task=self,
                project=self.project,
                organization=self.project.organization,
                metadata={
                    'priority': self.priority,
                    'status': self.status,
                }
            )
            
        elif old_status and old_status != self.status:
            # Status changed
            ActivityLog.objects.create(
                actor=None,
                action='STATUS_CHANGED',
                description=f'Changed status from {old_status} to {self.status}',
                task=self,
                project=self.project,
                metadata={
                    'old_status': old_status,
                    'new_status': self.status,
                }
            )   
class Comment(models.Model):
    """Comment model - discussions on tasks"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    mentioned_users = models.ManyToManyField(
        User,
        related_name='mentions',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.title}"
    
    def extract_mentions(self):
        """Extract @mentions from comment content"""
        import re
        # Find all @email patterns
        pattern = r'@(\S+@\S+\.\S+)'
        emails = re.findall(pattern, self.content)
        return emails
    
    def save(self, *args, **kwargs):
        """Override save to process mentions"""
        super().save(*args, **kwargs)
        
        # Extract and link mentioned users
        mentioned_emails = self.extract_mentions()
        if mentioned_emails:
            mentioned_users = User.objects.filter(email__in=mentioned_emails)
            self.mentioned_users.set(mentioned_users)


class ActivityLog(models.Model):
    """Activity log - audit trail of all actions"""
    
    ACTION_CHOICES = [
        ('TASK_CREATED', 'Task Created'),
        ('TASK_UPDATED', 'Task Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('COMMENT_ADDED', 'Comment Added'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('PROJECT_CREATED', 'Project Created'),
    ]
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Generic relation fields (can point to any model)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )
    
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.actor.email if self.actor else 'System'} - {self.action} at {self.created_at}"
    

class Feed(models.Model):
    """Feed model - aggregated activity stream for social timeline"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('TASK_CREATED', 'Task Created'),
        ('TASK_UPDATED', 'Task Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('COMMENT_ADDED', 'Comment Added'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('PROJECT_CREATED', 'Project Created'),
        ('USER_MENTIONED', 'User Mentioned'),
    ]
    
    # Actor (who did the action)
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feed_activities'
    )
    
    # Activity type
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    
    # Target objects (what was acted upon)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feed_items'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feed_items'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feed_items'
    )
    
    # Organization for scoping
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='feed_items'
    )
    
    # Feed content
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feeds'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.actor.email} - {self.activity_type} at {self.created_at}"