from django.contrib import admin
from .models import Organization, Team, Membership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    search_fields = ['name', 'owner__email']
    list_filter = ['created_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_by', 'created_at']
    search_fields = ['name', 'organization__name']
    list_filter = ['organization', 'created_at']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'team', 'role', 'joined_at']
    search_fields = ['user__email', 'organization__name']
    list_filter = ['role', 'organization', 'joined_at']