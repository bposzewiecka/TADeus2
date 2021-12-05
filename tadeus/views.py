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

def setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end):
    request.session['plot_' + str(p_id)] = (p_chrom, p_start, p_end, p_interval_start, p_interval_end)
    request.session['plot'] = (p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)

def getPlotCookie(request, p_id):
    if 'plot_' + str(p_id) in request.session:
        return request.session['plot_' + str(p_id)]
    return 'chr1', 30 * 1000 * 1000, 33 * 1000 * 1000 , None, None


def deletePlotCookie(request, p_id):
    if 'plot_' + str(p_id) in request.session:
        del request.session['plot_' + str(p_id)]

    if 'plot' in request.session and request.session['plot'][0] == str(p_id):
        del request.session['plot']

def printPlotCookie(request, p_id):
    if 'plot_' + str(p_id) in request.session:
        print(request.session['plot_' + str(p_id)])
    else:
        'Plot ' + str(p_id) + 'does not have cookie.'

def plots(request):

    plots = Plot.objects.filter(only_public_or_user(request))

    f = PlotFilter(request.GET, queryset=plots)
    table = PlotTable(f.qs)
    RequestConfig(request).configure(table)

    return render(request, 'tadeus/plots.html', {'table': table, 'filter': f})


def create_plot(request):

    if request.method == "POST":
        form = PlotForm(request.POST)

        if form.is_valid():
           plot = form.save(commit = False)

           set_owner_or_cookie(request, plot)

           plot.save()

           p_id = plot.id

           return redirect(edit_plot, p_id= p_id)

    else:
        form = PlotForm()

    return render(request, 'tadeus/plot.html', {'form': form, 'assemblies': Assembly.objects.all() })


def edit_plot(request, p_id):

    plot = Plot.objects.get(pk =p_id)
    tracks = plot.tracks.all().order_by('no','id')
    table = TrackTable(tracks)
    RequestConfig(request).configure(table)

    if request.method == "POST":
        form = PlotForm(request.POST, instance = plot)

        if form.is_valid():
            plot = form.save()

            if 'add_track' in request.POST:
                return redirect(create_track, p_plot_id = p_id)

    else:
        form = PlotForm(instance = plot)

    return render(request, 'tadeus/plot.html', {'table': table,  'form': form,
                'p_id': p_id, 'assemblies': Assembly.objects.all() , 'has_tracks': len(tracks) > 0,
                'readonly': is_object_readonly(request, plot), 'plot' : plot})


def delete_plot(request, p_id):

    plot = Plot.objects.get(pk =p_id)

    try: 
     
        plot.delete()
        deletePlotCookie(request, p_id)

        messages.success(request, 'Plot "{}" successfully deleted.'.format(plot.name))
    except  ProtectedError:
        messages.error(request, 'You cannot delete this plot. It belongs to evaluation.')
        return redirect(edit_plot, p_id = p_id)

    return redirect(plots)

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

    return render(request, 'tadeus/track.html', {'form': form,
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
    
    return render(request, 'tadeus/add_track.html', {'form': form, 'p_plot_id': p_plot_id, 'track_files': track_files, 'plot': plot })


def index(request):
    #evals = Evaluation.objects.filter(owner__username = 'root') 
    #table = EvalTable(evals)
    #RequestConfig(request).configure(table)
    table = None
    return render(request, 'tadeus/index.html', {'table': table })