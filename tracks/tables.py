import django_tables2 as tables
from django.urls import reverse

from tadeus_portal.defaults import DEFAULT_EDIT_ICON
from tadeus_portal.utils import getLink

from .models import Track


class TrackTable(tables.Table):

    file_name = tables.Column(empty_values=(), orderable=False)
    track_type = tables.Column(empty_values=(), orderable=False)

    def render_file_name(self, record):
        return record.track_file.name

    def render_track_type(self, record):
        return record.get_long_track_type_name

    def render_id(self, record):
        link = reverse("tracks:update", kwargs={"p_id": record.id})
        return getLink(link, DEFAULT_EDIT_ICON)

    class Meta:
        model = Track

        template_name = "django_tables2/bootstrap.html"
        sequence = ("id", "title", "file_name", "track_type", "no", "height")
        fields = sequence
