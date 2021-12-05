from django import forms

from .models import Evaluation
from datasources.models import BedFileEntry

class EvaluationForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Evaluation
        fields = ('name', 'text', 'assembly')

    def save(self, commit=True):
        return super(EvalForm, self).save(commit=commit)

class EvaluationAddEntryForm(forms.ModelForm):

    class Meta:
        model = BedFileEntry
        fields = ('name', 'chrom', 'start', 'end')

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("start")
        end = cleaned_data.get("end")

        if start > end:
            raise forms.ValidationError("The start coordinate should be less or equal to the end coordinate.")

        distance_limit =  10 * 1000 * 1000

        if end - start >  distance_limit:
            raise forms.ValidationError(
                "Distance from the start to the end coordinate must be less or equal to {:,}.".format(distance_limit)
            )