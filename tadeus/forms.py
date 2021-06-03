from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from tadeus.models import Track, Plot, TrackFile, Eval, Assembly, BedFileEntry, Subtrack

class TrackForm(forms.ModelForm):

    class Meta:
        model = Track
        fields = ('height', 'colormap', 'min_value', 'max_value', 'subtracks'  ) # 'display', 'labels', 'inverted', 'x_labels', 'name_filter',
                  #'no', 'transform', 'color', 'edgecolor', 'title', 'bedgraph_style', 'bed_display', 'domains_file',
                  #'chromosome', 'start_coordinate', 'end_coordinate',  'subtracks', 'bedgraph_display', 'bin_size')

    def __init__(self, *args, **kwargs):
        
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        
        self.fields["subtracks"].widget = CheckboxSelectMultiple()
        self.fields["subtracks"].queryset = Subtrack.objects.filter(track_file = self.instance.track_file)

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