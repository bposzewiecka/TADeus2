from .defaults import DELETION, DUPLICATION, TRANSLOCATION


def get_sv_abbr(SV_TYPE):

    if SV_TYPE == DELETION:
        return "DEL"

    if SV_TYPE == DUPLICATION:
        return "DUP"

    if SV_TYPE == TRANSLOCATION:
        return "TRANS"


def save_as_bed(file_entries, fn):

    with open(fn, "w") as f:

        for file_entry in file_entries:
            f.write(f"{file_entry.chrom}\t{file_entry.start}\t{file_entry.end}\t{get_sv_abbr(file_entry.sv_type)}\n")
