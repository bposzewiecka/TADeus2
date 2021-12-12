from datasources.models import BedFileEntry
from evaluation.defaults import DELETION, DUPLICATION, TRANSLOCATION
from evaluation.models import SVEntry


class ReadBedOrBedGraphException(Exception):
    def __init__(self, message, line_number=None):
        if line_number:
            message = f"Error reading line: #{line_number}. {message}"
        super().__init__(message)


class BedOrBedGraphReader:
    def __init__(self, file_handle, subtrack, return_svs=False):

        self.subtrack = subtrack
        self.bed_sub_type = None
        self.file_handle = file_handle
        self.line_number = 0
        self.return_svs = return_svs
        # guess file type
        fields = self.get_no_comment_line().split("\t")

        self.guess_bed_sub_type(fields)

        if not self.bed_sub_type:
            raise ReadBedOrBedGraphException("Cannot guess file type. Data should be in BED or BEDGraph format.")

        self.file_handle.seek(0)

        # list of bed fields
        self.fields = [
            "chrom",
            "chromStart",
            "chromEnd",
            "name",
            "score",
            "strand",
            "thickStart",
            "thickEnd",
            "itemRGB",
            "blockCount",
            "blockSizes",
            "blockStarts",
        ]

    def __iter__(self):
        return self

    def get_no_comment_line(self):

        line = self.file_handle.readline()

        if line.startswith("#") or line.startswith("track") or line.startswith("browser") or line.startswith("chrom"):
            line = self.get_no_comment_line()

        return line

    def guess_bed_sub_type(self, line_values):

        if self.return_svs:
            self.bed_sub_type = "Bed6"
        if len(line_values) == 3:
            self.bed_sub_type = "Bed3"
        if len(line_values) == 4:
            self.bed_sub_type = "BedGraph"
        if len(line_values) == 6:
            self.bed_sub_type = "Bed6"
        if len(line_values) == 9:
            self.bed_sub_type = "Bed9"
        if len(line_values) == 12:
            self.bed_sub_type = "Bed12"

        if self.bed_sub_type == "BedGraph":
            self.subtrack.track_file.file_type = "BG"
        else:
            self.subtrack.track_file.file_type = "BE"
            self.subtrack.track_file.bed_sub_type = self.bed_sub_type

    def num_of_fields(self):

        if self.return_svs:
            return 4

        if self.bed_sub_type == "Bed3":
            return 3
        if self.bed_sub_type == "BedGraph":
            return 4
        if self.bed_sub_type == "Bed6":
            return 6
        if self.bed_sub_type == "Bed9":
            return 9
        if self.bed_sub_type == "Bed12":
            return 12

    def __next__(self):
        line = self.get_no_comment_line()

        if line == "":
            raise StopIteration

        bed = self.get_bed_interval(line)

        return bed

    def get_bed_interval(self, bed_line):  # noqa: C901

        line_data = bed_line.strip().split("\t")
        self.line_number += 1

        if len(line_data) != self.num_of_fields():
            error_text = "Detected file type is {} but line does " "not have {} fields".format(self.bed_sub_type, self.num_of_fields())
            raise ReadBedOrBedGraphException(error_text, self.line_number)

        line_values = []
        for idx, r in enumerate(line_data):
            # first field is always chromosome/contig name
            # and should be cast as a string
            # same for field 3 (name)
            if (idx == 0) or (idx == 3 and self.subtrack.track_file.file_type == "BE" or self.return_svs):
                line_values.append(r)
            elif idx == 3 and self.subtrack.track_file.file_type == "BG":
                try:
                    line_values.append(float(r))
                except Exception:
                    raise ReadBedOrBedGraphException("Bedgraph value should be float.", self.line_number)
            # check field strand
            elif idx == 5:
                if r not in ["+", "-", "."]:
                    if r == "1":
                        r = "+"
                    elif r == "-1":
                        r = "-"
                    else:
                        error_text = f'Invalid strand value "{r}"'
                        raise ReadBedOrBedGraphException(error_text, self.line_number)

                line_values.append(r)

            elif idx in [1, 2, 6, 7, 9]:
                # start and end fields must be integers, same for thichStart(6),
                # and thickEnd(7) and blockCount(9) fields
                try:
                    line_values.append(int(r))

                    if idx == 9:
                        block_count = line_values[-1]

                except ValueError:
                    error_text = f'Value "{r}" in field "{self.fields[idx]}" is not an integer'
                    raise ReadBedOrBedGraphException(error_text, self.line_number)
            # check item rgb
            elif idx == 8:
                rgb = r.split(",")
                if len(rgb) == 3:
                    try:
                        rgb = list(map(int, rgb))
                        rgb = list(filter(lambda x: 0 <= x <= 255, rgb))
                        if len(rgb) != 3:
                            raise ValueError

                        rgb = list(map(lambda x: format(x, "x"), rgb))
                        rgb = "".join(map(lambda x: x if len(x) == 2 else "0" + x, rgb)).lower()
                    except ValueError:
                        error_text = f'The itemRGB field "{r}" is not valid'
                        raise ReadBedOrBedGraphException(error_text, self.line_number)
                    line_values.append(rgb)
                else:
                    line_values.append(None)

            elif idx in [10, 11]:
                # this are the block sizes and block start positions
                r_parts = r.split(",")
                try:
                    r_parts = [int(x) for x in r_parts if x != ""]
                except ValueError:
                    error_text = f'The block field "{r}" is not valid'
                    raise ReadBedOrBedGraphException(error_text, self.line_number)

                if len(r_parts) != block_count:
                    error_text = f'The block field "{r}" does not have {block_count} values'
                    raise ReadBedOrBedGraphException(error_text, self.line_number)

                line_values.append(r.strip(","))
            else:
                try:
                    tmp = float(r)
                except Exception:
                    tmp = None
                line_values.append(tmp)

        if line_values[2] < line_values[1]:
            raise ReadBedOrBedGraphException("ChromStart position greater  than chromEnd position", self.line_number)

        if len(line_values) >= 9 and line_values[7] < line_values[6]:
            raise ReadBedOrBedGraphException("ThickStart position greater than thickEnd position", self.line_number)

        chrom = line_values[0]
        start = line_values[1]
        end = line_values[2]

        name = score = strand = thick_start = thick_end = itemRGB = block_count = block_sizes = block_starts = None

        if self.bed_sub_type in ("BedGraph"):
            score = line_values[3]

        if self.return_svs:
            name, sv_type = get_name_and_sv_type(line_values[3], self.line_number)

            score = 0
            strand = "."

        if self.bed_sub_type in ("Bed6", "Bed9", "Bed12") and not self.return_svs:
            name = line_values[3]
            score = line_values[4]
            strand = line_values[5]

        if self.bed_sub_type in ("Bed9", "Bed12"):
            thick_start = line_values[6]
            thick_end = line_values[7]
            itemRGB = line_values[8]

        if self.bed_sub_type in ("Bed12"):
            block_count = line_values[9]
            block_sizes = line_values[10]
            block_starts = line_values[11]

        if self.return_svs:

            return SVEntry(subtrack=self.subtrack, chrom=chrom, start=start, end=end, name=name, score=score, strand=strand, sv_type=sv_type)

        return BedFileEntry(
            subtrack=self.subtrack,
            chrom=chrom,
            start=start,
            end=end,
            name=name,
            score=score,
            strand=strand,
            thick_start=thick_start,
            thick_end=thick_end,
            itemRGB=itemRGB,
            block_count=block_count,
            block_sizes=block_sizes,
            block_starts=block_starts,
        )


def get_name_and_sv_type(name, line_number):

    name_with_semicolon = name + ";"

    index = name_with_semicolon.find(";")

    sv_type_str = name_with_semicolon[:index].strip()
    name = name_with_semicolon[index + 1 : -1].strip()

    if sv_type_str.upper() not in ("DEL", "DUP", "TRANS"):
        raise ReadBedOrBedGraphException(
            'Structural variants without type specified. Add  "DEL", "DUP" or "TRANS" with semicolon at the beginning of bed entry name to specify a structural variant type.',
            line_number,
        )
    else:
        if sv_type_str == "DEL":
            sv_type = DELETION
        elif sv_type_str == "DUP":
            sv_type = DUPLICATION
        else:
            sv_type = TRANSLOCATION

    if name != "":
        return name, sv_type

    return sv_type_str, sv_type
