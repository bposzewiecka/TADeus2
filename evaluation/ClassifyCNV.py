import csv
import os
import shutil

from evaluation.utils import save_as_bed
from tadeus_portal.settings import CLASSIFYCNV_SCRIPT, CLASSIFYCNV_TEMP_FILES_DIR

from .defaults import DELETION, DUPLICATION


def get_cnv_scores(file_entries, output_directory, path_to_variants, path_to_results):

    save_as_bed(file_entries, path_to_variants)

    os.system(f"python3 {CLASSIFYCNV_SCRIPT} --GenomeBuild hg38 --infile {path_to_variants} --outdir {output_directory}")

    with open(path_to_results) as f:

        reader = csv.DictReader(f, delimiter="\t")

        svs_data = list(reader)

        for file_entry, sv_data in zip(file_entries, svs_data):

            # p = SVProperty(file_entry=file_entry, value=sv_data["Classification"], file_entry_property_type_id=15)
            # p.save()

            file_entry.ClassifyCNV = sv_data["Classification"]
            file_entry.save()


def annotate_cnvs_ClassifyCNV(file_entries, evaluation_id):

    output_directory = os.path.join(CLASSIFYCNV_TEMP_FILES_DIR, f"EVALUATION_{evaluation_id}")
    path_to_variants = os.path.join(CLASSIFYCNV_TEMP_FILES_DIR, f"input_{evaluation_id}.bed")
    path_to_results = os.path.join(output_directory, "Scoresheet.txt")

    if os.path.exists(output_directory) and os.path.isdir(output_directory):
        shutil.rmtree(output_directory)

    deldups = [file_entry for file_entry in file_entries if file_entry.sv_type in (DELETION, DUPLICATION)]

    if deldups:
        get_cnv_scores(deldups, output_directory, path_to_variants, path_to_results)

    shutil.rmtree(output_directory)
    os.remove(path_to_variants)
