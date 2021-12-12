import csv
import os
import shutil

from evaluation.utils import save_as_bed
from tadeus_portal.settings import CLASSIFYCNV_SCRIPT, CLASSIFYCNV_TEMP_FILES_DIR

from .defaults import DELETION, DUPLICATION


def get_cnv_scores(sv_entries, output_directory, path_to_variants, path_to_results):

    save_as_bed(sv_entries, path_to_variants)

    os.system(f"python3 {CLASSIFYCNV_SCRIPT} --GenomeBuild hg38 --infile {path_to_variants} --outdir {output_directory}")

    with open(path_to_results) as f:

        reader = csv.DictReader(f, delimiter="\t")

        svs_data = list(reader)

        for sv_entry, sv_data in zip(sv_entries, svs_data):

            sv_entry.ClassifyCNV = sv_data["Classification"]

            sv_entry.save()


def annotate_cnvs_ClassifyCNV(sv_entries, evaluation_id):

    output_directory = os.path.join(CLASSIFYCNV_TEMP_FILES_DIR, f"EVALUATION_{evaluation_id}")
    path_to_variants = os.path.join(CLASSIFYCNV_TEMP_FILES_DIR, f"input_{evaluation_id}.bed")
    path_to_results = os.path.join(output_directory, "Scoresheet.txt")

    deldups = [sv_entry for sv_entry in sv_entries if sv_entry.sv_type in (DELETION, DUPLICATION)]

    if deldups:

        if os.path.exists(output_directory) and os.path.isdir(output_directory):
            shutil.rmtree(output_directory)

        get_cnv_scores(deldups, output_directory, path_to_variants, path_to_results)

        shutil.rmtree(output_directory)
        os.remove(path_to_variants)
