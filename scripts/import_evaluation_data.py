from django.contrib.auth.models import User
from django.db import transaction

from datasources.models import Assembly, FileEntryPropertyType, TrackFile
from evaluation.defaults import CLINGEN_FILE_ID, DECIPHER_HAPLOINSUFFICENCY_FILE_ID, ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID, PLI_SCORE_FILE_ID

hg19 = Assembly.objects.get(name="hg19")
admin = User.objects.get(username="admin")


def save_xaxis():

    xa = TrackFile(id=1, assembly=hg19, name="XAxis", source_name="XAxis", file_type="XA", bed_sub_type=None, owner=admin, public=True, approved=True)

    xa.save()


@transaction.atomic
def save_genes():

    """
    ucsc_genes = TrackFile(
        id=3,
        assembly=hg19,
        name="UCSC Genes - knownGene",
        source_name="hgTables - UCSC genome browser",
        source_url="https://genome.ucsc.edu/cgi-bin/hgTables",
        file_type="BE",
        bed_sub_type="Bed12",
        owner=admin,
        public=True,
        approved=True,
    )
    """

    # ucsc_genes.save()
    # ucsc_genes.add_subtrack('data/hg19/genes/UCSCGenes.bed')

    """
    refseq_genes = TrackFile(
        id=4,
        assembly=hg19,
        name="RefSeq Genes - refGene",
        source_name="hgTables - UCSC genome browser",
        source_url="https://genome.ucsc.edu/cgi-bin/hgTables",
        file_type="BE",
        bed_sub_type="Bed12",
        owner=admin,
        public=True,
        approved=True,
    )
    """

    # refseq_genes.save()
    # refseq_genes.add_subtrack(file_path = 'data/hg19/genes/refSeqGenes.bed')

    haploinsufficient_genes = TrackFile(
        id=DECIPHER_HAPLOINSUFFICENCY_FILE_ID,
        assembly=hg19,
        name="DECIPHER Haploinsufficiency Predictions Version 3",
        source_name="DECIPHER project",
        source_url="https://decipher.sanger.ac.uk/about#downloads/data",
        file_type="BE",
        bed_sub_type="Bed6",
        owner=admin,
        public=True,
        approved=True,
    )

    haploinsufficient_genes.save()
    haploinsufficient_genes.add_subtrack("data/hg38/genes/HI_Predictions_Version3.bed6")

    pli_genes = TrackFile(
        id=PLI_SCORE_FILE_ID,
        assembly=hg19,
        name="pLI score",
        source_name="http://exac.broadinstitute.org/",
        source_url="ftp://ftp.broadinstitute.org/pub/ExAC_release/release1/manuscript_data/",
        file_type="BE",
        bed_sub_type="Bed6",
        owner=admin,
        public=True,
        approved=True,
    )

    pli_genes.save()
    pli_genes.add_subtrack("data/hg38/genes/forweb_cleaned_exac_r03_march16_z_data_pLI.bed6")

    clingen_genes = TrackFile(
        id=CLINGEN_FILE_ID,
        assembly=hg19,
        name="ClinGen Haploinsufficency Genes",
        source_name="ClinGen Dosage Sensitivity Map",
        source_url="https://ftp.clinicalgenome.org/ClinGen_haploinsufficiency_gene_GRCh38.bed",
        file_type="BE",
        bed_sub_type="Bed6",
        owner=admin,
        public=True,
        approved=True,
    )

    clingen_genes.save()
    clingen_genes.add_subtrack("data/hg38/genes/ClinGen_haploinsufficiency_gene_GRCh38.bed6")


@transaction.atomic
def save_enh_prom():

    refseq_genes = TrackFile(
        id=ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID,
        assembly=hg19,
        name="ENCODE distal DHS/enhancer-promoter connections",
        source_name="The accessible chromatin landscape of the human genome",
        source_url="",
        file_type="BE",
        bed_sub_type="Bed6",
        owner=admin,
        public=True,
        approved=True,
    )

    refseq_genes.save()
    refseq_genes.add_subtrack("data/hg19/enhancers/hi_score_enh_promoter.bed")


@transaction.atomic
def save_hic():

    pass
    # hi = TrackFile(
    #    id=no + 1,
    #    assembly=hg19,
    #    name=name.format(tissue=tissue),
    #    source_name=source_name.format(tissue=tissue, resolution="{resolution}"),
    #    source_url=source_url,
    #    reference=reference,
    #    file_type="HI",
    #    file_sub_type=None,
    #    owner=admin,
    #    public=True,
    #    approved=True,
    #    file_path=file_path.format(tissue=tissue, resolution="{resolution}"),
    # )


BOUNDARY_DISTANCE_ID = 1
BOUNDARY_DISTANCE_LABEL = "Boundary Distance"
BOUNDARY_STABILITY = 2
BOUNDARY_STABILITY_LABEL = "Boundary Stability"
GENE_DISTANCE = 3
GENE_DISTANCE_LABEL = "Gene Distance"
ENHANCER_DISTANCE = 4
ENHANCER_DISTANCE_LABEL = "Enhancer Distance"
DDG2P_DISTANCE = 5
DDG2P_DISTANCE_LABEL = "DDG2P Distance"
GENE_LOEUF = 6
GENE_LOEUF_LABEL = "Gene LOEUF"
ENHANCER_CONSERVATION = 7
ENHANCER_CONSERVATION_LABEL = "Enhancer conservation"
GENE_HI = 8
GENE_HI_LABEL = "Gene HI"
CTCF_DISTANCE = 9
CTCF_DISTANCE_LABEL = "CTCF Distance"
HI_LOGODDS_SCORE = 10
HI_LOGODDS_SCORE_LABEL = "HI LogOdds Score"
EXON_OVERLAP = 11
EXON_OVERLAP_LABEL = ("Exon Overlap",)
MPOI = 12
MPOI_LABEL = "MPOI"
PATHOGENICITY_SCORE = 13
PATHOGENICITY_SCORE_LABEL = "Pathogenicity Score"
PATHOGENICITY_LABEL = 14
PATHOGENICITY_LABEL_LABEL = "Pathogenicity Label"
TADEUS_PATHOGENICITY_SCORE = 15
TADEUS_PATHOGENICITY_SCORE_LABEL = "TADeus Pathogenicity Score"


def add_file_entry_property_types():

    for id, name in (
        (BOUNDARY_DISTANCE_ID, BOUNDARY_DISTANCE_LABEL),
        (BOUNDARY_STABILITY, BOUNDARY_STABILITY_LABEL),
        (GENE_DISTANCE, GENE_DISTANCE_LABEL),
        (ENHANCER_DISTANCE, ENHANCER_DISTANCE_LABEL),
        (DDG2P_DISTANCE, DDG2P_DISTANCE_LABEL),
        (GENE_LOEUF, GENE_LOEUF_LABEL),
        (ENHANCER_CONSERVATION, ENHANCER_CONSERVATION_LABEL),
        (GENE_HI, GENE_HI_LABEL),
        (CTCF_DISTANCE, CTCF_DISTANCE_LABEL),
        (HI_LOGODDS_SCORE, HI_LOGODDS_SCORE_LABEL),
        (EXON_OVERLAP, EXON_OVERLAP_LABEL),
        (MPOI, MPOI_LABEL),
        (PATHOGENICITY_SCORE, PATHOGENICITY_SCORE_LABEL),
        (PATHOGENICITY_LABEL, PATHOGENICITY_LABEL_LABEL),
        (TADEUS_PATHOGENICITY_SCORE, TADEUS_PATHOGENICITY_SCORE_LABEL),
    ):
        FileEntryPropertyType.objects.create(id=id, name=name)


globals().update(locals())

# save_xaxis()
# save_genes()
add_file_entry_property_types()
# save_enh_prom()
# ave_hic()
