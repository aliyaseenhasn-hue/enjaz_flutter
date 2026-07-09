
from django import forms
from .models import PortfolioImage

class PortfolioImageForm(forms.ModelForm):
    class Meta:
        model = PortfolioImage
        fields = ['image', 'caption']