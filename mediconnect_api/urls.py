from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    
    # Profile Management URLs
    path('profile/user/', views.user_profile, name='user-profile'),
    path('profile/doctor/', views.doctor_profile, name='doctor-profile'),
    
    # Hospital Management URLs
    path('hospitals/', views.hospital_list, name='hospital-list'),
    path('hospitals/<int:pk>/', views.hospital_detail, name='hospital-detail'),
    
    # Appointment URLs
    path('appointments/request/', views.request_appointment, name='request-appointment'),
    
    # Subscription and Token URLs
    path('subscription/purchase/', views.purchase_subscription, name='purchase-subscription'),
    path('tokens/purchase/', views.purchase_tokens, name='purchase-tokens'),
    path('access/status/', views.access_status, name='access-status'),
    
    # Doctor Application URLs
    path('apply-doctor/', views.apply_as_doctor, name='apply-doctor'),
    path('approve-doctor/<int:doctor_id>/', views.approve_doctor, name='approve-doctor'),
    
    # Rating URLs
    path('hospitals/<int:hospital_id>/rate/', views.rate_hospital, name='rate-hospital'),
    path('doctors/<int:doctor_id>/rate/', views.rate_doctor, name='rate-doctor'),
    
    # Doctor Unlock URLs
    path('doctors/<int:doctor_id>/hospitals/<int:hospital_id>/unlock/', views.unlock_doctor, name='unlock-doctor'),
    path('hospitals/<int:hospital_id>/doctors/', views.hospital_doctors, name='hospital-doctors'),
]
