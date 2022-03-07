from django import forms

from .models import Track


class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        exclude = ["plot"]

    def __init__(self, *args, **kwargs):

        super(forms.ModelForm, self).__init__(*args, **kwargs)

        self.fields.pop("subtracks")

        """
        instance_attributes = self.instance.get_attributes()
        all_fields_attributes = list(self.fields.keys())

        for attribute in all_fields_attributes:
            if attribute not in instance_attributes:
                self.fields.pop(attribute)

        if "subtracks" in self.fields:

            track_file_subtracks = Subtrack.objects.filter(track_file=self.instance.track_file)

            if len(track_file_subtracks) <= 1:
                self.fields.pop("subtracks")
            else:
                self.fields["subtracks"].widget = CheckboxSelectMultiple()
                self.fields["subtracks"].queryset = track_file_subtracks
        """


class CreateTrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ("no", "title", "height", "track_file", "hic_display")
