from django.shortcuts import render

from datasources.models import Chromosome

from .forms import TranslocationForm


def index(request):
    # evals = Evaluation.objects.filter(owner__username = 'root')
    # table = EvalTable(evals)
    # RequestConfig(request).configure(table)

    chromosomes = Chromosome.objects.filter(assembly__name="hg38")

    trans_form = TranslocationForm()

    return render(request, "tadeus/index.html", {"trans_form": trans_form, "chromosomes": chromosomes})
