from django import forms
from .models import ObjetDefectueux
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ObjetDefectueuxForm(forms.ModelForm):
    class Meta:
        model = ObjetDefectueux
        fields = ['name', 'inspection_date', 'status', 'description']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']