import django_tables2 as tables
from .models import Plot,  Track, Sample

from django.urls import reverse

from django.db.models import F

from tadeus.defaults import DEFAULT_EDIT_ICON, DEFAULT_BROWSER_ICON
from django.db.models import Q
import django_filters

from urllib.parse import urlencode, quote_plus


class TrackTable(tables.Table):

    file_name = tables.Column(empty_values=(), orderable=False)

    def render_file_name(self, record):
        return record.track_file.name

    def render_id(self, record):
        link = reverse('track', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON) 

    class Meta:
        model = Track

        template_name = 'django_tables2/bootstrap.html'
        sequence = ('id', 'title',  'file_name', 'no', 'height')
        fields = sequence
