from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import redirect, render

from datasources.models import TrackFile
from plots.models import Plot
from tadeus_portal.utils import is_object_readonly, only_public_or_user

from .forms import CreateTrackForm, TrackForm
from .models import Track


def update(request, p_id):

    track = Track.objects.get(pk=p_id)

    if request.method == "POST":
        form = TrackForm(request.POST, instance=track)

        if form.is_valid():
            track = form.save()
            messages.success(request, "Track successfully saved.")
        else:
            messages.success(request, "Track not saved.")
    else:

        form = TrackForm(instance=track)

    domains_files = None
    readonly = is_object_readonly(request, track.plot)
    chroms = track.plot.assembly.chromosomes.all()

    if track.get_file_type() == "HI":
        domains_files = TrackFile.objects.filter(file_type="BE").filter(only_public_or_user(request), Q(eval__isnull=True)).order_by("name", "id")

    return render(
        request,
        "tracks/track.html",
        {
            "form": form,
            "p_id": p_id,
            "track": track,
            "plot_id": track.plot.id,
            "file_type": track.get_file_type(),
            "file_sub_type": track.get_bed_sub_type(),
            "readonly": readonly,
            "plot_br": track.plot.name,
            "track_br": track.track_file.name,
            "track_name": track.track_file.name,
            "style_choices": track.get_style_choices(),
            "domains_files": domains_files,
            "hic_display": track.hic_display,
            "hic_display_name": track.get_hic_display_display(),
            "chroms": chroms,
            "subtracks": track.track_file.subtracks.all(),
        },
    )


def delete(request, p_id):

    track = Track.objects.get(pk=p_id)
    plot_id = track.plot.id
    track.delete()

    messages.success(request, "Track successfully deleted.")
    return redirect("plots:edit", p_id=plot_id)


def create(request, p_plot_id):

    plot = Plot.objects.get(pk=p_plot_id)
    tracks = plot.tracks.all()

    track_numbers = [track.no for track in tracks] + [0]
    track_number = (max(track_numbers) + 10) // 10 * 10

    if request.method == "POST":
        form = CreateTrackForm(request.POST)

        if form.is_valid():
            track = form.save(commit=False)
            track.plot = plot
            track.save()

            messages.success(request, "Track successfully created.")
            return redirect("tracks:edit", p_id=track.id)

    else:
        form = CreateTrackForm(initial={"no": track_number})

    track_files = TrackFile.objects.filter(Q(assembly=plot.assembly), only_public_or_user(request)).order_by(Lower("name"), "id")

    return render(request, "tracks/add_track.html", {"form": form, "p_plot_id": p_plot_id, "track_files": track_files, "plot": plot})
