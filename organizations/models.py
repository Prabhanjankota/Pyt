from django.db import models
from django.conf import settings


class Organization(models.Model):
    """Organization/Company model"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Team(models.Model):
    """Team model within an organization"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='teams'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['-created_at']
        unique_together = ['name', 'organization']
    
    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class Membership(models.Model):
    """User membership in organization with role"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('MEMBER', 'Member'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
        null=True,
        blank=True
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'memberships'
        unique_together = ['user', 'organization']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"