from scipy.stats import geom

from datasources import TrackFile

from .defaults import ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID, TRANSLOCATION


def get_TADeusScore(sv_entry):

    enh_prom_file = TrackFile.objects.get(pk=ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID)

    n1 = len([1 for enh_prom in enh_prom_file.get_entries(sv_entry.chrom, sv_entry.start, sv_entry.start)])
    n2 = len([1 for enh_prom in enh_prom_file.get_entries(sv_entry.chrom, sv_entry.end, sv_entry.end)])

    return get_pvalue(max(n1, n2))


def get_pvalue(n, theta=0.09241035129185671, p=0.011742364113774086):

    if n == 0:
        return 1 - theta

    return 1 - (theta + (1 - theta) * geom.cdf(n, p, loc=0))


def annotate_cnvs_TADeusScore(sv_entries):

    for sv_entry in sv_entries:
        if sv_entry.sv_type == TRANSLOCATION:
            sv_entry.TADeus_score = get_TADeusScore(sv_entry)
