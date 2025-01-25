from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from knox.models import AuthToken
from django.utils import timezone
from datetime import timedelta
from .models import User, UserProfile, DoctorProfile, Hospital, Appointment, Subscription, Token, PaymentHistory, HospitalRating, DoctorRating, DoctorUnlock, Notification
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    DoctorProfileSerializer, 
    HospitalSerializer,
    AppointmentSerializer,
    SubscriptionSerializer,
    TokenSerializer,
    HospitalRatingSerializer,
    DoctorRatingSerializer,
    DoctorUnlockSerializer,
    NotificationSerializer
)

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user.is_doctor:
            DoctorProfile.objects.filter(user=user).update(is_approved=False)
        
        # Update phone number
        if 'phone_number' in request.data:
            UserProfile.objects.filter(user=user).update(phone_number=request.data['phone_number'])
            
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
        if user.is_doctor and not hasattr(user, 'doctor_profile'):
            DoctorProfile.objects.create(user=user, is_approved=False)
            
        if user.is_doctor and not user.doctor_profile.is_approved:
            return Response({
                'error': 'Your doctor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        _, token = AuthToken.objects.create(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token,
            'is_doctor': user.is_doctor,
            'is_approved': user.doctor_profile.is_approved if user.is_doctor else None
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

# Rating and Unlock Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_hospital(request, hospital_id):
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not 1 <= rating <= 5:
            return Response({'error': 'Rating must be between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)
            
        rating_obj, created = HospitalRating.objects.update_or_create(
            user=request.user,
            hospital=hospital,
            defaults={'rating': rating, 'comment': comment}
        )
        return Response({'message': 'Rating submitted successfully'}, status=status.HTTP_201_CREATED)
    except Hospital.DoesNotExist:
        return Response({'error': 'Hospital not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_doctor(request, doctor_id):
    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
        
        # Check if this is a reply to another rating
        parent_id = request.data.get('parent_id')
        parent_rating = None
        if parent_id:
            parent_rating = DoctorRating.objects.get(id=parent_id)
            # Only doctor can reply to ratings
            if request.user != doctor.user:
                return Response({'error': 'Only the doctor can reply to ratings'}, 
                              status=status.HTTP_403_FORBIDDEN)
        else:
            # Check if user has already rated this doctor (only for new ratings, not replies)
            if DoctorRating.objects.filter(user=request.user, doctor=doctor, parent=None).exists():
                return Response({'error': 'You have already rated this doctor'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        rating = DoctorRating.objects.create(
            user=request.user,
            doctor=doctor,
            rating=request.data.get('rating', 0) if not parent_id else 0,  # Only parent ratings have rating value
            comment=request.data.get('comment', ''),
            parent=parent_rating
        )
        
        if parent_id:
            # Create notification for reply
            Notification.objects.create(
                recipient=parent_rating.user,
                sender=request.user,
                notification_type='reply',
                rating=rating,
                message=f"{request.user.get_full_name()} replied to your rating"
            )
        else:
            # Create notification for new rating
            Notification.objects.create(
                recipient=doctor.user,
                sender=request.user,
                notification_type='rating',
                rating=rating,
                message=f"{request.user.get_full_name()} left you a new rating"
            )
        
        serializer = DoctorRatingSerializer(rating)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except DoctorProfile.DoesNotExist:
        return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
    except DoctorRating.DoesNotExist:
        return Response({'error': 'Parent rating not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlock_doctor(request, doctor_id, hospital_id):
    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
        hospital = Hospital.objects.get(id=hospital_id)
        
        # Check if user has enough tokens
        user_tokens = Token.objects.filter(user=request.user, valid_until__gt=timezone.now()).first()
        if not user_tokens or user_tokens.token_count < 1:
            return Response({'error': 'Insufficient tokens'}, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Create or update unlock
        unlock, created = DoctorUnlock.objects.get_or_create(
            user=request.user,
            doctor=doctor,
            hospital=hospital,
            defaults={'is_active': True}
        )
        
        if not created:
            # If already unlocked, extend the validity
            unlock.valid_until = timezone.now() + timedelta(days=30)
            unlock.is_active = True
            unlock.save()
        
        # Deduct token
        user_tokens.token_count -= 1
        user_tokens.save()
        
        return Response({
            'message': 'Doctor unlocked successfully',
            'valid_until': unlock.valid_until
        }, status=status.HTTP_201_CREATED)
        
    except (DoctorProfile.DoesNotExist, Hospital.DoesNotExist):
        return Response({'error': 'Doctor or Hospital not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_doctors(request, hospital_id):
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        doctors = DoctorProfile.objects.filter(hospitals=hospital, is_approved=True)
        
        # Get user's unlocked doctors
        unlocked_doctors = DoctorUnlock.objects.filter(
            user=request.user,
            hospital=hospital,
            valid_until__gt=timezone.now(),
            is_active=True
        ).values_list('doctor_id', flat=True)
        
        # Get one free doctor if no unlocked doctors
        free_doctor = None
        if not unlocked_doctors:
            free_doctor = doctors.first()
            if free_doctor:
                unlocked_doctors = [free_doctor.id]
        
        # Prepare response
        doctor_list = []
        for doctor in doctors:
            doctor_data = DoctorProfileSerializer(doctor).data
            doctor_data['is_unlocked'] = doctor.id in unlocked_doctors
            doctor_list.append(doctor_data)
        
        return Response({
            'doctors': doctor_list,
            'unlocked_count': len(unlocked_doctors)
        })
        
    except Hospital.DoesNotExist:
        return Response({'error': 'Hospital not found'}, status=status.HTTP_404_NOT_FOUND)
