from django.shortcuts import render

from .forms import TranslocationForm


def index(request):
    # evals = Evaluation.objects.filter(owner__username = 'root')
    # table = EvalTable(evals)
    # RequestConfig(request).configure(table)

    trans_form = TranslocationForm()

    return render(request, "tadeus/index.html", {"trans_form": trans_form})
