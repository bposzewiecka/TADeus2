from django.contrib.auth.models import User
from django.db import transaction

from datasources.models import Assembly, TrackFile
from evaluation.defaults import (
    CLINGEN_FILE_ID,
    DECIPHER_HAPLOINSUFFICENCY_FILE_ID,
    ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID,
    HIC_NA12787_FILE_ID,
    HIC_NA12787_TADS_FILE_ID,
    PLI_SCORE_FILE_ID,
)
from evaluation.models import SVPropertyType

hg38 = Assembly.objects.get(name="hg38")
admin = User.objects.get(username="admin")


def save_xaxis():

    xa = TrackFile(id=1, assembly=hg38, name="XAxis", source_name="XAxis", file_type="XA", bed_sub_type=None, owner=admin, public=True, approved=True)

    xa.save()


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
        assembly=hg38,
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
    haploinsufficient_genes.add_subtrack("data/hg19/genes/HI_Predictions_Version3.bed6")

    pli_genes = TrackFile(
        id=PLI_SCORE_FILE_ID,
        assembly=hg38,
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
        assembly=hg38,
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


def save_enh_prom():

    refseq_genes = TrackFile(
        id=ENCODE_DISTAL_DHS_ENHANCER_PROMOTER_FILE_ID,
        assembly=hg38,
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
    refseq_genes.add_subtrack("data/hg38/enhancers/hi_score_enh_promoter.bed")


def save_hic():

    hi = TrackFile(
        id=HIC_NA12787_FILE_ID,
        assembly=hg38,
        name="In situ Hi-C on gm12878 with MboI and bio-dCTP (Tethered HiC)",
        source_name="Rao SS et al. (2014) PMID:25497547",
        source_url="https://data.4dnucleome.org/files-processed/4DNFITRVKRPA/",
        file_type="HI",
        owner=admin,
        public=True,
        approved=True,
    )

    hi.save()
    hi.add_subtrack("data/hg38/HIC/NA12878/4DNFITRVKRPA.cool")

    tads = TrackFile(
        id=HIC_NA12787_TADS_FILE_ID,
        assembly=hg38,
        name="In situ Hi-C on gm12878 with MboI and bio-dCTP (Tethered HiC) - Boundaries calls on Hi-C contact matrices",
        source_name="Rao SS et al. (2014) PMID:25497547",
        source_url="https://data.4dnucleome.org/files-processed/4DNFITRVKRPA/",
        file_type="BED",
        bed_sub_type="BED3",
        owner=admin,
        public=True,
        approved=True,
    )

    tads.save()
    tads.add_subtrack("data/hg38/HIC/NA12878/4DNFIVAZEUBG.bed")


TADA_NUMBER_OF_AFFECTED_GENES_ID = 1
TADA_NUMBER_OF_AFFECTED_GENES_LABEL = "Number of affected Genes"
TADA_NUMBER_OF_AFFECTED_ENHANCERS_ID = 2
TADA_NUMBER_OF_AFFECTED_ENHANCERS_LABEL = "Number of affected Enhancers"
TADA_BOUNDARY_DISTANCE_ID = 3
TADA_BOUNDARY_DISTANCE_LABEL = "Boundary Distance"
TADA_BOUNDARY_DISTANCE_ID = 3
TADA_BOUNDARY_DISTANCE_LABEL = "Boundary Distance"
TADA_BOUNDARY_STABILITY = 4
TADA_BOUNDARY_STABILITY_LABEL = "Boundary Stability"
TADA_GENE_DISTANCE = 5
TADA_GENE_DISTANCE_LABEL = "Gene Distance"
TADA_ENHANCER_DISTANCE = 6
TADA_ENHANCER_DISTANCE_LABEL = "Enhancer Distance"
TADA_DDG2P_DISTANCE = 7
TADA_DDG2P_DISTANCE_LABEL = "DDG2P Distance"
TADA_GENE_LOEUF = 8
TADA_GENE_LOEUF_LABEL = "Gene LOEUF"
TADA_ENHANCER_CONSERVATION = 9
TADA_ENHANCER_CONSERVATION_LABEL = "Enhancer conservation"
TADA_GENE_HI = 10
TADA_GENE_HI_LABEL = "Gene HI"
TADA_CTCF_DISTANCE = 11
TADA_CTCF_DISTANCE_LABEL = "CTCF Distance"
TADA_HI_LOGODDS_SCORE = 12
TADA_HI_LOGODDS_SCORE_LABEL = "HI LogOdds Score"
TADA_EXON_OVERLAP = 13
TADA_EXON_OVERLAP_LABEL = ("Exon Overlap",)
TADA_MPOI = 14
TADA_MPOI_LABEL = "MPOI"
TADA_PATHOGENICITY_SCORE = 15
TADA_PATHOGENICITY_SCORE_LABEL = "Pathogenicity Score"
TADA_PATHOGENICITY_LABEL = 16
TADA_PATHOGENICITY_LABEL_LABEL = "Pathogenicity Label"
TADEUS_PATHOGENICITY_SCORE = 17
TADEUS_PATHOGENICITY_SCORE_LABEL = "TADeus Pathogenicity Score"


def add_file_entry_property_types():

    for id, name in (
        (TADA_BOUNDARY_DISTANCE_ID, TADA_BOUNDARY_DISTANCE_LABEL),
        (TADA_BOUNDARY_STABILITY, TADA_BOUNDARY_STABILITY_LABEL),
        (TADA_GENE_DISTANCE, TADA_GENE_DISTANCE_LABEL),
        (TADA_ENHANCER_DISTANCE, TADA_ENHANCER_DISTANCE_LABEL),
        (TADA_DDG2P_DISTANCE, TADA_DDG2P_DISTANCE_LABEL),
        (TADA_GENE_LOEUF, TADA_GENE_LOEUF_LABEL),
        (TADA_ENHANCER_CONSERVATION, TADA_ENHANCER_CONSERVATION_LABEL),
        (TADA_GENE_HI, TADA_GENE_HI_LABEL),
        (TADA_CTCF_DISTANCE, TADA_CTCF_DISTANCE_LABEL),
        (TADA_HI_LOGODDS_SCORE, TADA_HI_LOGODDS_SCORE_LABEL),
        (TADA_EXON_OVERLAP, TADA_EXON_OVERLAP_LABEL),
        (TADA_MPOI, TADA_MPOI_LABEL),
        (TADA_PATHOGENICITY_SCORE, TADA_PATHOGENICITY_SCORE_LABEL),
        (TADA_PATHOGENICITY_LABEL, TADA_PATHOGENICITY_LABEL_LABEL),
        (TADEUS_PATHOGENICITY_SCORE, TADEUS_PATHOGENICITY_SCORE_LABEL),
    ):
        SVPropertyType.objects.create(id=id, name=name)


globals().update(locals())


@transaction.atomic
def save_data():
    save_xaxis()
    # save_genes()
    # save_enh_prom()
    # save_hic()
    add_file_entry_property_types()


save_data()
