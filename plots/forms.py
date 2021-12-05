from django import forms

from .models import Plot


class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ("title", "name", "assembly")
