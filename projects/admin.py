from django.contrib import admin
from .models import Project, Task, Comment, ActivityLog


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for projects"""
    
    list_display = ['name', 'organization', 'owner', 'status', 'created_at']
    list_filter = ['status', 'organization', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'organization', 'owner')
        }),
        ('Status & Dates', {
            'fields': ('status', 'start_date', 'end_date')
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for tasks"""
    
    list_display = ['title', 'project', 'assignee', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'project', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'project')
        }),
        ('Assignment', {
            'fields': ('assignee', 'reporter')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'due_date')
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for comments"""
    
    list_display = ['id', 'author', 'task', 'content_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__email', 'task__title']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        """Show first 50 characters of comment"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for activity logs"""
    
    list_display = ['id', 'actor', 'action', 'description_preview', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['description', 'actor__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['actor', 'action', 'description', 'task', 'project', 'comment', 'metadata', 'created_at']
    
    def description_preview(self, obj):
        """Show first 50 characters of description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
    
    def has_add_permission(self, request):
        """Don't allow manual creation of logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of logs"""
        return False