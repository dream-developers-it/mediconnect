from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

urlpatterns = [
    # Home and basic pages
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('search/doctors/', views.search_doctors, name='search_doctors'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Password Reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='mediconnect_web/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='mediconnect_web/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='mediconnect_web/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='mediconnect_web/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Profile Management
    path('profile/', views.profile, name='profile'),
    path('doctor/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    
    # Hospitals
    path('hospitals/', views.HospitalListView.as_view(), name='hospital_list'),
    path('hospital/<int:pk>/', views.HospitalDetailView.as_view(), name='hospital_detail'),
    
    # Appointments
    path('appointment/new/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointment/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    
    # Tokens and Payments
    path('subscription/purchase/', views.subscription_purchase, name='subscription_purchase'),
    path('token/purchase/', views.token_purchase, name='token_purchase'),
    path('payment/status/<str:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('bkash/callback/', views.bkash_callback, name='bkash_callback'),
]
