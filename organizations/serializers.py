from rest_framework import serializers
from .models import Organization, Team, Membership
from users.serializers import UserSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'description', 'owner', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team"""
    created_by = UserSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'organization', 'organization_name', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer for Membership"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Membership
        fields = ['id', 'user', 'user_id', 'organization', 'organization_name', 'team', 'team_name', 'role', 'joined_at']
        read_only_fields = ['id', 'user', 'joined_at']