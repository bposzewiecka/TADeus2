# tutorial/tables.py
import django_tables2 as tables
from .models import Plot, Track, TrackFile, Eval, BedFileEntry, Phenotype, Gene, Breakpoint, Sample

from django.urls import reverse
from django.utils.html import format_html
from django.db.models import F

from tadeus.defaults import DEFAULT_EDIT_ICON, DEFAULT_BROWSER_ICON
from django.db.models import Q
import django_filters

from urllib.parse import urlencode, quote_plus

def getLink(link, icon):
    return format_html('<a href="{link}"><i class="fas ' + icon + '"></i></a>', link = link) 

class PlotTable(tables.Table):

    edit_tracks = tables.Column(empty_values=(), orderable=False)
    show_in_browser = tables.Column(empty_values=(), orderable=False)

    def render_edit_tracks(self, record):
        link = reverse('edit_plot', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON)

    def render_show_in_browser(self, record):

        link = reverse('browser', kwargs = {'p_id': record.id}) 
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
        sequence = ('id', 'title',  'file_name', 'no', 'column', 'height')
        fields = sequence


class TrackFileTable(tables.Table):
    
    source = tables.Column(empty_values=(), order_by=('source_name'))
    organism = tables.Column(orderable=False)
    number_of_entries = tables.Column(empty_values=())

    def render_id(self, record):
        link = reverse('edit_datasource', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON) 


    def render_number_of_entries(self, record):
        return  TrackFile.objects.get(pk = record.id).file_entries.count()

    def render_source(self, record):
        if record.source_url is None:
            return record.source_name if record.source_name else ''
        else:	
            return format_html('<a href="{link}" target="_blank">{name}</a>', link = record.source_url, name = record.source_name)

    class Meta:
        model = TrackFile
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('id', 'organism',  'assembly', 'file_type', 'name', 'source', 'reference', 'number_of_entries', 'owner', 'public')
        fields = sequence

class TrackFileFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TrackFile
        fields = ['assembly', 'file_type', 'name', ]

class EvalTable(tables.Table):

    def render_id(self, record):
        link = reverse('edit_eval', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON) 

    class Meta:
        model = Eval
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('id', 'name',)
        fields = sequence


class EvalFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Eval
        fields = ['name', ]

class EvalEntryTable(tables.Table):

    def __init__(self, rows, multi_plot_id):
        super(EvalEntryTable, self).__init__(rows)
        self.multi_plot_id = multi_plot_id


    show_in_browser = tables.Column(empty_values=(), orderable=False)
    length = tables.Column(empty_values=(), orderable=False)
    start = tables.Column(accessor='start')
    end = tables.Column(accessor='end')

    def render_length(self, record):
        return "{:,}".format(record.end - record.start)

    def render_show_in_browser(self, record):

        entry_len = record.end - record.start 

        add_space = 1000 * 1000

        start =  int(max(0, record.start - add_space))
        end =  int(record.end + add_space )

        link = reverse('browser', kwargs = {'p_id': self.multi_plot_id, 
                                            'p_chrom': record.chrom, 
                                            'p_start': start,
                                            'p_end': end,
                                            }) 

        get_url = '?' + urlencode({'interval_start':  record.start, 'interval_end':  record.end}, quote_via=quote_plus)

        return getLink(link + get_url, DEFAULT_BROWSER_ICON) 


    class Meta:
        model = BedFileEntry
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('show_in_browser', 'name', 'chrom', 'start', 'end', 'length', 'score', )
        fields = sequence
        localize = ('start', 'end', )



class PhenotypeTable(tables.Table):

    class Meta:
        model = Phenotype
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('db',  'link', 'name', 'definition', 'comment', 'is_a')
        fields = sequence


class PhenotypeFilter(django_filters.FilterSet):

    pheno_id = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    definition = django_filters.CharFilter(lookup_expr='icontains')
    comment =  django_filters.CharFilter(lookup_expr='icontains')


    class Meta:
        model =  Phenotype
        fields = ('db', 'pheno_id', 'name',  'definition', 'comment')
 

class GeneTable(tables.Table):

    def render_id(self, record):
        link = reverse('gene', kwargs = {'p_id': record.id})
        return getLink(link, DEFAULT_EDIT_ICON) 

    class Meta:
        model = Gene
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('id', 'name', 'ensembl_gene_id', 'chrom', 'start', 'end',  'strand', 'biotype')
        fields = sequence

class GeneFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')
    ensembl_gene_id = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Gene
        fields = ( 'name', 'ensembl_gene_id')



class BreakpointTable(tables.Table):
    
    assembly = tables.Column(empty_values=())
    sample = tables.Column(empty_values=())

    #def render_assembly(self, record):
    #    return record.assembly

    def render_right_inverse(self, record):
        return 'yes' if record.right_inverse else 'no'
 
    def render_left_inverse(self, record):
        return 'yes' if record.left_inverse else 'no'

    class Meta:
        model = Breakpoint
        template_name = 'django_tables2/bootstrap.html'
        sequence = ('id', 'sample', 'left_chrom', 'left_coord', 'left_inverse', 'right_chrom', 'right_coord', 'right_inverse', 'owner', 'public', 'assembly')
        fields = sequence


class BreakpointFilter(django_filters.FilterSet):

    sample = django_filters.ModelChoiceFilter(queryset = Sample.objects.all())


    def do_not_filter(self, queryset, name, value):
        return queryset

    min_range = django_filters.NumberFilter(method = 'do_not_filter')
    max_range = django_filters.NumberFilter(method = 'do_not_filter')
    chrom = django_filters.CharFilter(method = 'do_not_filter')

    class Meta:
        model = Breakpoint
        fields = ( 'sample', 'chrom', 'min_range', 'max_range')
