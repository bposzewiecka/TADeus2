from django.shortcuts import render

from django.db import transaction

from tadeus_portal.utils import  get_auth_cookie

from .models import Evaluation
from .forms import EvaluationForm

from datasources.models import Assembly

def index(request):
    table = None
    f = None

    auth_cookie = get_auth_cookie(request)

    if request.user.is_authenticated:
        evals = Evaluation.objects.filter(owner = request.user)
    else:
        evals = Evaluation.objects.filter(auth_cookie = auth_cookie)

    if evals:

        table = EvalTable(evals)

        f = EvalFilter(request.GET, queryset=evals)
        table = EvalTable(f.qs)

        RequestConfig(request).configure(table)

    return render(request, 'evaluation/evaluations.html', {'table': table, 'filter':  f })

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


def create(request, p_type):

    if request.method == 'POST':
        form = EvaluationForm(request.POST, request.FILES)

        if form.is_valid():

            try:
                eval = create_eval_atomic(request, form, p_type)

                messages.success(request, "Successful evaluation.")

                return redirect(edit_eval, p_id = eval.id)

            except ReadBedOrBedGraphException as exp:
                messages.error(request, exp)   
    else:
        form = EvaluationForm()

    return render(request,'evaluation/evaluation.html', {'form': form,  'assemblies': Assembly.objects.all(), 'p_type': p_type, 'p_id': None})

def edit(request, p_id):
    
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

    return render(request, 'evaluation/evaluation.html', {'form': form,  
                                                 'p_id': p_id,
                                                 'assembly_name': eval.track_file.assembly.name , 
                                                 'eval_br': eval.name,
                                                 'table': table })

@transaction.atomic
def delete(request, p_id):

    eval = Eval.objects.get(pk =p_id)

    eval.delete()

    eval.plot.delete()
    eval.track_file.delete()

    messages.success(request, "Evaluation of SVs '{}' successfully deleted.".format(eval.name))

    return redirect(evals)


def show(request, p_id):

    eval = Eval.objects.get(pk =p_id) 

    tracks = eval.plot.getTracks()
 
    file_entries = split_seq(eval.track_file.file_entries.all(), 2)

    return render(request, 'evaluation/eval_show.html', {'p_id': p_id, 'tracks': tracks, 'file_entries' : file_entries} )


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

    return render(request, 'evaluation/eval_add_entry.html', {'p_id': p_id, 'chroms': chroms , 'form': form} )



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

    return results    
