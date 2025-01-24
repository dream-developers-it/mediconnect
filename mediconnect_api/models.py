from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    is_doctor = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def has_valid_access(self, hospital):
        # Check for valid subscription
        subscription = self.user.subscriptions.filter(
            valid_until__gt=timezone.now()
        ).first()
        if subscription and subscription.hospital_count > 0:
            return True
            
        # Check for valid tokens
        tokens = self.user.tokens.filter(
            valid_until__gt=timezone.now(),
            token_count__gt=0
        ).first()
        return tokens is not None

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField(default='')
    image = models.ImageField(upload_to='hospital_images/', null=True, blank=True)
    contact_number = models.CharField(max_length=20, default='N/A')
    email = models.EmailField(default='hospital@example.com')
    website = models.URLField(blank=True)
    mapurl = models.URLField(blank=True, help_text='Google Maps embed URL')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    medical_license = models.FileField(upload_to='medical_licenses/', null=True, blank=True)
    hospitals = models.ManyToManyField(Hospital, related_name='doctors')
    is_approved = models.BooleanField(default=False)
    available_from = models.TimeField(default='09:00')
    available_to = models.TimeField(default='17:00')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

class Appointment(models.Model):
    APPOINTMENT_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField(default='09:00')  
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-created_at']

    def __str__(self):
        return f"{self.user.email} - Dr. {self.doctor.user.get_full_name()} - {self.appointment_date}"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    hospital_count = models.IntegerField(default=5)
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    token_count = models.IntegerField(default=10)
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PaymentHistory(models.Model):
    PAYMENT_METHODS = [
        ('bkash', 'bKash'),
        ('card', 'Credit/Debit Card'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    token_count = models.IntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.email}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        if instance.is_doctor:
            DoctorProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.user_profile.save()
    if instance.is_doctor and hasattr(instance, 'doctor_profile'):
        instance.doctor_profile.save()

@receiver(post_delete, sender=User)
def delete_user_profiles(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'user_profile'):
            instance.user_profile.delete()
        if hasattr(instance, 'doctor_profile'):
            instance.doctor_profile.delete()
    except:
        pass

@receiver(post_save, sender=PaymentHistory)
def update_user_tokens(sender, instance, **kwargs):
    if instance.status == 'completed':
        # Create or update user's token
        token, created = Token.objects.get_or_create(
            user=instance.user,
            defaults={
                'token_count': instance.token_count,
                'amount': instance.amount,
                'valid_until': timezone.now() + timezone.timedelta(days=30)
            }
        )
        
        if not created:
            # Add tokens to existing count and extend validity
            token.token_count += instance.token_count
            token.valid_until = timezone.now() + timezone.timedelta(days=30)
            token.save()
