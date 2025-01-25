from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from mediconnect_api.models import User, UserProfile, DoctorProfile, Hospital, Appointment, Subscription, Token, PaymentHistory, DIVISION_CHOICES
from .forms import UserRegistrationForm, UserProfileForm, DoctorProfileForm, AppointmentForm, ContactForm, TokenPurchaseForm, CustomAuthenticationForm
from django.utils import timezone
import uuid
import requests
from django.http import JsonResponse
from django.db import transaction

# Create your views here.

def home(request):
    hospitals = Hospital.objects.all()[:6]  # Get 6 featured hospitals
    doctors = DoctorProfile.objects.filter(is_approved=True)[:6]  # Get 6 featured doctors
    return render(request, 'mediconnect_web/home.html', {
        'hospitals': hospitals,
        'doctors': doctors,
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Start transaction
                with transaction.atomic():
                    # Create user
                    user = form.save(commit=False)
                    user.is_doctor = form.cleaned_data.get('is_doctor', False)
                    user.save()

                    # Create UserProfile
                    user_profile = UserProfile.objects.create(
                        user=user,
                        phone_number=form.cleaned_data.get('phone_number', '')
                    )
                    
                    # If registering as doctor, create DoctorProfile
                    if user.is_doctor:
                        doctor_profile = DoctorProfile.objects.create(
                            user=user,
                            is_approved=False,
                            gender=request.POST.get('gender', 'M'),
                            specialization=request.POST.get('specialization', 'general'),
                            medical_license=request.FILES.get('medical_license'),
                            available_from='09:00',
                            available_to='17:00',
                            consultation_fee=0.00
                        )
                        messages.info(request, 'Your doctor account has been created and is pending approval. Our admin team will review your application. You will be notified once approved.')
                        return redirect('login')
                    
                    # Only login if not a doctor
                    login(request, user)
                    messages.success(request, 'Registration successful! Please complete your profile.')
                    return redirect('profile')
                    
            except Exception as e:
                messages.error(request, f'Registration failed. Please try again. Error: {str(e)}')
                return redirect('register')
    else:
        form = UserRegistrationForm()
    return render(request, 'mediconnect_web/register.html', {'form': form})

@login_required
def profile(request):
    # Get or create user profile
    try:
        user_profile = request.user.user_profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
    }
    
    # If user is a doctor, get or create doctor profile
    if hasattr(request.user, 'groups'):
        if request.user.groups.filter(name='Doctors').exists():
            try:
                doctor_profile = request.user.doctor_profile
            except DoctorProfile.DoesNotExist:
                doctor_profile = DoctorProfile.objects.create(user=request.user)
            
            if request.method == 'POST':
                doctor_form = DoctorProfileForm(request.POST, request.FILES, instance=doctor_profile)
                if doctor_form.is_valid():
                    doctor_form.save()
                    messages.success(request, 'Your doctor profile has been updated successfully!')
                    return redirect('profile')
            else:
                doctor_form = DoctorProfileForm(instance=doctor_profile)
            
            context['doctor_form'] = doctor_form
            context['is_doctor'] = True
    
    # Get appointments
    if request.user.is_doctor:
        doctor_appointments = Appointment.objects.filter(doctor__user=request.user).order_by('-appointment_date')[:5]
        user_appointments = None
    else:
        doctor_appointments = None
        user_appointments = Appointment.objects.filter(user=request.user).order_by('-appointment_date')[:5]
    
    context['appointments'] = user_appointments
    context['doctor_appointments'] = doctor_appointments
    context['payments'] = PaymentHistory.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'mediconnect_web/profile.html', context)

class HospitalListView(ListView):
    model = Hospital
    template_name = 'mediconnect_web/hospital_list.html'
    context_object_name = 'hospitals'
    paginate_by = 9

    def get_queryset(self):
        queryset = Hospital.objects.all()
        
        # Filter by name
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # Filter by division
        division = self.request.GET.get('division')
        if division:
            queryset = queryset.filter(division=division)
        
        # Filter by city
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['divisions'] = DIVISION_CHOICES
        return context

class HospitalDetailView(DetailView):
    model = Hospital
    template_name = 'mediconnect_web/hospital_detail.html'
    context_object_name = 'hospital'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = self.object.doctors.filter(is_approved=True)
        return context

@method_decorator(login_required, name='dispatch')
class AppointmentCreateView(CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'mediconnect_web/appointment_form.html'
    success_url = reverse_lazy('appointment_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@login_required
def appointment_list(request):
    if hasattr(request.user, 'doctor_profile'):
        appointments = Appointment.objects.filter(doctor=request.user.doctor_profile)
    else:
        appointments = Appointment.objects.filter(user=request.user)
    return render(request, 'mediconnect_web/appointment_list.html', {
        'appointments': appointments
    })

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.user != appointment.user and request.user != appointment.doctor.user:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('appointment_list')
    return render(request, 'mediconnect_web/appointment_detail.html', {
        'appointment': appointment
    })

@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    if appointment.status != 'cancelled':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    return redirect('appointment_list')

@login_required
def subscription_purchase(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        duration = int(request.POST.get('duration', 30))
        hospital_count = int(request.POST.get('hospital_count', 5))
        
        # Process payment here (implement payment gateway)
        # For now, we'll create the subscription directly
        Subscription.objects.create(
            user=request.user,
            amount=amount,
            hospital_count=hospital_count,
            valid_until=timezone.now() + timezone.timedelta(days=duration)
        )
        messages.success(request, 'Subscription purchased successfully!')
        return redirect('profile')
    
    return render(request, 'mediconnect_web/subscription_purchase.html')

@login_required
def token_purchase(request):
    # Get user's current tokens
    current_tokens = Token.objects.filter(
        user=request.user,
        valid_until__gt=timezone.now()
    ).first()

    if request.method == 'POST':
        amount = request.POST.get('amount')
        token_count = request.POST.get('token_count')
        
        # Validate the amount and token count
        valid_packages = {
            '500': 10,
            '1000': 25,
            '2000': 60
        }
        
        if amount not in valid_packages or int(token_count) != valid_packages[amount]:
            messages.error(request, 'Invalid package selected.')
            return redirect('token_purchase')
        
        # Generate unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Save payment attempt
        payment = PaymentHistory.objects.create(
            user=request.user,
            amount=amount,
            payment_id=payment_id,
            payment_method='bkash',
            status='pending',
            token_count=token_count
        )
        
        # Store payment info in session
        request.session['payment_id'] = payment_id
        request.session['token_count'] = token_count
        
        return render(request, 'mediconnect_web/bkash_payment.html', {
            'payment_id': payment_id,
            'amount': amount,
            'token_count': token_count,
            'current_tokens': current_tokens,
            'merchant_number': settings.BKASH_MERCHANT_NUMBER
        })
    
    return render(request, 'mediconnect_web/token_purchase.html', {
        'current_tokens': current_tokens
    })

@login_required
def check_payment_status(request, payment_id):
    try:
        # Get the payment record and ensure it belongs to the current user
        payment = get_object_or_404(PaymentHistory, payment_id=payment_id, user=request.user)
        
        # Here you would typically check with bKash API
        # For demo, we'll simulate a successful payment
        if payment.status == 'pending':
            try:
                # Update payment status
                payment.status = 'completed'
                payment.save()
                
                # Create or update user's tokens
                token, created = Token.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'token_count': 0,
                        'valid_until': timezone.now() + timezone.timedelta(days=365)
                    }
                )
                
                # Add new tokens
                token.token_count = token.token_count + int(payment.token_count)
                token.save()
                
                return JsonResponse({
                    'status': 'completed',
                    'message': 'Payment successful! Tokens have been added to your account.',
                    'redirect_url': reverse('profile')
                })
                
            except Exception as e:
                # If something goes wrong, revert payment status
                payment.status = 'pending'
                payment.save()
                raise e
                
        elif payment.status == 'completed':
            return JsonResponse({
                'status': 'completed',
                'message': 'Payment has already been processed.',
                'redirect_url': reverse('profile')
            })
        else:
            return JsonResponse({
                'status': 'pending',
                'message': 'Payment is still being processed.'
            })
            
    except PaymentHistory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid payment ID'
        }, status=400)
    except Exception as e:
        # Log the error for debugging
        print(f"Payment status check error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while checking payment status. Please try again.'
        }, status=500)

@require_POST
def bkash_callback(request):
    payment_id = request.POST.get('payment_id')
    transaction_id = request.POST.get('transaction_id')
    status = request.POST.get('status')

    try:
        payment = PaymentHistory.objects.get(payment_id=payment_id)
        if status == 'completed':
            payment.status = 'completed'
            payment.transaction_id = transaction_id
            payment.completed_at = timezone.now()
            payment.save()

            # Create or update user's token
            token, created = Token.objects.get_or_create(
                user=payment.user,
                defaults={
                    'token_count': payment.token_count,
                    'amount': payment.amount,
                    'valid_until': timezone.now() + timezone.timedelta(days=30)
                }
            )
            
            if not created:
                # Add tokens to existing count and extend validity
                token.token_count += payment.token_count
                token.valid_until = timezone.now() + timezone.timedelta(days=30)
                token.save()

            messages.success(request, f'Payment successful! {payment.token_count} tokens have been added to your account.')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Payment failed. Please try again.')

    except PaymentHistory.DoesNotExist:
        messages.error(request, 'Invalid payment information.')
    
    return redirect('profile')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check if user is a doctor and not approved
            if user.is_doctor and hasattr(user, 'doctor_profile') and not user.doctor_profile.is_approved:
                messages.warning(request, 'Your doctor account is pending approval. Please wait for admin approval.')
                return redirect('login')
            
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('profile')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'mediconnect_web/login.html', {'form': form})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            send_mail(
                subject=f"Contact Form: {form.cleaned_data['subject']}",
                message=f"From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n{form.cleaned_data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            messages.success(request, 'Your message has been sent!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'mediconnect_web/contact.html', {'form': form})

def search_doctors(request):
    doctors = DoctorProfile.objects.all()
    
    # Filter by specialization
    specialization = request.GET.get('specialization')
    if specialization:
        doctors = doctors.filter(specialization=specialization)
    
    # Filter by hospital
    hospital_id = request.GET.get('hospital')
    if hospital_id:
        doctors = doctors.filter(hospitals__id=hospital_id)
    
    # Get unique specializations for filter dropdown
    specializations = DoctorProfile.SPECIALIZATION_CHOICES
    
    # Get hospitals for filter dropdown
    hospitals = Hospital.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(doctors, 9)  # Show 9 doctors per page
    page = request.GET.get('page')
    doctors = paginator.get_page(page)
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'hospitals': hospitals,
        'current_specialization': specialization,
        'current_hospital': hospital_id,
    }
    return render(request, 'mediconnect_web/doctor_search.html', context)

def custom_logout(request):
    """Custom logout view."""
    logout(request)
    return redirect('login')  # 

@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(DoctorProfile, pk=pk)
    context = {
        'doctor': doctor,
        'profile_picture': doctor.user.user_profile.profile_picture if hasattr(doctor.user, 'user_profile') else None,
    }
    return render(request, 'mediconnect_web/doctor_detail.html', context)