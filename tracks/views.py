from itertools import groupby

from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import redirect, render

from browser.views import getBrowserTypeCookie
from datasources.defaults import FILE_TYPE_BED, get_filetypes_by_attribute
from datasources.models import TrackFile
from plots.models import Plot
from tadeus_portal.utils import is_object_readonly, only_public_or_user

from .forms import TrackForm
from .models import Track


def redirect_to_plot(request, p_id):

    if getBrowserTypeCookie(request) == "synthenic":
        return redirect("browser:browser", p_id=p_id)

    return redirect("browser:breakpoint_browser", p_id=p_id)


def get_domain_files(request):
    return TrackFile.objects.filter(file_type=FILE_TYPE_BED).filter(only_public_or_user(request), Q(eval__isnull=True)).order_by("name", "id")


def get_track_files(request, plot):

    track_files = TrackFile.objects.filter(Q(assembly=plot.assembly), only_public_or_user(request), Q(eval__isnull=True)).order_by(
        "file_type", Lower("name"), "id"
    )

    track_files = groupby(track_files, key=lambda x: x.get_long_file_type_name)

    track_files = [(group_name, list(elements)) for group_name, elements in track_files]

    return track_files


def get_track_data(request, p_id):

    plot = Plot.objects.get(pk=p_id)

    return {
        "domains_files": get_domain_files(request),
        "chroms": plot.assembly.chromosomes.all(),
        "track_files": get_track_files(request, plot),
        "filetypes_by_attribute": get_filetypes_by_attribute(),
        "plot": plot,
    }


def update(request, p_id):

    track = Track.objects.get(pk=p_id)
    plot = Plot.objects.get(pk=track.plot_id)

    if request.method == "POST":
        form = TrackForm(request.POST, instance=track)

        if form.is_valid():
            track = form.save()
            messages.success(request, "Track successfully saved.")
        else:
            messages.error(request, "Track not saved.")

    else:
        form = TrackForm(instance=track)

    context = get_track_data(request, plot.id)

    context["readonly"] = is_object_readonly(request, track.plot)
    context["form"] = form
    context["subtracks"] = track.track_file.subtracks.all()
    context["p_id"] = p_id
    context["track"] = track

    return render(request, "tracks/track.html", context)


def delete(request, p_id):

    track = Track.objects.get(pk=p_id)
    p_plot_id = track.plot.id
    track.delete()

    messages.success(request, "Track successfully deleted.")
    return redirect_to_plot(request, p_plot_id)


def create(request, p_plot_id):

    plot = Plot.objects.get(pk=p_plot_id)
    tracks = plot.tracks.all()

    track_numbers = [track.no for track in tracks] + [0]
    track_number = (max(track_numbers) + 10) // 10 * 10

    if request.method == "POST":
        form = TrackForm(request.POST)

        if form.is_valid():
            track = form.save(commit=False)
            track.plot = plot
            track.save()

            messages.success(request, "Track successfully created.")

            return redirect_to_plot(request, p_plot_id)

    else:
        form = TrackForm(initial={"no": track_number})

    context = get_track_data(request, plot.id)
    context["form"] = form

    return render(request, "tracks/track.html", context)


def fox(request):
    return render(request, "tracks/fox.html")
