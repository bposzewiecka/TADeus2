from django.shortcuts import render
from django.http import HttpResponse
from . import trackPlot
import matplotlib.pyplot as plt
from django.conf import settings
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
import re, random, string

from tadeus.models import Plot, Track, TrackFile, Assembly, Eval, Phenotype, Gene, Breakpoint, Sample
from tadeus.misc import split_seq

from django.contrib import messages

from django.db.models import Q, ProtectedError

from django.db.models.functions import Lower

from io import StringIO, TextIOWrapper, BytesIO
from tadeus.readBed import BedOrBedGraphReader, ReadBedOrBedGraphException
from django.db import transaction

from .forms import CreateTrackForm, PlotForm, TrackForm, TrackFileForm, EvalForm, EvalAddEntryForm

from django_tables2 import RequestConfig
from .tables import PlotTable, TrackTable, TrackFileTable, EvalTable, EvalEntryTable, PhenotypeTable, GeneTable, BreakpointTable
from .tables import TrackFileFilter, EvalFilter, PlotFilter, PhenotypeFilter, GeneFilter, BreakpointFilter

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from urllib.parse import urlencode, quote_plus

from collections import Counter
from scipy import stats

from tadeus.defaults import DEFAULT_WIDTH_PROP

def is_object_readonly(request, obj):
    auth_cookie = get_auth_cookie(request)

    return (request.user.is_authenticated and request.user != obj.owner) or (not request.user.is_authenticated and auth_cookie != obj.auth_cookie)

def only_public_or_user(request):
    user =  request.user if request.user.is_authenticated else None

    if request.user.is_authenticated:
        return Q(public = True) | Q(owner = user)

    auth_cookie = get_auth_cookie(request)

    return Q(public = True) |  Q(auth_cookie = auth_cookie)


def set_owner_or_cookie(request, p_obj):

    auth_cookie = get_auth_cookie(request)

    if request.user.is_authenticated:
        p_obj.owner = request.user
    else:
        p_obj.auth_cookie = auth_cookie

def get_chrom_length(plot_id, chrom):
    assembly = Plot.objects.get(id = plot_id).assembly
    return assembly.chromosomes.get(name = chrom).size


def get_region_or_err_msg(search_text, plot_id):

    search_text  = re.sub(r'(\s|,)', '', search_text)

    if search_text == '':
        return 'Enter valid position query'

    sre = re.search('^chr(\d+|X|Y):(\d+)-(\d+)$',search_text)

    if not sre:
        return '"{search_text}" is not valid position query'.format(search_text = search_text)

    sre =  sre.groups()

    chrom = 'chr' + sre[0]
    start =  int(sre[1])
    end = int(sre[2])

    if start >= end:
        return 'End coordinate should be greater than start coordinate. Your position query: {search_text}'.format(search_text = search_text)

    try:    
        chrom_size = get_chrom_length(plot_id, chrom)
       
        if end > chrom_size:
            return 'End coordinate greater than chromosome size ({chrom_size}). Your position query: {search_text}'.format(chrom_size = chrom_size, search_text = search_text)

        if start > chrom_size:
            return 'Start coordinate greater then chromosome size ({chrom_size}). Your position query: {search_text}'.format(chrom_size = chrom_size, search_text = search_text)

    except ObjectDoesNotExist:
        return  'Chromosome "{chrom}" does not exists. Search text: {search_text}'.format(chrom = chrom, search_text = search_text)

    return  chrom, start, end

def move(start, end, perc, right):
    region_len =  end - start
    m =int(region_len  * perc)

    if right:
        return start + m, end + m, 100 * perc
    else:
        return max(start - m, 0), max(end - m, region_len), 100 * perc

def zoom(start, end, perc, zoom_in):

    if  zoom_in:
        perc = 1 / perc

    region_len =  end - start
    middle = start + region_len / 2

    new_region_len  = region_len * perc

    return max(int(middle - new_region_len / 2), 0), max(int(middle + new_region_len / 2), int(new_region_len ))


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

def generateRandomString(n):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def get_auth_cookie(request):
    if 'auth' not in request.session:
        request.session['auth'] = generateRandomString(n=25)

    auth_cookie = request.session['auth']
    request.session.set_expiry(356 * 24 * 60 * 60)

    return request.session['auth']

def ranking(eval, p_chrom, p_interval_start, p_interval_end):
    p_interval_start, p_interval_end = int(p_interval_start), int(p_interval_end)

    region_start = max(p_interval_start - 3 * 1000 * 1000, 0)
    region_end = p_interval_end + 3 *1000 * 1000

    gene_file = TrackFile.objects.get(pk = 2)

    genes =  gene_file.get_entries(p_chrom, region_start,  region_end)

    genes = { gene.name : { 'gene': Gene.objects.get(pk =gene.id) } for gene in genes } 

    pLI_file = TrackFile.objects.get(pk = 6)
    pLI = { gene.name.upper() : gene.score for gene in pLI_file.get_entries(p_chrom, region_start, region_end) }

    clingen_file = TrackFile.objects.get(pk = 7)
    clingen = { gene.name : gene.score for gene in clingen_file.get_entries(p_chrom, region_start, region_end) }

    enh_prom_file = TrackFile.objects.get(pk = 40)
    enh_proms = [ enh_prom.name.upper() for enh_prom in enh_prom_file.get_entries(p_chrom, p_interval_start, p_interval_end)]
    enh_proms = Counter(enh_proms)


    for gene_name, d in genes.items():
        d['enh_prom'] = enh_proms[gene_name]

    enh_prom_scores = [ gene['enh_prom'] for gene in genes.values()]

    for gene_name, d in genes.items():
        gene = d['gene']
        d['gene_name'] = gene_name

        d['clingen'] = clingen.get(gene_name, None)
        d['clingen_score'] = 100 if clingen.get(gene_name, 0) in (3,2,30) else 0

        d['pLI'] = pLI.get(gene_name, None)

        d['distance'] = None

        d['distance'] = min( abs(p_interval_start - gene.start), 
                        abs(p_interval_end - gene.end))

        if d['distance'] < 1 * 1000 * 1000:
            d['distance_1Mb_score'] = 100
        else:
            d['distance_1Mb_score'] = 0

        d['phenotypes'] = gene.phenotypes.order_by('name', 'pheno_id')

        if d['phenotypes']:
            d['phenotype_score'] = 100
        else:
            d['phenotype_score'] = 0           

        if enh_proms[gene_name]:
            d['enh_prom_score'] = 100
        else:
            d['enh_prom_score'] = 0

        d['rank'] = d['clingen_score'] +  d['enh_prom_score'] +  d['phenotype_score'] + d['distance_1Mb_score'] 

    results = list(genes.items())
    results.sort(key = lambda x : (-x[1]['rank'], -x[1]['enh_prom'], x[1]['distance'], x[1]['gene_name']))

    """
    with open('/home/basia/CNVBrowser/latex/eval_' + str(eval.id) + '_' +  p_chrom + '.txt', 'w') as f_out:


        f_out.write(\\begin{center}
    \\begin{longtable}{ | l | l | l | l | l | l | l |}
  \\hline
   &  & &  Enhancer  &  & &\\\\ 
   &  & &  -promoter  & Distance  &  &\\\\ 
   Gene name  & pLI & Clingen & interactions & from & Phenotypes & Rank \\\\  
   &  &  & number & breakpoints & & \\\\  
  \\hline
"")
 
        for gene_name, gene in results:

            if gene['rank'] == 0:
                continue

            f_out.write(gene_name)
            f_out.write(' & ')
            f_out.write("{0:.4f}".format(gene['pLI']))
            f_out.write(' & ')
            f_out.write("{0:.0f}".format(gene['clingen']))
            f_out.write(' & ')
            f_out.write(str(gene['enh_prom']))
            f_out.write(' & ')
            f_out.write(str(gene['distance']))
            f_out.write(' & ')
            f_out.write('Yes' if gene['phenotypes'] else 'No')
            f_out.write(' & ')
            f_out.write(str(gene['rank']))
            f_out.write('\\\\\n')

        f_out.write('\\hline \\end{longtable} \\end{center}')

        f_out.write('\n\n')



        for gene_name, gene in results:

            phenotypes = gene['phenotypes']

            if not phenotypes:
                continue

            f_out.write('\\begin{center}\n')
            f_out.write('\t\\begin{longtable}{ | p{3cm} |  p{10cm} |}\n')

            f_out.write('\t\t\\hline\n')
            f_out.write('\\multicolumn{2}{ |c| }{' + gene_name + '} \\\\\n')

            f_out.write('\t\t\\hline\n')
            f_out.write('\t\t Name  & Definition and comments \\\\\n')
            f_out.write('\t\t\\hline\n')


            for phenotype in phenotypes:



                f_out.write(phenotype.name)
                f_out.write(' \href{' + phenotype.url + '}{' + phenotype.pheno_id +'}')
                f_out.write(' & ')

                info = []

                if phenotype.definition:
                    definition = 'Definition: ' + phenotype.definition.replace('%', '\%')
                    info.append(definition)
                if phenotype.comment:
                    comment = 'Comment: ' + phenotype.comment.replace('%', '\%')
                    info.append(comment)

                if phenotype.pheno_id in ('HP:0000006', 'HP:0000007'):
                    info = []

                if len(info) > 0:
                    f_out.write(info[0])

                f_out.write('\\\\\n')

                if len(info) == 2:
                    f_out.write(' & ')
                    f_out.write(info[1])                                         
                    f_out.write('\\\\\n')     

                f_out.write('\t\t\\hline\n')               
        
            f_out.write("\\end{longtable} \\end{center}")
"""
    return results    

def zoom_breakpoint(size, shift, perc, zoom_in):

    if  zoom_in:
        perc = 1 / perc

    return urlencode({'shift': int(shift * perc), 'size': int(size * perc)}, quote_via=quote_plus)    

def move_breakpoint(size, shift, perc, right):
    
    m = int(size * perc)

    if right:
        new_shift =  shift + m
    else:
        new_shift = shift - m

    return urlencode({'shift':  new_shift, 'size': size}, quote_via=quote_plus), 100 * perc 

def breakpoint_browser(request, p_id, p_breakpoint_id):

    perc_move = (0.2, 0.1)
    perc_zoom = 1.25

    breakpoint = Breakpoint.objects.get(id = p_breakpoint_id)

    p_plot = Plot.objects.get(id = p_id)

    if request.method == 'GET': 
        p_size = int(request.GET.get('size',  2000000))
        p_shift = int(request.GET.get('shift', 0))

    else:
        pass

    if 2 * abs(p_shift) < p_size :

        right_size = int(p_size / 2) - p_shift

        if breakpoint.right_inverse:
            breakpoint.right_start = breakpoint.right_coord- right_size 
            breakpoint.right_end = breakpoint.right_coord
        else:
            breakpoint.right_start = breakpoint.right_coord
            breakpoint.right_end = breakpoint.right_coord + right_size

        left_size = int(p_size / 2) + p_shift 

        if breakpoint.left_inverse:
            breakpoint.left_start = breakpoint.left_coord
            breakpoint.left_end = breakpoint.left_coord + left_size 
        else:
            breakpoint.left_start = breakpoint.left_coord - left_size
            breakpoint.left_end = breakpoint.left_coord

        breakpoint.left_width_prop = int(left_size / p_size * DEFAULT_WIDTH_PROP)
        breakpoint.right_width_prop = int(right_size / p_size * DEFAULT_WIDTH_PROP)
    
    elif p_size  <= 2 * p_shift:

        breakpoint.left_start = breakpoint.left_coord  - p_shift - p_size
        breakpoint.left_end = breakpoint.left_coord - p_shift

        breakpoint.left_width_prop = DEFAULT_WIDTH_PROP

    else:
        breakpoint.right_start =  breakpoint.right_coord - p_shift - p_size
        breakpoint.right_end = breakpoint.right_coord - p_shift
   
        breakpoint.right_width_prop = DEFAULT_WIDTH_PROP

    url_params = {}

    if breakpoint.left_start: url_params['left_start'] = breakpoint.left_start
    if breakpoint.left_end: url_params['left_end'] = breakpoint.left_end
    if breakpoint.right_start: url_params['right_start'] = breakpoint.right_start
    if breakpoint.right_end: url_params['right_end'] = breakpoint.right_end

    get_url = '?' +  urlencode(url_params, quote_via=quote_plus)

    return TemplateResponse(request, 'tadeus/browser_breakpoint.html', {'p_id': p_id, 
                           'p_plot': p_plot,
                           'p_breakpoint': breakpoint,
                           'p_size': p_size, 
                           'p_shift': p_shift, 
                           'move': ( move_breakpoint( p_size, p_shift, perc_move[0] , False), 
                                     move_breakpoint( p_size, p_shift, perc_move[1] , False),
                                     move_breakpoint( p_size, p_shift, perc_move[1] , True),
                                     move_breakpoint( p_size, p_shift, perc_move[0] , True)
                                ),
                           'zoom_in': zoom_breakpoint( p_size, p_shift, perc_zoom, True),
                           'zoom_out': zoom_breakpoint( p_size, p_shift, perc_zoom, False),
                           'get_url':  get_url
            })


def browser(request, p_id,  p_chrom = None, p_start = None, p_end = None):

    perc_move = (0.5, 0.25)
    perc_zoom = 1.25

    p_plot = Plot.objects.get(id = p_id)

    p_columns_dict = p_plot.getColumnsDict()
    
    c_chrom, c_start, c_end, c_interval_start, c_interval_end = getPlotCookie(request, p_id)

    if p_chrom is None:
        p_chrom = c_chrom
        p_start = c_start
        p_end = c_end


    p_name_filters = sorted(p_plot.getNameFilters(p_chrom, p_start, p_end))
    name_filter = ''
    get_url = ''
    results = ''

    if request.method == 'GET': 

        search_text = request.GET.get('search_text', '')
        name_filter = request.GET.get('name_filter', '')
        interval_start = request.GET.get('interval_start', c_interval_start or '')
        interval_end = request.GET.get('interval_end', c_interval_end or '')

        p_interval_start = request.GET.get('interval_start', c_interval_start)
        p_interval_end = request.GET.get('interval_end', c_interval_end)

        setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)

        region_or_err_msg = get_region_or_err_msg(search_text, p_id)

        if len(region_or_err_msg) == 3:
            p_chrom, p_start, p_end = region_or_err_msg
        elif search_text  == '':
            pass
        else:
            messages.error(request, region_or_err_msg) 

        get_url = '?' +  urlencode({'name_filter':  name_filter, 
                                    'interval_start': interval_start, 
                                    'interval_end': interval_end}, quote_via=quote_plus)


        if p_plot.hasEval() and p_interval_start is not None and p_interval_end is not None and  p_interval_start != '' and p_interval_end != '':
            results = ranking(p_plot.eval, p_chrom, p_interval_start, p_interval_end)

    else:
        pass

    return TemplateResponse(request, 'tadeus/browser.html', {'p_id': p_id, 
                           'p_plot': p_plot,
                           'p_name_filters': p_name_filters,
                           'p_columns_dict': p_columns_dict,
                           'p_cols': len(p_columns_dict,),
                           'p_chrom': p_chrom, 
                           'p_start': p_start, 
                           'p_end': p_end,
                           'name_filter': name_filter,
                           'move': ( move( p_start, p_end, perc_move[0] , False), 
                                     move( p_start, p_end, perc_move[1] , False),
                                     move( p_start, p_end, perc_move[1] , True),
                                     move( p_start, p_end, perc_move[0] , True)
                                ),
                           'zoom_in': zoom( p_start, p_end, perc_zoom, True),
                           'zoom_out': zoom( p_start, p_end, perc_zoom, False),
                           'region_len': p_end - p_start,
                           'get_url':  get_url,
                           'results': results,
                           'interval_start': interval_start,
                           'interval_end': interval_end
            })

def image(request, p_cols, p_id, p_chrom, p_start, p_end, p_breakpoint_id = None, p_left_side = None, p_width_prop = None):
    
    p_start = int(p_start)

    track = Track.objects.get(id = p_id)
    breakpoint = None

    p_name_filter = None

    if request.method == 'GET': 
        name_filter = request.GET.get('name_filter', None)
        interval_start = request.GET.get('interval_start', '')

        if interval_start:
            interval_start = int(interval_start)

        interval_end = request.GET.get('interval_end', '')

        if interval_end:
            interval_end = int(interval_end)

        if p_breakpoint_id:
            breakpoint = Breakpoint.objects.get(id = p_breakpoint_id)

        breakpoint_coordinates = {}
        breakpoint_coordinates['left_start'] = int(request.GET.get('left_start', '-1'))
        breakpoint_coordinates['left_end'] = int(request.GET.get('left_end', '-1'))
        breakpoint_coordinates['right_start'] = int(request.GET.get('right_start', '-1'))
        breakpoint_coordinates['right_end'] = int(request.GET.get('right_end', '-1'))

    fig = track.draw_track(p_cols, chrom = p_chrom, start = p_start, end = p_end, 
        interval_start = interval_start, interval_end = interval_end, name_filter = name_filter,  
        breakpoint = breakpoint, left_side = p_left_side, 
        width_prop = p_width_prop, breakpoint_coordinates = breakpoint_coordinates)

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    return HttpResponse(buf, content_type="image/png")



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
    tracks = plot.tracks.all().order_by('column', 'no','id')
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


def datasources(request):

    track_files = TrackFile.objects.filter( ~Q(file_type= 'XA'),
                                            only_public_or_user(request),
                                            Q(eval__isnull=True) ).order_by('owner', 'assembly', 'file_type', 'name', 'id')

    f = TrackFileFilter(request.GET, queryset=track_files)
    table = TrackFileTable(f.qs)

    RequestConfig(request).configure(table)
    return render(request, 'tadeus/datasources.html', {'table': table, 'filter': f})



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
                   'file_sub_type': track.get_file_sub_type(),
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
        form = CreateTrackForm(initial={'no': track_number, 'column': 1})

    track_files = TrackFile.objects.filter(Q(assembly = plot.assembly), only_public_or_user(request), Q(eval__isnull=True)).order_by(Lower('name'),'id')

    return render(request, 'tadeus/add_track.html', {'form': form, 'p_plot_id': p_plot_id, 'track_files': track_files, 'plot': plot })

def edit_datasource(request, p_id):
    
    track_file = TrackFile.objects.get(pk = p_id)

    if request.method == 'POST':
        form = TrackFileForm(request.POST, instance = track_file)

        if form.is_valid():
            track_file = form.save()
            messages.success(request, 'Data source successfully saved.')
        else:
            messages.error(request, 'Data was NOT successfully saved.')            

            print(form['assembly'].errors)
            
    else:
        form = TrackFileForm(instance = track_file)

    return render(request, 'tadeus/datasource.html', {'form': form,  
                                                         'assemblies': Assembly.objects.all(),
                                                         'p_id': p_id,
                                                         'datasource_br': track_file.name,
                                                         'readonly': is_object_readonly(request, track_file )})


def delete_datasource(request, p_id):

    try: 
        track_file = TrackFile.objects.get(pk =p_id)
        track_file.delete()

        messages.success(request, 'Data source successfully deleted.')
    except ProtectedError:
        messages.error(request, 'You cannot delete this data source. It is used in a plot.')
        return redirect(edit_datasource, p_id= p_id)

    return redirect(datasources)


def save_datasource(track_file, file_handle, eval = False):

    if file_handle:
        reader = BedOrBedGraphReader(file_handle = file_handle, track_file = track_file)

    track_file.save()


    if file_handle:
        for bed_entry in reader: 

            if eval:
                bed_entry.set_eval_pvalue()

            bed_entry.save()


@transaction.atomic
def save_datasource_atomic(track_file, file_handle):
    save_datasource(track_file, file_handle)


def  get_file_handle(p_type, form):

    if p_type == 'file':
        f = form.files['file']
        return  TextIOWrapper(f.file)            
    elif p_type == 'text' :
        text = form.data['text']
        if len(text) == 0:
            raise ReadBedOrBedGraphException('Paste in data in BED or BEDGraph format.')
        return StringIO(text)
    else:
        return None


def create_datasource(request, p_type):
    
    if request.method == 'POST':
        form = TrackFileForm(request.POST, request.FILES)

        if form.is_valid():

            try:

                track_file = form.save(commit = False)
                set_owner_or_cookie(request, track_file)
                file_handle =  get_file_handle(p_type, form)
                save_datasource_atomic(track_file, file_handle)
            
                messages.success(request, "Data source '{}' successfully created.".format(track_file.name))

                return redirect(edit_datasource, p_id = track_file.id)

            except ReadBedOrBedGraphException as exp:
                messages.error(request, exp)   

    else:
        form = TrackFileForm()

    return render(request, 'tadeus/datasource.html', {'form': form,  'assemblies': Assembly.objects.all(), 'p_type': p_type, 'p_id': None})

def index(request):
    evals = Eval.objects.filter(owner__username = 'root') 
    table = EvalTable(evals)
    RequestConfig(request).configure(table)

    return render(request, 'tadeus/index.html', {'table': table })

def evals(request):
    table = None
    f = None

    auth_cookie = get_auth_cookie(request)
    print(auth_cookie)

    if request.user.is_authenticated:
        evals = Eval.objects.filter(owner = request.user)
    else:
        evals = Eval.objects.filter(auth_cookie = auth_cookie)

    if evals:

        table = EvalTable(evals)

        f = EvalFilter(request.GET, queryset=evals)
        table = EvalTable(f.qs)

        RequestConfig(request).configure(table)

    return render(request, 'tadeus/evals.html', {'table': table, 'filter':  f })

@transaction.atomic
def create_eval_atomic(request, form, p_type):
    track_file = TrackFile()

    set_owner_or_cookie(request, track_file)

    assembly = form.instance.assembly
    track_file.assembly = assembly
    track_file.save()

    file_handle = get_file_handle(p_type, form)

    eval = form.save(commit = False)

    set_owner_or_cookie(request, eval)

    eval.track_file =  track_file 

    columns = ( ( 1, 10001, 40, 6, ),)

    plot = Plot(assembly = assembly)

    set_owner_or_cookie(request, plot)

    plot.title = 'Plot for evaluation \''  + form.cleaned_data['name'] + '\''
    plot.name = 'Plot for evaluation \''  + form.cleaned_data['name'] + '\''
    plot.save()
    
    for i, column in enumerate(columns):
        for j, track_id in enumerate(column): 

            if j == 0:
                 track = Track(plot = plot, 
                              track_file = TrackFile.objects.get(pk = track_id), 
                              no = (j + 1) * 10)               

            if j == 1:
                track = Track(plot = plot, 
                              track_file = TrackFile.objects.get(pk = track_id), 
                              no = (j + 1) * 10,
                              domains_file  = TrackFile.objects.get(pk = 10101))
            if j == 2:
                track = Track(plot = plot, 
                        track_file = TrackFile.objects.get(pk = track_id), 
                        name_filter = True, 
                        no = (j + 1) * 10, style = 'arcs')

            if j == 3:
                track = Track(plot = plot, 
                        track_file = TrackFile.objects.get(pk = track_id), 
                        no = (j + 1) * 10, style = 'tiles',
                        min_value = 0,
                        max_value = 1
                        )

            track.save()
    
    eval.plot = plot
    save_datasource(track_file, file_handle, eval = True)    
    eval.save()

    return eval


def create_eval(request, p_type):

    if request.method == 'POST':
        form = EvalForm(request.POST, request.FILES)

        if form.is_valid():

            try:
                eval = create_eval_atomic(request, form, p_type)

                messages.success(request, "Successful evaluation.")

                return redirect(edit_eval, p_id = eval.id)

            except ReadBedOrBedGraphException as exp:
                messages.error(request, exp)   
    else:
        form = EvalForm()

    return render(request, 'tadeus/eval.html', {'form': form,  'assemblies': Assembly.objects.all(), 'p_type': p_type, 'p_id': None})

def edit_eval(request, p_id):
    
    eval = Eval.objects.get(pk = p_id)

    table = EvalEntryTable( eval.track_file.file_entries.all(), eval.plot.id)

    RequestConfig(request).configure(table)

    if request.method == 'POST':
        form = EvalForm(request.POST, instance = eval)

        if form.is_valid():
            eval = form.save()
            messages.success(request, 'Data source successfully saved.')
        else:
            print(form.errors)
            messages.error(request, 'Data was NOT successfully saved.')  
            
    else:
        form = TrackFileForm(instance = eval)

    return render(request, 'tadeus/eval.html', {'form': form,  
                                                 'p_id': p_id,
                                                 'assembly_name': eval.track_file.assembly.name , 
                                                 'eval_br': eval.name,
                                                 'table': table })

@transaction.atomic
def delete_eval(request, p_id):

    eval = Eval.objects.get(pk =p_id)

    eval.delete()

    eval.plot.delete()
    eval.track_file.delete()

    messages.success(request, "Evaluation of SVs '{}' successfully deleted.".format(eval.name))

    return redirect(evals)


def show_eval(request, p_id):

    eval = Eval.objects.get(pk =p_id) 

    tracks = eval.plot.getTracks()
 
    file_entries = split_seq(eval.track_file.file_entries.all(), 2)

    return render(request, 'tadeus/eval_show.html', {'p_id': p_id, 'tracks': tracks, 'file_entries' : file_entries} )


def add_entry_eval(request, p_id):

    eval = Eval.objects.get(pk =p_id) 

    chroms = eval.assembly.chromosomes.all()

    if request.method == 'POST':
        form = EvalAddEntryForm(request.POST)

        if form.is_valid():
            bed_file_entry = form.save(commit = False)
            bed_file_entry.track_file  = eval.track_file

            bed_file_entry.set_eval_pvalue()
            bed_file_entry.save()
            messages.success(request, "Breakpoint '{}' added to evaluation.".format(bed_file_entry.name))

            return redirect(edit_eval, p_id = eval.id)

        else:
            messages.error(request, 'Data was NOT successfully saved.')  
    else:
        form = EvalAddEntryForm()

    return render(request, 'tadeus/eval_add_entry.html', {'p_id': p_id, 'chroms': chroms , 'form': form} )


def phenotypes(request, p_db):

    phenotypes = Phenotype.objects.filter(db = p_db).order_by('pheno_id')

    f = PhenotypeFilter(request.GET, queryset = phenotypes)
    table = PhenotypeTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'tadeus/phenotypes.html', {'table': table, 'filter': f, 'db' : p_db })


def genes(request):

    genes = Gene.objects.all().order_by('name')

    f = GeneFilter(request.GET, queryset = genes)
    table = GeneTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'tadeus/genes.html', { 'table': table, 'filter': f})


def gene(request,p_id):

    gene = Gene.objects.get(pk=p_id)

    phenotypes = gene.phenotypes.all()
    f = PhenotypeFilter(request.GET, queryset = phenotypes)
    table = PhenotypeTable(f.qs)

    RequestConfig(request).configure(table)

    return render(request, 'tadeus/gene.html', {'table': table,'filter': f, 'gene':gene })

def breakpoints(request):

    breakpoints = Breakpoint.objects.all()

    if request.method == 'GET': 
        min_range = request.GET.get('min_range')
        max_range = request.GET.get('max_range')
        chrom = request.GET.get('chrom')


    print(min_range)
    print(max_range)
    print(chrom)

    q_left = Q()
    q_right = Q()

    if chrom:
        q_left &= Q(left_chrom__name__iexact = chrom)
        q_right &= Q(right_chrom__name__iexact = chrom)
    if min_range:
        q_left &= Q(left_coord__gte = min_range)
        q_right &= Q(right_coord__gte = min_range)
    if max_range:
        q_left &= Q(left_coord__lte = max_range)
        q_right &= Q(right_coord__lte = max_range)

    f =  BreakpointFilter(request.GET, queryset = breakpoints.filter(q_left | q_right))
    table =  BreakpointTable(f.qs)

    RequestConfig(request).configure(table)

    samples = Sample.objects.all().order_by('name', 'id')

    return render(request, 'tadeus/breakpoints.html', {'table': table,'filter': f, 'samples': samples })