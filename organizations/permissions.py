from rest_framework import permissions
from .models import Membership


class IsOrganizationAdmin(permissions.BasePermission):
    """Allow only ADMIN role in organization"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers can do anything
        if request.user.is_superuser:
            return True
        
        # For creation, check if user is ADMIN role in their user model
        if request.method == 'POST':
            return request.user.role == 'ADMIN'
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Check if user is ADMIN in this organization
        membership = Membership.objects.filter(
            user=request.user,
            organization=obj if hasattr(obj, 'memberships') else obj.organization,
            role='ADMIN'
        ).first()
        
        return membership is not None


# class IsOrganizationManagerOrAdmin(permissions.BasePermission):
#     """Allow ADMIN and MANAGER roles"""
    
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
        
#         if request.user.is_superuser:
#             return True
        
#         return True
    
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_superuser:
#             return True
        
#         # Check if user is ADMIN or MANAGER in this organization
#         membership = Membership.objects.filter(
#             user=request.user,
#             organization=obj if hasattr(obj, 'memberships') else obj.organization,
#             role__in=['ADMIN', 'MANAGER']
#         ).first()
        
#         return membership is not None
class IsOrganizationManagerOrAdmin(permissions.BasePermission):
    """Allow ADMIN and MANAGER roles for creation/modification, MEMBER can read only"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Safe methods (GET, HEAD, OPTIONS) allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only ADMIN or MANAGER can POST/PUT/PATCH/DELETE
        return request.user.role in ['ADMIN', 'MANAGER']
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if request.method in permissions.SAFE_METHODS:
            return Membership.objects.filter(
                user=request.user,
                organization=obj if hasattr(obj, 'memberships') else obj.organization
            ).exists()
        
        # Only ADMIN or MANAGER in that organization can modify
        membership = Membership.objects.filter(
            user=request.user,
            organization=obj if hasattr(obj, 'memberships') else obj.organization,
            role__in=['ADMIN', 'MANAGER']
        ).first()
        
        return membership is not None


class IsOrganizationMember(permissions.BasePermission):
    """Allow any member of the organization"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Check if user is a member in this organization
        membership = Membership.objects.filter(
            user=request.user,
            organization=obj if hasattr(obj, 'memberships') else obj.organization
        ).first()
        
        return membership is not None