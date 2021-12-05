from django.shortcuts import render

from .models import Phenotype, Gene
from .tables import PhenotypeTable,  PhenotypeFilter, GeneTable,  GeneFilter
from django_tables2 import RequestConfig

def phenotypes(request, p_db):

    phenotypes = Phenotype.objects.filter(db = p_db).order_by('pheno_id')

    f = PhenotypeFilter(request.GET, queryset = phenotypes)
    table = PhenotypeTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'ontologies/phenotypes.html', {'table': table, 'filter': f, 'db' : p_db })


def genes(request):

    genes = Gene.objects.all().order_by('name')

    f = GeneFilter(request.GET, queryset = genes)
    table = GeneTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'ontologies/genes.html', { 'table': table, 'filter': f})


def gene(request,p_id):

    gene = Gene.objects.get(pk=p_id)

    phenotypes = gene.phenotypes.all()
    f = PhenotypeFilter(request.GET, queryset = phenotypes)
    table = PhenotypeTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'ontologies/gene.html', {'table': table,'filter': f, 'gene':gene })