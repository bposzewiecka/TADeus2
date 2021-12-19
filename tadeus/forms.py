from django import forms

from datasources.models import Chromosome
from evaluation.defaults import DELETION, DUPLICATION

"""
class CNVForm(forms.Form):
    cnv_type = forms.CharField(max_length=1)
    chrom =
    start_coordinate = forms.IntegerField()
    end_coordinate = forms.IntegerField()
"""

TRANSLOCATION_DIRECTIONS_HEAD = "H"
TRANSLOCATION_DIRECTIONS_TAIL = "T"

TRANSLOCATION_DIRECTIONS = (
    (TRANSLOCATION_DIRECTIONS_HEAD, "Head"),
    (TRANSLOCATION_DIRECTIONS_TAIL, "Tail"),
)


CNV_TYPES = ((DELETION, "Deletion"), (DUPLICATION, "Duplication"))


def get_chromosomes():
    return [(chrom.name, chrom.name) for chrom in Chromosome.objects.filter(assembly__name="hg38")]


class TranslocationForm(forms.Form):

    chrom1 = forms.ChoiceField(choices=get_chromosomes)
    coordinate1 = forms.IntegerField()
    direction1 = forms.ChoiceField(choices=TRANSLOCATION_DIRECTIONS)
    chrom2 = forms.ChoiceField(choices=get_chromosomes)
    coordinate2 = forms.IntegerField()
    direction2 = forms.ChoiceField(choices=TRANSLOCATION_DIRECTIONS)


class CNVForm(forms.Form):
    cnv_type = forms.ChoiceField(choices=CNV_TYPES)
    chrom = forms.ChoiceField(choices=get_chromosomes)
    start_coordinate = forms.IntegerField()
    end_coordinate = forms.IntegerField()
