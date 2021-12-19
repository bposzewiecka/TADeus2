from django.shortcuts import render

from datasources.models import Chromosome

from .forms import CNVForm, TranslocationForm


def index(request):
    chromosomes = Chromosome.objects.filter(assembly__name="hg38")

    trans_form = TranslocationForm()
    cnv_form = CNVForm()

    return render(request, "tadeus/index.html", {"trans_form": trans_form, "cnv_form": cnv_form, "chromosomes": chromosomes})


def index2(request):

    return render(request, "tadeus_portal/moj.html", {})
