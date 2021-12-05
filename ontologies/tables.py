from .models import Phenotype, Gene

import django_tables2 as tables
import django_filters
from django.urls import reverse

from urllib.parse import urlencode, quote_plus

#from tadeus.tables import getLink, DEFAULT_EDIT_ICON


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
        sequence = ('id', 'name', 'ensembl_gene_id', 'entrezgene_id', 'chrom', 'start', 'end',  'strand', 'gene_biotype')
        fields = sequence

class GeneFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')
    ensembl_gene_id = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Gene
        fields = ( 'name', 'ensembl_gene_id')