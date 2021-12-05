from django import forms
from .models import TrackFile

class TrackFileForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = TrackFile
        fields = ('assembly', 'name', 'text')

    def save(self, commit=True):
        return super(TrackFileForm, self).save(commit=commit)