from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    User, UserProfile, DoctorProfile, Hospital, DoctorService,
    Appointment, Token, Subscription, PaymentHistory,
    HospitalRating, DoctorRating, DoctorUnlock
)

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'display_profile_picture')
    search_fields = ('user__email', 'phone_number')
    
    def display_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return "No picture"
    display_profile_picture.short_description = 'Profile Picture'

@admin.register(DoctorService)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'experience_years', 'is_approved')
    list_filter = ('specialization', 'is_approved', 'hospitals')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    filter_horizontal = ('services', 'hospitals')
    list_editable = ('is_approved',)
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        queryset.update(is_approved=True)
    approve_doctors.short_description = "Approve selected doctors"

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'division', 'city', 'phone', 'email')
    list_filter = ('division', 'city')
    search_fields = ('name', 'division', 'city', 'address')
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No image"
    display_image.short_description = 'Hospital Image'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('user__email', 'doctor__user__email')
    date_hierarchy = 'appointment_date'

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_count', 'valid_until')
    list_filter = ('valid_until',)
    search_fields = ('user__email',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'hospital_count', 'valid_until')
    list_filter = ('valid_until',)
    search_fields = ('user__email',)

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('user__email', 'transaction_id')
    date_hierarchy = 'created_at'

@admin.register(HospitalRating)
class HospitalRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'hospital', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'hospital__name')
    date_hierarchy = 'created_at'

@admin.register(DoctorRating)
class DoctorRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'doctor__user__email')
    date_hierarchy = 'created_at'

@admin.register(DoctorUnlock)
class DoctorUnlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'valid_until')
    list_filter = ('valid_until',)
    search_fields = ('user__email', 'doctor__user__email')
