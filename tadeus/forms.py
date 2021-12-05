from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from tadeus.models import Track, Plot
  
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



