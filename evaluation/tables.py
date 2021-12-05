from .models import Evaluation

import django_tables2 as tables
import django_filters

class EvaluationTable(tables.Table):

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
        model = Evaluation
        fields = ['name', ]

class EvaluationEntryTable(tables.Table):

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
