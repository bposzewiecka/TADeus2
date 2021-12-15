from urllib.parse import quote_plus, urlencode

import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from tadeus_portal.defaults import BREAKPOINT_BROWSER_ICON, DEFAULT_BROWSER_ICON, DEFAULT_EDIT_ICON
from tadeus_portal.utils import getLink

from .models import Evaluation, SVEntry


class EvaluationTable(tables.Table):
    def render_id(self, record):
        link = reverse("evaluation:update", kwargs={"p_id": record.id})
        return getLink(link, DEFAULT_EDIT_ICON)

    class Meta:
        model = Evaluation
        template_name = "django_tables2/bootstrap.html"
        sequence = (
            "id",
            "name",
        )
        fields = sequence


class EvaluationFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Evaluation
        fields = [
            "name",
        ]


class EvaluationEntryTable(tables.Table):
    def __init__(self, rows, multi_plot_id):
        super().__init__(rows)
        self.multi_plot_id = multi_plot_id

    show_in_browser = tables.Column(empty_values=(), orderable=False)
    show_in_breakpoint_browser = tables.Column(empty_values=(), orderable=False)
    length = tables.Column(empty_values=(), orderable=False)
    start = tables.Column(accessor="start")
    end = tables.Column(accessor="end")
    TADA_score = tables.Column(accessor="TADA_score")
    TADeus_score = tables.Column(accessor="TADeus_score")
    ClassifyCNV = tables.Column(accessor="ClassifyCNV")
    delete_button = tables.Column(empty_values=(), orderable=False)

    def render_length(self, record):
        return f"{record.end - record.start:,}"

    def render_delete_button(self, record):

        link = reverse(
            "evaluation:delete_entry",
            kwargs={
                "p_id": record.id,
            },
        )

        delete_text = "return confirm('Are you sure you want to delete this SV?')"
        return format_html(f'<a class="btn btn-danger" href="{link}" onclick="{delete_text}" role="button">Delete</a>')

    def render_show_in_browser(self, record):

        add_space = 1000 * 1000

        start = int(max(0, record.start - add_space))
        end = int(record.end + add_space)

        link = reverse(
            "browser:browser",
            kwargs={
                "p_id": self.multi_plot_id,
                "p_chrom": record.chrom,
                "p_start": start,
                "p_end": end,
            },
        )

        get_url = "?" + urlencode({"interval_start": record.start, "interval_end": record.end}, quote_via=quote_plus)

        return getLink(link + get_url, DEFAULT_BROWSER_ICON)

    def render_show_in_breakpoint_browser(self, record):

        link = reverse("browser:breakpoint_browser", kwargs={"p_id": self.multi_plot_id})

        return getLink(link, BREAKPOINT_BROWSER_ICON)

    class Meta:
        model = SVEntry
        template_name = "django_tables2/bootstrap.html"
        sequence = (
            "show_in_browser",
            "show_in_breakpoint_browser",
            "name",
            "sv_type",
            "chrom",
            "start",
            "end",
            "TADA_score",
            "ClassifyCNV",
            "TADeus_score",
            "length",
            "delete_button",
        )
        fields = sequence
        localize = (
            "start",
            "end",
        )
