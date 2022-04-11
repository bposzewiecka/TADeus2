from .defaults import DELETION, DUPLICATION, TRANSLOCATION
from .models import SVEntry


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


def transform_build(file_entries, from_build, to_build):

    from liftover import get_lifter

    converter = get_lifter(from_build, to_build)

    tmp = []

    for file_entry in file_entries:
        sv = SVEntry()
        sv.chrom = file_entry.chrom
        sv.start = converter[sv.chrom][file_entry.start][0][1]
        sv.end = converter[sv.chrom][file_entry.end][0][1]
        sv.sv_type = file_entry.sv_type
        tmp.append(sv)

    return tmp
