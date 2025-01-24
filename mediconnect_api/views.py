from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from knox.models import AuthToken
from django.utils import timezone
from datetime import timedelta
from .models import User, UserProfile, DoctorProfile, Hospital, Appointment, Subscription, Token, PaymentHistory
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    DoctorProfileSerializer, 
    HospitalSerializer,
    AppointmentSerializer,
    SubscriptionSerializer,
    TokenSerializer
)

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        _, token = AuthToken.objects.create(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(email=email, password=password)
    if user:
        _, token = AuthToken.objects.create(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

# Profile Management Views
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def doctor_profile(request):
    try:
        profile = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = DoctorProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Hospital Management Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_list(request):
    hospitals = Hospital.objects.all()
    serializer = HospitalSerializer(hospitals, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_detail(request, pk):
    try:
        hospital = Hospital.objects.get(pk=pk)
    except Hospital.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    # Check if user has valid subscription or token
    user_profile = UserProfile.objects.get(user=request.user)
    if not user_profile.has_valid_access(hospital):
        return Response(
            {'error': 'No valid subscription or token for this hospital'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = HospitalSerializer(hospital)
    return Response(serializer.data)

# Appointment Management
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_appointment(request):
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        # Check if user has valid access
        hospital = serializer.validated_data['doctor'].hospital
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.has_valid_access(hospital):
            return Response(
                {'error': 'No valid subscription or token for this hospital'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Subscription and Token Management
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_subscription(request):
    amount = request.data.get('amount')
    duration_days = request.data.get('duration_days', 30)
    hospital_count = request.data.get('hospital_count', 5)
    
    # Process payment (implement your payment gateway here)
    # For now, we'll assume payment is successful
    
    subscription = Subscription.objects.create(
        user=request.user,
        amount=amount,
        valid_until=timezone.now() + timedelta(days=duration_days),
        hospital_count=hospital_count
    )
    
    PaymentHistory.objects.create(
        user=request.user,
        amount=amount,
        payment_type='subscription'
    )
    
    return Response({
        'message': 'Subscription purchased successfully',
        'subscription': SubscriptionSerializer(subscription).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_tokens(request):
    amount = request.data.get('amount')
    token_count = request.data.get('token_count', 10)
    
    # Process payment (implement your payment gateway here)
    # For now, we'll assume payment is successful
    
    token = Token.objects.create(
        user=request.user,
        amount=amount,
        token_count=token_count,
        valid_until=timezone.now() + timedelta(days=30)
    )
    
    PaymentHistory.objects.create(
        user=request.user,
        amount=amount,
        payment_type='token'
    )
    
    return Response({
        'message': 'Tokens purchased successfully',
        'token': TokenSerializer(token).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def access_status(request):
    user_profile = UserProfile.objects.get(user=request.user)
    subscription = Subscription.objects.filter(
        user=request.user,
        valid_until__gt=timezone.now()
    ).first()
    
    tokens = Token.objects.filter(
        user=request.user,
        valid_until__gt=timezone.now()
    ).first()
    
    return Response({
        'subscription': SubscriptionSerializer(subscription).data if subscription else None,
        'tokens': TokenSerializer(tokens).data if tokens else None
    })

# Doctor Application and Approval
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_as_doctor(request):
    try:
        # Check if user already has a doctor profile
        DoctorProfile.objects.get(user=request.user)
        return Response(
            {'error': 'Doctor profile already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except DoctorProfile.DoesNotExist:
        serializer = DoctorProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, is_approved=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_doctor(request, doctor_id):
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff members can approve doctors'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        doctor_profile = DoctorProfile.objects.get(id=doctor_id)
        doctor_profile.is_approved = True
        doctor_profile.save()
        return Response({'message': 'Doctor approved successfully'})
    except DoctorProfile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
