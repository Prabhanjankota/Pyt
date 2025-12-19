from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, TeamViewSet, MembershipViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet, basename='organization')
router.register('teams', TeamViewSet, basename='team')
router.register('memberships', MembershipViewSet, basename='membership')

urlpatterns = [
    path('', include(router.urls)),
]