from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Organization, Team, Membership
from .serializers import OrganizationSerializer, TeamSerializer, MembershipSerializer
from .permissions import IsOrganizationAdmin, IsOrganizationManagerOrAdmin, IsOrganizationMember


class OrganizationViewSet(viewsets.ModelViewSet):
    """CRUD for Organizations - Only ADMINs can create"""
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrganizationAdmin]
    
    def get_queryset(self):
        # Users see only organizations they belong to
        if self.request.user.is_superuser:
            return Organization.objects.all()
        
        return Organization.objects.filter(
            memberships__user=self.request.user
        ).distinct()
    
    def perform_create(self, serializer):
        # Set owner and auto-create membership
        org = serializer.save(owner=self.request.user)
        Membership.objects.create(
            user=self.request.user,
            organization=org,
            role='ADMIN'
        )


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD for Teams - ADMINs and MANAGERs can create"""
    serializer_class = TeamSerializer
    permission_classes = [IsOrganizationManagerOrAdmin]
    
    def get_queryset(self):
        # Users see teams from their organizations
        if self.request.user.is_superuser:
            return Team.objects.all()
        
        user_orgs = Membership.objects.filter(
            user=self.request.user
        ).values_list('organization', flat=True)
        
        return Team.objects.filter(organization__in=user_orgs)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MembershipViewSet(viewsets.ModelViewSet):
    """Manage organization memberships - ADMIN only"""
    serializer_class = MembershipSerializer
    permission_classes = [IsOrganizationAdmin]
    
    def get_queryset(self):
        # Show memberships from user's organizations
        if self.request.user.is_superuser:
            return Membership.objects.all()
        
        admin_orgs = Membership.objects.filter(
            user=self.request.user,
            role='ADMIN'
        ).values_list('organization', flat=True)
        
        return Membership.objects.filter(organization__in=admin_orgs)
    
    def create(self, request, *args, **kwargs):
        # Add user to organization
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if membership already exists
        existing = Membership.objects.filter(
            user_id=serializer.validated_data['user_id'],
            organization=serializer.validated_data['organization']
        ).first()
        
        if existing:
            return Response(
                {'error': 'User already member of this organization'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)