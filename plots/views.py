from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig

from datasources.models import Assembly
from tadeus_portal.utils import is_object_readonly, only_public_or_user, set_owner_or_cookie
from tracks.tables import TrackTable

from .forms import PlotForm
from .models import Plot
from .tables import PlotFilter, PlotTable


def setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end):
    request.session["plot_" + str(p_id)] = (p_chrom, p_start, p_end, p_interval_start, p_interval_end)
    request.session["plot"] = (p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)


def getPlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        return request.session["plot_" + str(p_id)]
    return "chr1", 30 * 1000 * 1000, 33 * 1000 * 1000, None, None


def deletePlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        del request.session["plot_" + str(p_id)]

    if "plot" in request.session and request.session["plot"][0] == str(p_id):
        del request.session["plot"]


"""
def printPlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        print(request.session["plot_" + str(p_id)])
    else:
        "Plot " + str(p_id) + "does not have cookie."
"""


def index(request):

    plots = Plot.objects.filter(only_public_or_user(request))

    f = PlotFilter(request.GET, queryset=plots)
    table = PlotTable(f.qs)
    RequestConfig(request).configure(table)

    return render(request, "plots/plots.html", {"table": table, "filter": f})


def create(request):

    if request.method == "POST":
        form = PlotForm(request.POST)

        if form.is_valid():
            plot = form.save(commit=False)

            set_owner_or_cookie(request, plot)

            plot.save()

            p_id = plot.id

            return redirect("plots:update", p_id=p_id)

    else:
        form = PlotForm()

    return render(request, "plots/plot.html", {"form": form, "assemblies": Assembly.objects.all()})


def update(request, p_id):

    plot = Plot.objects.get(pk=p_id)
    tracks = plot.tracks.all().order_by("no", "id")
    table = TrackTable(tracks)
    RequestConfig(request).configure(table)

    if request.method == "POST":
        form = PlotForm(request.POST, instance=plot)

        if form.is_valid():
            plot = form.save()

            if "add_track" in request.POST:
                return redirect("tracks:create", p_plot_id=p_id)

    else:
        form = PlotForm(instance=plot)

    return render(
        request,
        "plots/plot.html",
        {
            "table": table,
            "form": form,
            "p_id": p_id,
            "assemblies": Assembly.objects.all(),
            "has_tracks": len(tracks) > 0,
            "readonly": is_object_readonly(request, plot),
            "plot": plot,
        },
    )


def delete(request, p_id):

    plot = Plot.objects.get(pk=p_id)

    try:

        plot.delete()
        deletePlotCookie(request, p_id)

        messages.success(request, f'Plot "{plot.name}" successfully deleted.')
    except ProtectedError:
        messages.error(request, "You cannot delete this plot. It belongs to evaluation.")
        return redirect("plots:update", p_id=p_id)

    return redirect("plots:index")
