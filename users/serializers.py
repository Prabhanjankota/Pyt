from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        """Check that passwords match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password2')  # Remove password2, we don't need it
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']