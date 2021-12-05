from .models import Plot

import django_tables2 as tables
import django_filters

from django.urls import reverse

from tadeus_portal.utils import getLink 
from tadeus_portal.defaults import  DEFAULT_EDIT_ICON,DEFAULT_BROWSER_ICON


class PlotTable(tables.Table):

    edit_tracks = tables.Column(empty_values=(), orderable=False)
    show_in_browser = tables.Column(empty_values=(), orderable=False)

    def render_edit_tracks(self, record):
        link = reverse('plots:update', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON)

    def render_show_in_browser(self, record):

        link = reverse('browser:browser', kwargs = {'p_id': record.id}) 
        return getLink(link, DEFAULT_BROWSER_ICON)

    class Meta:
        model = Plot
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('show_in_browser', 'edit_tracks',  'name', 'title', 'assembly', 'owner', 'public')
        fields = sequence

class PlotFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Plot
        fields = ['name', 'title', 'assembly']

