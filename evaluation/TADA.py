import csv
import os
import shutil

from evaluation.utils import save_as_bed
from tadeus_portal.settings import TADA_TEMP_FILES_DIR

from .defaults import DELETION, DUPLICATION


def get_cnv_scores(file_entries, output_directory, path_to_variants, path_to_results, cnv_type, save=True):

    from liftover import get_lifter

    converter = get_lifter("hg38", "hg19")

    for file_entry in file_entries:

        file_entry.start = converter[file_entry.chrom][file_entry.start]
        file_entry.end = converter[file_entry.chrom][file_entry.end]

    save_as_bed(file_entries, path_to_variants)

    os.system(f"predict_variants -d -t {cnv_type} -v {path_to_variants} -o {output_directory}")

    with open(path_to_results) as f:

        reader = csv.DictReader(f, delimiter="\t")

        svs_data = list(reader)

        for file_entry, sv_data in zip(file_entries, svs_data):

            # p = SVProperty(file_entry=file_entry, value=sv_data["Pathogenicity Score"], file_entry_property_type_id=16)
            # p.save()

            file_entry.TADA_score = float(sv_data["Pathogenicity Score"])

            if save:
                file_entry.save()


def annotate_cnvs_TADA(file_entries, evaluation_id, save=True):

    output_directory = os.path.join(TADA_TEMP_FILES_DIR, f"EVALUATION_{evaluation_id}")
    path_to_variants = os.path.join(output_directory, "input.bed")
    path_to_results = os.path.join(output_directory, "Annotated_Predicted_TEST.csv")

    os.makedirs(output_directory, exist_ok=True)

    deletions = [file_entry for file_entry in file_entries if file_entry.sv_type == DELETION]
    duplications = [file_entry for file_entry in file_entries if file_entry.sv_type == DUPLICATION]

    if deletions:
        get_cnv_scores(deletions, output_directory, path_to_variants, path_to_results, "DEL", save)
    if duplications:
        get_cnv_scores(duplications, output_directory, path_to_variants, path_to_results, "DUP", save)

    shutil.rmtree(output_directory)
