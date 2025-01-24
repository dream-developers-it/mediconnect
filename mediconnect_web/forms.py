from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from mediconnect_api.models import User, UserProfile, DoctorProfile, Appointment

User = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegistrationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        (False, 'Patient'),
        (True, 'Doctor'),
    ]
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    is_doctor = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False,
        label='Register as'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_doctor', 'password1', 'password2')

    def clean_is_doctor(self):
        return self.cleaned_data['is_doctor'] == 'True'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_doctor = self.cleaned_data['is_doctor']
        if commit:
            user.save()
            if user.is_doctor:
                DoctorProfile.objects.create(user=user)
        return user

class UserProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address',
            'rows': 3
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'style': 'display: none;',
            'id': 'profile_picture_input'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address']

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'medical_license', 'hospitals', 'available_from', 'available_to', 'consultation_fee']
        widgets = {
            'available_from': forms.TimeInput(attrs={'type': 'time'}),
            'available_to': forms.TimeInput(attrs={'type': 'time'}),
            'consultation_fee': forms.NumberInput(attrs={'min': '0', 'step': '0.01'})
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

class TokenPurchaseForm(forms.Form):
    TOKEN_CHOICES = [
        (10, '10 Tokens - 10 BDT'),
        (20, '20 Tokens - 20 BDT'),
    ]
    
    token_count = forms.ChoiceField(
        choices=TOKEN_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Select Token Package'
    )
    
    def clean_token_count(self):
        token_count = int(self.cleaned_data['token_count'])
        # Calculate amount based on token count (1 token = 1 BDT)
        self.cleaned_data['amount'] = token_count
        return token_count
