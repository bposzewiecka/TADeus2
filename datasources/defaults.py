FILE_TYPE_BED = "BE"
FILE_TYPE_BED_GRAPH = "BG"
FILE_TYPE_HIC = "HI"
FILE_TYPE_XAXIS = "XA"

FILE_TYPES = (
    (FILE_TYPE_BED, "Bed"),
    (FILE_TYPE_BED_GRAPH, "BedGraph"),
    (FILE_TYPE_HIC, "HiCMatrix"),
    (FILE_TYPE_XAXIS, "XAxis"),
)

BED3 = "Bed3"
BED6 = "Bed6"
BED9 = "Bed9"
BED12 = "Bed12"

FILE_SUB_TYPES = ((BED3, BED3), (BED6, BED6), (BED9, BED9), (BED12, BED12))


def get_attributes(file_type, bed_sub_type):

    attributes = []

    attributes.append("title")
    attributes.append("no")
    attributes.append("height")

    if file_type != FILE_TYPE_XAXIS:
        attributes.append("edgecolor")

    if file_type in (FILE_TYPE_BED_GRAPH, FILE_TYPE_HIC):
        attributes.append("transform")

    if file_type == FILE_TYPE_BED:
        attributes.append("color")
        attributes.append("bed_display")
        attributes.append("bed_style")

    bed_with_name_and_color = file_type == FILE_TYPE_BED and (bed_sub_type in (BED6, BED9, BED12))

    if bed_with_name_and_color:
        attributes.append("labels")
        attributes.append("name_filter")

    if file_type in FILE_TYPE_HIC or bed_with_name_and_color:
        attributes.append("colormap")

    if file_type in (FILE_TYPE_BED_GRAPH, FILE_TYPE_HIC) or bed_with_name_and_color:
        attributes.append("min_value")
        attributes.append("max_value")

    if file_type == FILE_TYPE_HIC:
        attributes.append("hic_display")
        attributes.append("domains_file")
        attributes.append("inverted")
        attributes.append("chromosome")
        attributes.append("start_coordinate")
        attributes.append("end_coordinate")
        attributes.append("color")
        attributes.append("transform")

    if file_type == FILE_TYPE_BED_GRAPH:
        attributes.append("subtracks")
        attributes.append("bedgraph_display")
        attributes.append("bedgraph_type")
        attributes.append("bedgraph_style")
        attributes.append("style")
        attributes.append("bin_size")
        attributes.append("aggregate_function")

    return attributes


def get_filetypes():

    return [(FILE_TYPE_BED, bed_sub_type) for bed_sub_type in (BED3, BED6, BED9, BED12)] + [
        (file_type, None) for file_type in [FILE_TYPE_BED_GRAPH, FILE_TYPE_HIC, FILE_TYPE_XAXIS]
    ]


def get_filetypes_by_attribute():

    d = {}

    for file_type, bed_sub_type in get_filetypes():
        for attribute in get_attributes(file_type, bed_sub_type):
            if attribute in d:
                d[attribute].append((file_type, bed_sub_type))
            else:
                d[attribute] = [(file_type, bed_sub_type)]

    return d
