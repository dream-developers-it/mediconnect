from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, DoctorProfile, Hospital, Appointment, Subscription, Token, HospitalRating, DoctorRating, DoctorUnlock

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name', 'is_doctor')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'email', 'full_name', 'profile_picture', 'phone_number', 'address')

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ('id', 'name', 'location', 'map_url', 'created_at', 'updated_at')

class DoctorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    hospitals = HospitalSerializer(many=True, read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = ('id', 'email', 'full_name', 'hospitals', 'specialization', 
                 'medical_documents', 'appointment_number', 'is_approved',
                 'created_at', 'updated_at')
        read_only_fields = ('is_approved',)

class AppointmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ('id', 'user', 'user_name', 'doctor', 'doctor_name', 
                 'appointment_date', 'status', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('user', 'status')

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'amount', 'hospital_count', 'valid_until', 'created_at')
        read_only_fields = ('created_at',)

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ('id', 'amount', 'token_count', 'valid_until', 'created_at')
        read_only_fields = ('created_at',)

class HospitalRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = HospitalRating
        fields = ('id', 'user', 'user_name', 'hospital', 'rating', 'comment', 'created_at')
        read_only_fields = ('user',)

class DoctorRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = DoctorRating
        fields = ('id', 'user', 'user_name', 'doctor', 'rating', 'comment', 'created_at')
        read_only_fields = ('user',)

class DoctorUnlockSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    
    class Meta:
        model = DoctorUnlock
        fields = ('id', 'user', 'doctor', 'doctor_name', 'hospital', 'hospital_name', 
                 'unlocked_at', 'valid_until', 'is_active')
        read_only_fields = ('user', 'unlocked_at', 'valid_until', 'is_active')
