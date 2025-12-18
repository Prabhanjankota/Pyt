from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """API endpoint for user registration"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]  # Anyone can register
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