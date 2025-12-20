from django.contrib import admin
from .models import Project, Task


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