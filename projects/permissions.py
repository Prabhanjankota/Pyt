from rest_framework import permissions
from organizations.models import Membership


class CanManageProject(permissions.BasePermission):
    """
    ADMIN: Full access to all projects in their orgs
    MANAGER: Can create and manage projects
    USER: Can view projects and manage assigned tasks
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Safe methods (GET, HEAD, OPTIONS) allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only ADMIN or MANAGER can create projects
        if view.action == 'create':
            return request.user.role in ['ADMIN', 'MANAGER']
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Get the project's organization
        project = obj if hasattr(obj, 'organization') else obj.project
        
        # Check if user is a member of the organization
        membership = Membership.objects.filter(
            user=request.user,
            organization=project.organization
        ).first()
        
        if not membership:
            return False
        
        # Safe methods allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only ADMIN or MANAGER can modify/delete
        return membership.role in ['ADMIN', 'MANAGER']


class CanManageTask(permissions.BasePermission):
    """
    ADMIN/MANAGER: Full task access
    USER: Can view all tasks, edit tasks assigned to them
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Everyone can view and create tasks
        if request.method in permissions.SAFE_METHODS or view.action == 'create':
            return True
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Get the task's project organization
        task = obj
        
        # Check if user is a member of the organization
        membership = Membership.objects.filter(
            user=request.user,
            organization=task.project.organization
        ).first()
        
        if not membership:
            return False
        
        # Safe methods allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # ADMIN or MANAGER can do anything
        if membership.role in ['ADMIN', 'MANAGER']:
            return True
        
        # USERS can only edit tasks assigned to them or reported by them
        if membership.role == 'USER':
            return task.assignee == request.user or task.reporter == request.user
        
        return False