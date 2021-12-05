from django import forms
from .models  import Plot
from django.shortcuts import redirect

class PlotForm(forms.ModelForm):

     class Meta:
        model = Plot
        fields = ('title', 'name', 'assembly')
