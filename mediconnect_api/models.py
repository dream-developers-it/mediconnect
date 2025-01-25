from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta

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
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='images/bkash-logo.png', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s profile"

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

class DoctorService(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class DoctorProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    SPECIALIZATION_CHOICES = (
        ('general', 'General Physician'),
        ('cardiologist', 'Cardiologist'),
        ('dermatologist', 'Dermatologist'),
        ('neurologist', 'Neurologist'),
        ('orthopedic', 'Orthopedic'),
        ('pediatrician', 'Pediatrician'),
        ('psychiatrist', 'Psychiatrist'),
        ('surgeon', 'Surgeon'),
        ('urologist', 'Urologist'),
        ('ophthalmologist', 'Ophthalmologist'),
        ('dentist', 'Dentist'),
        ('ent', 'ENT Specialist'),
        ('gynecologist', 'Gynecologist'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, default='general')
    experience_years = models.PositiveIntegerField(default=0, help_text="Total years of experience")
    services = models.ManyToManyField(DoctorService, related_name='doctors', blank=True)
    medical_license = models.FileField(upload_to='medical_licenses/', null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bio = models.TextField(blank=True)
    hospitals = models.ManyToManyField('Hospital', related_name='doctors')
    is_approved = models.BooleanField(default=False)
    available_from = models.TimeField(default='09:00')
    available_to = models.TimeField(default='17:00')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    @property
    def full_name(self):
        return f"Dr. {self.user.get_full_name()}"

    @property
    def experience_text(self):
        years = self.experience_years
        if years == 0:
            return "New Doctor"
        elif years == 1:
            return "1 Year Experience"
        else:
            return f"{years} Years Experience"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set created_at for new instances
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

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

class Rating(models.Model):
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class HospitalRating(Rating):
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE, related_name='ratings')

    class Meta:
        unique_together = ('user', 'hospital')

class DoctorRating(Rating):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='ratings')

    class Meta:
        unique_together = ('user', 'doctor')

class DoctorUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_doctors')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='unlocked_by')
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.valid_until:
            self.valid_until = self.unlocked_at + timedelta(days=30)
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'doctor', 'hospital')

    def __str__(self):
        return f"{self.user.email} unlocked {self.doctor} at {self.hospital.name}"

# Division choices
DIVISION_CHOICES = [
    ('DHA', 'Dhaka'),
    ('CTG', 'Chittagong'),
    ('SYL', 'Sylhet'),
    ('RAJ', 'Rajshahi'),
    ('KHU', 'Khulna'),
    ('BAR', 'Barisal'),
    ('RAN', 'Rangpur'),
    ('MYM', 'Mymensingh'),
]

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    division = models.CharField(max_length=3, choices=DIVISION_CHOICES, null=True)
    city = models.CharField(max_length=100, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    website = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='hospital_images/', default='images/hospital-default.jpg')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set created_at for new instances
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']

@receiver(post_delete, sender=User)
def delete_user_profiles(sender, instance, **kwargs):
    """Delete associated profiles when User is deleted"""
    try:
        if hasattr(instance, 'user_profile'):
            instance.user_profile.delete()
        if hasattr(instance, 'doctor_profile'):
            instance.doctor_profile.delete()
    except Exception:
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
