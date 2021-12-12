from collections import Counter

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig

from datasources.defaults import FILE_TYPE_XAXIS
from datasources.forms import TrackFileForm
from datasources.models import Assembly, TrackFile
from datasources.readBed import ReadBedOrBedGraphException
from datasources.views import get_file_handle
from ontologies.models import Gene
from plots.models import Plot
from tadeus_portal.utils import get_auth_cookie, set_owner_or_cookie, split_seq
from tracks.defaults import BED_DISPLAY_ARCS, BED_DISPLAY_TILES, HIC_DISPLAY_HIC, TRANSFORM_LOG1P
from tracks.models import Track

from .ClassifyCNV import annotate_cnvs_ClassifyCNV
from .defaults import (
    BIOMART_GENES_FILE_ID,
    CLINGEN_FILE_ID,
    ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID,
    HIC_NA12787_FILE_ID,
    HIC_NA12787_TADS_FILE_ID,
    PLI_SCORE_FILE_ID,
)
from .forms import EvaluationAddEntryForm, EvaluationForm
from .models import Evaluation, SVEntry
from .tables import EvaluationEntryTable, EvaluationFilter, EvaluationTable
from .TADA import annotate_cnvs_TADA
from .TADeusScore import annotate_translocations_TADeusScore


def index(request):
    table = None
    f = None

    auth_cookie = get_auth_cookie(request)

    if request.user.is_authenticated:
        evals = Evaluation.objects.filter(owner=request.user)
    else:
        evals = Evaluation.objects.filter(auth_cookie=auth_cookie)

    if evals:

        table = EvaluationTable(evals)

        f = EvaluationFilter(request.GET, queryset=evals)
        table = EvaluationTable(f.qs)

        RequestConfig(request).configure(table)

    return render(request, "evaluation/evaluations.html", {"table": table, "filter": f})


@transaction.atomic
def create_eval_atomic(request, form, p_type):
    track_file = TrackFile()

    set_owner_or_cookie(request, track_file)

    assembly = form.instance.assembly
    track_file.assembly = assembly
    track_file.save()

    file_handle = get_file_handle(p_type, form)

    eval = form.save(commit=False)

    set_owner_or_cookie(request, eval)

    eval.track_file = track_file

    tracks = (
        (TrackFile.objects.get(assembly=Assembly.objects.get(name="hg38"), file_type=FILE_TYPE_XAXIS).id, {"title": "XAxis"}),
        (
            HIC_NA12787_FILE_ID,
            {
                "domains_file": TrackFile.objects.get(pk=HIC_NA12787_TADS_FILE_ID),
                "title": "HiC Track",
                "hic_display": HIC_DISPLAY_HIC,
                "transform": TRANSFORM_LOG1P,
            },
        ),
        (
            ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID,
            {"bed_display": BED_DISPLAY_ARCS, "name_filter": True, "title": "Enhancers-promoters interactions"},
        ),
        (PLI_SCORE_FILE_ID, {"bed_display": BED_DISPLAY_TILES, "min_value": 0, "max_value": 1, "title": "Genes coloured by pLI score"}),
    )

    plot = Plot(assembly=assembly)

    set_owner_or_cookie(request, plot)

    plot.title = "Plot for evaluation '" + form.cleaned_data["name"] + "'"
    plot.name = "Plot for evaluation '" + form.cleaned_data["name"] + "'"
    plot.save()

    for j, (track_id, params) in enumerate(tracks):
        track = Track(plot=plot, track_file=TrackFile.objects.get(pk=track_id), no=(j + 1) * 10, **params)
        track.save()

    eval.plot = plot
    sv_entries = track_file.read_bed(file_handle, return_svs=True)
    eval.save()

    annotate_sv_entries(sv_entries, eval.id, request)

    return eval


def create(request, p_type):

    if request.method == "POST":
        form = EvaluationForm(request.POST, request.FILES)

        if form.is_valid():

            try:
                eval = create_eval_atomic(request, form, p_type)

                messages.success(request, "Successful evaluation.")

                return redirect("evaluation:update", p_id=eval.id)

            except ReadBedOrBedGraphException as exp:
                messages.error(request, exp)
    else:
        form = EvaluationForm()

    return render(request, "evaluation/evaluation.html", {"form": form, "assemblies": Assembly.objects.all(), "p_type": p_type, "p_id": None})


def update(request, p_id):

    eval = Evaluation.objects.get(pk=p_id)

    # sv_entries_id = [ file_entry.id for file_entry in eval.track_file.subtracks.all()[0].datasources_bedfileentry_file_entries.all()]
    sv_entries = SVEntry.objects.filter(subtrack__in=eval.track_file.subtracks.all())

    table = EvaluationEntryTable(sv_entries, eval.plot.id)

    RequestConfig(request).configure(table)

    if request.method == "POST":
        form = EvaluationForm(request.POST, instance=eval)

        if form.is_valid():
            eval = form.save()
            messages.success(request, "Data source successfully saved.")
        else:
            messages.error(request, "Data was NOT successfully saved.")

    else:
        form = TrackFileForm(instance=eval)

    return render(request, "evaluation/evaluation.html", {"form": form, "p_id": p_id, "evaluation": eval, "table": table})


@transaction.atomic
def delete(request, p_id):

    eval = Evaluation.objects.get(pk=p_id)

    eval.delete()

    eval.plot.delete()
    eval.track_file.delete()

    messages.success(request, f"Evaluation of SVs '{eval.name}' successfully deleted.")

    return redirect("evaluation:index")


def show(request, p_id):

    eval = Evaluation.objects.get(pk=p_id)

    tracks = eval.plot.getTracks()

    file_entries = split_seq(eval.track_file.file_entries.all(), 2)

    return render(request, "evaluation/eval_show.html", {"p_id": p_id, "tracks": tracks, "file_entries": file_entries})


def add_entry(request, p_id):

    eval = Evaluation.objects.get(pk=p_id)

    chroms = eval.assembly.chromosomes.all()

    if request.method == "POST":
        form = EvaluationAddEntryForm(request.POST)

        if form.is_valid():
            sv_entry = form.save(commit=False)
            sv_entry.subtrack = eval.track_file.subtracks.all()[0]

            annotate_sv_entries([sv_entry], p_id, request)
            sv_entry.save()

            messages.success(request, f"Breakpoint '{sv_entry.name}' added to evaluation.")

            return redirect("evaluation:update", p_id=eval.id)

        else:
            messages.error(request, "Data was NOT successfully saved.")
    else:
        form = EvaluationAddEntryForm()

    return render(request, "evaluation/evaluation_add_entry.html", {"p_id": p_id, "chroms": chroms, "form": form})


def delete_entry(request, p_id):

    sv_entry = SVEntry.objects.get(pk=p_id)
    eval = sv_entry.subtrack.track_file.eval

    sv_entry.delete()

    messages.success(request, "SV successfully deleted.")

    return redirect("evaluation:update", p_id=eval.id)


def ranking(eval, p_chrom, p_interval_start, p_interval_end):
    return []
    p_interval_start, p_interval_end = int(p_interval_start), int(p_interval_end)

    region_start = max(p_interval_start - 3 * 1000 * 1000, 0)
    region_end = p_interval_end + 3 * 1000 * 1000

    gene_file = TrackFile.objects.get(pk=BIOMART_GENES_FILE_ID)

    genes = gene_file.get_entries(p_chrom, region_start, region_end)

    genes = {gene.name: {"gene": Gene.objects.get(pk=gene.id)} for gene in genes}

    pLI_file = TrackFile.objects.get(pk=PLI_SCORE_FILE_ID)
    pLI = {gene.name.upper(): gene.score for gene in pLI_file.get_entries(p_chrom, region_start, region_end)}

    clingen_file = TrackFile.objects.get(pk=CLINGEN_FILE_ID)
    clingen = {gene.name: gene.score for gene in clingen_file.get_entries(p_chrom, region_start, region_end)}

    enh_prom_file = TrackFile.objects.get(pk=ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID)
    enh_proms = [enh_prom.name.upper() for enh_prom in enh_prom_file.get_entries(p_chrom, p_interval_start, p_interval_end)]
    enh_proms = Counter(enh_proms)

    for gene_name, d in genes.items():
        d["enh_prom"] = enh_proms[gene_name]

    # enh_prom_scores = [gene["enh_prom"] for gene in genes.values()]

    for gene_name, d in genes.items():
        gene = d["gene"]
        d["gene_name"] = gene_name

        d["clingen"] = clingen.get(gene_name, None)
        d["clingen_score"] = 100 if clingen.get(gene_name, 0) in (3, 2, 30) else 0

        d["pLI"] = pLI.get(gene_name, None)

        d["distance"] = None

        d["distance"] = min(abs(p_interval_start - gene.start), abs(p_interval_end - gene.end))

        if d["distance"] < 1 * 1000 * 1000:
            d["distance_1Mb_score"] = 100
        else:
            d["distance_1Mb_score"] = 0

        d["phenotypes"] = gene.phenotypes.order_by("name", "pheno_id")

        if d["phenotypes"]:
            d["phenotype_score"] = 100
        else:
            d["phenotype_score"] = 0

        if enh_proms[gene_name]:
            d["enh_prom_score"] = 100
        else:
            d["enh_prom_score"] = 0

        d["rank"] = d["clingen_score"] + d["enh_prom_score"] + d["phenotype_score"] + d["distance_1Mb_score"]

    results = list(genes.items())
    results.sort(key=lambda x: (-x[1]["rank"], -x[1]["enh_prom"], x[1]["distance"], x[1]["gene_name"]))

    return results


def annotate_sv_entries(sv_entries, p_id, request):

    try:
        annotate_cnvs_TADA(sv_entries, p_id)
    except Exception:
        messages.error(request, "Error in TADA annotation.")

    try:
        annotate_cnvs_ClassifyCNV(sv_entries, p_id)
    except Exception:
        messages.error(request, "Error in ClassifyCNV annotation.")

    try:
        annotate_translocations_TADeusScore(sv_entries)
    except Exception:
        messages.error(request, "Error in TADeus annotation.")
