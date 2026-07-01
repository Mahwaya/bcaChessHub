from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from associations.models import Association
from .models import Member


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    association = forms.ModelChoiceField(
        queryset=Association.objects.filter(is_active=True),
        empty_label='— Select your association —',
    )
    phone = forms.CharField(max_length=20, required=False,
                            widget=forms.TextInput(attrs={'placeholder': '+263 77 123 4567'}))
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Member.objects.create(
                user=user,
                association=self.cleaned_data['association'],
                phone=self.cleaned_data.get('phone', ''),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                role='player',
            )
        return user
