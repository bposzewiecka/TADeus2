from django.shortcuts import render


def index(request):
    # evals = Evaluation.objects.filter(owner__username = 'root')
    # table = EvalTable(evals)
    # RequestConfig(request).configure(table)
    table = None
    return render(request, "tadeus/index.html", {"table": table})
