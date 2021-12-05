from django.shortcuts import render
from django.http import HttpResponse
from . import trackPlot
import matplotlib.pyplot as plt
from django.conf import settings
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist


from tadeus.models import Plot, Track

from evaluation.models import Evaluation

from ontologies.models import Phenotype, Gene
from tadeus.misc import split_seq

from django.contrib import messages

from django.db.models import Q, ProtectedError

from django.db.models.functions import Lower


from django.db import transaction

from .forms import CreateTrackForm, PlotForm, TrackForm

from django_tables2 import RequestConfig

from .tables import PlotTable
from .tables import PlotFilter

from evaluation.models import Evaluation

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from urllib.parse import urlencode, quote_plus

from collections import Counter
from scipy import stats

from tadeus.defaults import DEFAULT_WIDTH_PROP


def edit_track(request, p_id):

    track = Track.objects.get(pk = p_id)

    if request.method == "POST":
        form = TrackForm(request.POST, instance = track)

        if form.is_valid():
            track = form.save()
            messages.success(request, 'Track successfully saved.')
        else:
            messages.success(request, 'Track not saved.')
            print(form.errors)
    else:
        
        form = TrackForm(instance = track)

    domains_files = None
    readonly = is_object_readonly(request, track.plot)
    chroms = track.plot.assembly.chromosomes.all()

    if track.get_file_type() == 'HI':
        domains_files = TrackFile.objects.filter(file_type = 'BE').filter(only_public_or_user(request),  Q(eval__isnull=True)).order_by('name', 'id')


    print(track.track_file.subtracks.all())

    return render(request, 'tracks/track.html', {'form': form,
                   'p_id':  p_id, 
                   'track': track,
                   'plot_id': track.plot.id,
                   'file_type': track.get_file_type(), 
                   'file_sub_type': track.get_bed_sub_type(),
                   'readonly': readonly,
                   'plot_br': track.plot.name,
                   'track_br': track.track_file.name,
                   'track_name': track.track_file.name,
                   'style_choices': track.get_style_choices(),
                   'domains_files': domains_files,
                   'hic_display': track.hic_display,
                   'hic_display_name': track.get_hic_display_display(),
                   'chroms': chroms,
                   'subtracks': track.track_file.subtracks.all()})


def delete_track(request, p_id):

    track = Track.objects.get(pk =p_id)
    plot_id = track.plot.id
    track.delete()

    messages.success(request, 'Track successfully deleted.')
    return redirect(edit_plot, p_id = plot_id)

def create_track(request, p_plot_id):

    plot = Plot.objects.get(pk = p_plot_id)
    tracks = plot.tracks.all()

    track_numbers = [track.no for track in tracks] + [0]
    track_number = (max(track_numbers) + 10) // 10 * 10


    if request.method == "POST":
        form = CreateTrackForm(request.POST)

        if form.is_valid():
            track = form.save(commit = False)
            track.plot = plot
            track.save()

            messages.success(request, 'Track successfully created.')
            return redirect(edit_track, p_id = track.id)

    else:
        form = CreateTrackForm(initial={'no': track_number})

    track_files = TrackFile.objects.filter(Q(assembly = plot.assembly), only_public_or_user(request)).order_by(Lower('name'),'id')
    
    return render(request, 'tracks/add_track.html', {'form': form, 'p_plot_id': p_plot_id, 'track_files': track_files, 'plot': plot })


def index(request):
    #evals = Evaluation.objects.filter(owner__username = 'root') 
    #table = EvalTable(evals)
    #RequestConfig(request).configure(table)
    table = None
    return render(request, 'tracks/index.html', {'table': table })