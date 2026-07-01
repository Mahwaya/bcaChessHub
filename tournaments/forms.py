from django import forms
from .models import Tournament


class TournamentForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Tournament
        fields = [
            'name', 'format', 'status',
            'start_date', 'end_date', 'location',
            'num_rounds', 'max_players',
            'registration_fee', 'currency',
            'description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'currency': forms.TextInput(attrs={'placeholder': 'USD'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Bulawayo City Hall'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('End date cannot be before start date.')
        return cleaned
