from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from core.throttling import LoginRateThrottle
from .serializers import UserRegistrationSerializer, UserSerializer
from django.core.cache import cache

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """API endpoint for user registration"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveAPIView):
    """API endpoint to get current user profile"""
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add caching"""
        cache_key = f'user_profile_{request.user.id}'
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # If not cached, get data normally
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache for 15 minutes
        cache.set(cache_key, serializer.data, 900)
        
        return Response(serializer.data)


# Custom login view with rate limiting
class CustomLoginView(TokenObtainPairView):
    """Custom login view with rate limiting"""
    throttle_classes = [LoginRateThrottle]