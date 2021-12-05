import django_filters
import django_tables2 as tables

from datasources.models import Sample

from .models import Breakpoint


class BreakpointTable(tables.Table):

    assembly = tables.Column(empty_values=())
    sample = tables.Column(empty_values=())

    # def render_assembly(self, record):
    #    return record.assembly

    def render_right_inverse(self, record):
        return "yes" if record.right_inverse else "no"

    def render_left_inverse(self, record):
        return "yes" if record.left_inverse else "no"

    class Meta:
        model = Breakpoint
        template_name = "django_tables2/bootstrap.html"
        sequence = (
            "id",
            "sample",
            "left_chrom",
            "left_coord",
            "left_inverse",
            "right_chrom",
            "right_coord",
            "right_inverse",
            "owner",
            "public",
            "assembly",
        )
        fields = sequence


class BreakpointFilter(django_filters.FilterSet):

    sample = django_filters.ModelChoiceFilter(queryset=Sample.objects.all())

    def do_not_filter(self, queryset, name, value):
        return queryset

    min_range = django_filters.NumberFilter(method="do_not_filter")
    max_range = django_filters.NumberFilter(method="do_not_filter")
    chrom = django_filters.CharFilter(method="do_not_filter")

    class Meta:
        model = Breakpoint
        fields = ("sample", "chrom", "min_range", "max_range")
