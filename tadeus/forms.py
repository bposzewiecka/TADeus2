from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from tadeus.models import Track, Plot, TrackFile, Eval, Assembly, BedFileEntry, Subtrack

class TrackForm(forms.ModelForm):

    class Meta:
        model = Track
        exclude = ['plot' , 'track_file']

    def __init__(self, *args, **kwargs):
        
        super(forms.ModelForm, self).__init__(*args, **kwargs)

        instance_attributes = self.instance.track_file.get_attributes()
        all_fields_attributes = list(self.fields.keys())

        print(instance_attributes)

        for attribute in all_fields_attributes:
            if attribute not in instance_attributes:
                self.fields.pop(attribute)

        if 'subtracks' in self.fields and len(self.instance.subtracks.all()) <= 1: 
            self.fields.pop('subtracks')

        if 'subtracks' in self.fields:
            self.fields['subtracks'].widget = CheckboxSelectMultiple()
            self.fields['subtracks'].queryset = Subtrack.objects.filter(track_file = self.instance.track_file)

class CreateTrackForm(forms.ModelForm):

     class Meta:
        model = Track
        fields = ('no',  'title', 'height', 'track_file', 'hic_display')


class PlotForm(forms.ModelForm):

     class Meta:
        model = Plot
        fields = ('title', 'name', 'assembly')


class TrackFileForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = TrackFile
        fields = ('assembly', 'name', 'text')

    def save(self, commit=True):
        return super(TrackFileForm, self).save(commit=commit)


class EvalForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Eval
        fields = ('name', 'text', 'assembly')

    def save(self, commit=True):
        return super(EvalForm, self).save(commit=commit)

class EvalAddEntryForm(forms.ModelForm):
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