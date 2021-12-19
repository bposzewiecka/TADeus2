from django.contrib.auth.models import User
from django.db import transaction

from datasources.defaults import FILE_TYPE_XAXIS
from datasources.models import Assembly, Chromosome, TrackFile
from evaluation.defaults import HIC_NA12787_FILE_ID, HIC_NA12787_TADS_FILE_ID, NCBI_REFSEQ_FUNCTIONAL_ELEMENTS_FILE_ID, PLI_SCORE_FILE_ID
from plots.models import Plot
from tracks.defaults import BED_DISPLAY_TILES, HIC_DISPLAY_HIC, HIC_DISPLAY_VIRTUAL4C, TRANSFORM_LOG1P
from tracks.models import Track


@transaction.atomic
def create_translocation_case_study():

    chr6 = Chromosome.objects.get(name="chr6", assembly__name="hg38")
    chr14 = Chromosome.objects.get(name="chr14", assembly__name="hg38")

    assembly = Assembly.objects.get(name="hg38")

    tracks = (
        (TrackFile.objects.get(assembly=assembly, file_type=FILE_TYPE_XAXIS).id, {"title": "XAxis"}),
        (
            HIC_NA12787_FILE_ID,
            {
                "domains_file": TrackFile.objects.get(pk=HIC_NA12787_TADS_FILE_ID),
                "title": "Hi-C map",
                "hic_display": HIC_DISPLAY_HIC,
                "transform": TRANSFORM_LOG1P,
            },
        ),
        (
            HIC_NA12787_FILE_ID,
            {
                "title": "Virtual 4C FOXG1",
                "hic_display": HIC_DISPLAY_VIRTUAL4C,
                "chromosome": chr14,
                "start_coordinate": 28765286,
                "end_coordinate": 28767086,
            },
        ),
        (
            HIC_NA12787_FILE_ID,
            {
                "title": "Virtual 4C BMP6",
                "hic_display": HIC_DISPLAY_VIRTUAL4C,
                "chromosome": chr6,
                "start_coordinate": 7724598,
                "end_coordinate": 7724598,
            },
        ),
        (
            NCBI_REFSEQ_FUNCTIONAL_ELEMENTS_FILE_ID,
            {
                "title": "Validated enhancers",
            },
        ),
        (PLI_SCORE_FILE_ID, {"bed_display": BED_DISPLAY_TILES, "min_value": 0, "max_value": 1, "title": "pLI score"}),
    )

    plot = Plot(id=1, assembly=assembly)

    plot.title = "Case study of a patient with a balanced translocation 46,XX,t(6;14)(p25.1;q12)."
    plot.name = plot.title
    plot.public = True
    plot.owner = User.objects.get(username="admin")
    plot.save()

    for j, (track_id, params) in enumerate(tracks):
        track = Track(plot=plot, track_file=TrackFile.objects.get(pk=track_id), no=(j + 1) * 10, **params)
        track.save()


globals().update(locals())


create_translocation_case_study()
