from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig

from datasources.readBed import ReadBedOrBedGraphException
from tadeus_portal.utils import get_file_handle, is_object_readonly, only_public_or_user, set_owner_or_cookie

from .forms import TrackFileForm
from .models import Assembly, TrackFile
from .tables import TrackFileFilter, TrackFileTable


def index(request):

    track_files = TrackFile.objects.filter(~Q(file_type="XA"), only_public_or_user(request), Q(eval__isnull=True)).order_by(
        "owner", "assembly", "file_type", "name", "id"
    )

    f = TrackFileFilter(request.GET, queryset=track_files)
    table = TrackFileTable(f.qs)

    RequestConfig(request).configure(table)
    return render(request, "datasources/datasources.html", {"table": table, "filter": f})


def update(request, p_id):

    track_file = TrackFile.objects.get(pk=p_id)

    if request.method == "POST":
        form = TrackFileForm(request.POST, instance=track_file)

        if form.is_valid():
            track_file = form.save()
            messages.success(request, "Data source successfully saved.")
        else:
            messages.error(request, "Data was NOT successfully saved.")

    else:
        form = TrackFileForm(instance=track_file)

    return render(
        request,
        "datasources/datasource.html",
        {
            "form": form,
            "assemblies": Assembly.objects.all(),
            "p_id": p_id,
            "datasource_br": track_file.name,
            "readonly": is_object_readonly(request, track_file),
        },
    )


def create(request, p_type):

    if request.method == "POST":
        form = TrackFileForm(request.POST, request.FILES)

        if form.is_valid():

            try:

                track_file = form.save(commit=False)

                set_owner_or_cookie(request, track_file)
                file_handle = get_file_handle(p_type, form)

                track_file.save()

                track_file.read_bed(file_handle)

                track_file.save()

                messages.success(request, f"Data source '{track_file.name}' successfully created.")

                return redirect("datasources:update", p_id=track_file.id)

            except ReadBedOrBedGraphException as exp:
                messages.error(request, exp)

    else:
        form = TrackFileForm()

    return render(request, "datasources/datasource.html", {"form": form, "assemblies": Assembly.objects.all(), "p_type": p_type, "p_id": None})


def delete(request, p_id):

    try:
        track_file = TrackFile.objects.get(pk=p_id)
        track_file.delete()

        messages.success(request, "Data source successfully deleted.")
    except ProtectedError:
        messages.error(request, "You cannot delete this data source. It is used in a plot.")
        return redirect("datasources:update", p_id=p_id)

    return redirect("datasources:index")
