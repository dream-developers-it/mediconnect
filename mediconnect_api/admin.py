from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, UserProfile, DoctorProfile, Hospital,
    Appointment, Subscription, Token, PaymentHistory
)

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_doctor', 'is_staff')
    list_filter = ('is_doctor', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_doctor', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_doctor'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__email', 'phone_number')

class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'is_approved')
    list_filter = ('specialization', 'is_approved')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'specialization')

class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('user__email', 'doctor__user__email')

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'hospital_count', 'valid_until')
    list_filter = ('valid_until',)
    search_fields = ('user__email',)

class TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'token_count', 'valid_until')
    list_filter = ('valid_until',)
    search_fields = ('user__email',)

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__email', 'payment_id', 'transaction_id']
    readonly_fields = ['payment_id', 'created_at', 'completed_at']

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(DoctorProfile, DoctorProfileAdmin)
admin.site.register(Hospital, HospitalAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Token, TokenAdmin)
