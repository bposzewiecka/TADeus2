import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from tadeus_portal.defaults import DEFAULT_EDIT_ICON
from tadeus_portal.utils import getLink

from .models import TrackFile


class TrackFileTable(tables.Table):

    source = tables.Column(empty_values=(), order_by=("source_name"))
    organism = tables.Column(orderable=False)
    number_of_entries = tables.Column(empty_values=())

    def render_id(self, record):
        link = reverse("datasources:update", kwargs={"p_id": record.id})
        return getLink(link, DEFAULT_EDIT_ICON)

    def render_number_of_entries(self, record):
        return TrackFile.objects.get(pk=record.id).file_entries.count()

    def render_source(self, record):
        if record.source_url is None:
            return record.source_name if record.source_name else ""
        else:
            return format_html('<a href="{link}" target="_blank">{name}</a>', link=record.source_url, name=record.source_name)

    class Meta:
        model = TrackFile
        template_name = "django_tables2/bootstrap.html"
        sequence = ("id", "organism", "assembly", "file_type", "name", "source", "reference", "number_of_entries", "owner", "public")
        fields = sequence


class TrackFileFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TrackFile
        fields = [
            "assembly",
            "file_type",
            "name",
        ]
