import re
from io import BytesIO
from urllib.parse import quote_plus, urlencode

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django_tables2 import RequestConfig

from datasources.models import Sample
from evaluation.views import ranking
from plots.models import Plot
from tracks.defaults import DEFAULT_WIDTH_PROP
from tracks.models import Track

from .models import Breakpoint
from .tables import BreakpointFilter, BreakpointTable


def setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end):
    request.session["plot_" + str(p_id)] = (p_chrom, p_start, p_end, p_interval_start, p_interval_end)
    request.session["plot"] = (p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)


def getPlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        return request.session["plot_" + str(p_id)]
    return "chr1", 30 * 1000 * 1000, 33 * 1000 * 1000, None, None


def deletePlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        del request.session["plot_" + str(p_id)]

    if "plot" in request.session and request.session["plot"][0] == str(p_id):
        del request.session["plot"]


def setBreakpointPlotCookie(request, p_id, p_left_inverse, p_right_inverse, p_left_coordinate, p_right_coordinate, p_wildtype_option):
    request.session["breakpoint_plot_" + str(p_id)] = (
        p_id,
        p_left_inverse,
        p_right_inverse,
        p_left_coordinate,
        p_right_coordinate,
        p_wildtype_option,
    )
    request.session["breakpoint_plot"] = (p_id, p_left_inverse, p_right_inverse, p_left_coordinate, p_right_coordinate, p_wildtype_option)


def getBreakpointPlotCookie(request, p_id):
    if "breakpoint_plot_" + str(p_id) in request.session:
        return request.session["breakpoint_plot_" + str(p_id)]
    return p_id, "false", "false", "chr1:30000000", "chr2:40000000", WILDTYPES_OPTIONS_NONE


def setBrowserTypeCookie(request, browser_type):
    request.session["browser_type"] = browser_type


def getBrowserTypeCookie(request):
    if "browser_type" in request.session:
        return request.session["browser_type"]

    return "syntenic"


"""
def printPlotCookie(request, p_id):
    if "plot_" + str(p_id) in request.session:
        print(request.session["plot_" + str(p_id)])
    else:
        "Plot " + str(p_id) + "does not have cookie."
"""


def image(request, p_cols, p_id, p_chrom, p_start, p_end, p_breakpoint_id=None, p_left_side=None, p_width_prop=None):

    p_start = int(p_start)

    track = Track.objects.get(id=p_id)

    breakpoint = {}

    if request.method == "GET":
        name_filter = request.GET.get("name_filter", None)
        interval_start = request.GET.get("interval_start", "")

        if interval_start:
            interval_start = int(interval_start)

        interval_end = request.GET.get("interval_end", "")

        if interval_end:
            interval_end = int(interval_end)

        p_type = request.GET.get("type", "synthenic")

        breakpoint = {
            "left_start": int(request.GET.get("left_start", "-1")),
            "left_end": int(request.GET.get("left_end", "-1")),
            "right_start": int(request.GET.get("right_start", "-1")),
            "right_end": int(request.GET.get("right_end", "-1")),
            "right_coord": int(request.GET.get("right_coord", "-1")),
            "left_coord": int(request.GET.get("left_coord", "-1")),
            "right_inverse": get_bool_param(request, "right_inverse", "false"),
            "left_inverse": get_bool_param(request, "left_inverse", "false"),
        }

    fig = track.draw_track(
        p_cols,
        chrom=p_chrom,
        start=p_start,
        end=p_end,
        interval_start=interval_start,
        interval_end=interval_end,
        name_filter=name_filter,
        breakpoint=breakpoint,
        left_side=p_left_side,
        width_prop=p_width_prop,
        ttype=p_type,
    )

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)

    return HttpResponse(buf, content_type="image/png")


def get_chrom_length(plot_id, chrom):

    assembly = Plot.objects.get(id=plot_id).assembly
    return assembly.chromosomes.get(name=chrom).size


def get_chrom(chrom, plot_id):

    assembly = Plot.objects.get(id=plot_id).assembly
    return assembly.chromosomes.get(name=chrom)


def get_region_or_err_msg(search_text, plot_id):

    search_text = re.sub(r"(\s|,)", "", search_text)

    if search_text == "":
        return "Enter valid position query"

    sre = re.search(r"^chr(\d+|X|Y):(\d+)-(\d+)$", search_text)

    if not sre:
        return f'"{search_text}" is not valid position query'

    sre = sre.groups()

    chrom = "chr" + sre[0]
    start = int(sre[1])
    end = int(sre[2])

    if start >= end:
        return f"End coordinate should be greater than start coordinate. Your position query: {search_text}"

    try:
        chrom_size = get_chrom_length(plot_id, chrom)

        if end > chrom_size:
            return "End coordinate greater than chromosome size ({chrom_size}). Your position query: {search_text}".format(
                chrom_size=chrom_size, search_text=search_text
            )

        if start > chrom_size:
            return "Start coordinate greater then chromosome size ({chrom_size}). Your position query: {search_text}".format(
                chrom_size=chrom_size, search_text=search_text
            )

    except ObjectDoesNotExist:
        return f'Chromosome "{chrom}" does not exists. Search text: {search_text}'

    return chrom, start, end


def move(start, end, perc, right):
    region_len = end - start
    m = int(region_len * perc)

    if right:
        return start + m, end + m, 100 * perc
    else:
        return max(start - m, 0), max(end - m, region_len), 100 * perc


def zoom(start, end, perc, zoom_in):

    if zoom_in:
        perc = 1 / perc

    region_len = end - start
    middle = start + region_len / 2

    new_region_len = region_len * perc

    return max(int(middle - new_region_len / 2), 0), max(int(middle + new_region_len / 2), int(new_region_len))


def browser(request, p_id, p_chrom=None, p_start=None, p_end=None):

    setBrowserTypeCookie(request, "synthenic")

    perc_move = (0.5, 0.25)
    perc_zoom = 1.25

    p_plot = Plot.objects.get(id=p_id)

    c_chrom, c_start, c_end, c_interval_start, c_interval_end = getPlotCookie(request, p_id)

    if p_chrom is None:
        p_chrom = c_chrom
        p_start = c_start
        p_end = c_end

    p_name_filters = sorted(p_plot.getNameFilters(p_chrom, p_start, p_end))
    name_filter = ""
    get_url = ""
    results = ""

    if request.method == "GET":

        search_text = request.GET.get("search_text", "")
        name_filter = request.GET.get("name_filter", "")
        interval_start = request.GET.get("interval_start", c_interval_start or "")
        interval_end = request.GET.get("interval_end", c_interval_end or "")

        p_interval_start = request.GET.get("interval_start", c_interval_start)
        p_interval_end = request.GET.get("interval_end", c_interval_end)

        p_cnv_type = request.GET.get("cnv_type", "")
        p_TADeus_pvalue = request.GET.get("TADeus_pvalue", "")

        setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)

        region_or_err_msg = get_region_or_err_msg(search_text, p_id)

        if len(region_or_err_msg) == 3:
            p_chrom, p_start, p_end = region_or_err_msg
        elif search_text == "":
            pass
        else:
            messages.error(request, region_or_err_msg)

        get_url = "?" + urlencode(
            {
                "name_filter": name_filter,
                "interval_start": interval_start,
                "interval_end": interval_end,
                "cnv_type": p_cnv_type,
                "TADeus_pvalue": p_TADeus_pvalue,
            },
            quote_via=quote_plus,
        )

        if p_plot.hasEval() and p_interval_start is not None and p_interval_end is not None and p_interval_start != "" and p_interval_end != "":
            results = ranking(p_plot.eval, p_chrom, p_interval_start, p_interval_end)

    else:
        pass

    return TemplateResponse(
        request,
        "browser/browser.html",
        {
            "p_id": p_id,
            "p_plot": p_plot,
            "p_name_filters": p_name_filters,
            "p_cols": 1,
            "p_chrom": p_chrom,
            "p_start": p_start,
            "p_end": p_end,
            "name_filter": name_filter,
            "move": (
                move(p_start, p_end, perc_move[0], False),
                move(p_start, p_end, perc_move[1], False),
                move(p_start, p_end, perc_move[1], True),
                move(p_start, p_end, perc_move[0], True),
            ),
            "zoom_in": zoom(p_start, p_end, perc_zoom, True),
            "zoom_out": zoom(p_start, p_end, perc_zoom, False),
            "region_len": p_end - p_start,
            "get_url": get_url,
            "results": results,
            "interval_start": interval_start,
            "interval_end": interval_end,
            "cnv_type": p_cnv_type,
            "TADeus_pvalue": p_TADeus_pvalue,
        },
    )


def zoom_breakpoint(size, shift, perc, zoom_in, form_params):

    if zoom_in:
        perc = 1 / perc

    attributes = {"shift": int(shift * perc), "size": int(size * perc)}
    attributes.update(form_params)

    return urlencode(attributes, quote_via=quote_plus)


def move_breakpoint(size, shift, perc, right, form_params):

    m = int(size * perc)

    if right:
        new_shift = shift + m
    else:
        new_shift = shift - m

    attributes = {"shift": new_shift, "size": size}
    attributes.update(form_params)

    return urlencode(attributes, quote_via=quote_plus), 100 * perc


def get_coordinate_or_err_msg(request, search_text, plot_id):
    def get_results(request, search_text, plot_id):

        search_text = re.sub(r"(\s|,)", "", search_text)

        if search_text == "":
            return "Enter valid coordinate."

        sre = re.search(r"^chr(\d+|X|Y):(\d+)$", search_text)

        if not sre:
            return f'"{search_text}" is not valid coordinate.'

        sre = sre.groups()

        chrom = "chr" + sre[0]
        coordinate = int(sre[1])

        try:
            chrom_size = get_chrom_length(plot_id, chrom)

            if coordinate > chrom_size:
                return "Coordinate greater than chromosome size ({chrom_size}). Your coordinate: {search_text}".format(
                    chrom_size=chrom_size, search_text=search_text
                )

        except ObjectDoesNotExist:
            return f'Chromosome "{chrom}" does not exists. Search text: {search_text}.'

        return chrom, coordinate

    results = get_results(request, search_text, plot_id)

    if type(results) == tuple:
        return results
    else:
        messages.error(request, results)
        return None, None


def get_param(request, name, default):

    val = request.GET.get(name, default)

    if val == "":
        val = default

    return int(val)


def get_bool_param(request, name, default):

    val = request.GET.get(name, default)
    return val == "true"


WILDTYPES_OPTIONS_NONE = 0
WILDTYPES_OPTIONS_LEFT = 1
WILDTYPES_OPTIONS_RIGHT = 2
WILDTYPES_OPTIONS_BOTH = 3

WILDTYPES_OPTIONS = (
    (WILDTYPES_OPTIONS_NONE, "None"),
    (WILDTYPES_OPTIONS_LEFT, "Left"),
    (WILDTYPES_OPTIONS_RIGHT, "Right"),
    (WILDTYPES_OPTIONS_BOTH, "Both"),
)


def get_wildtype_params(direction, p_chrom, p_start, p_end, p_inverse, p_size, p_wildtype_option):

    if (direction == "left" and p_wildtype_option in (WILDTYPES_OPTIONS_LEFT, WILDTYPES_OPTIONS_BOTH)) or (
        direction == "right" and p_wildtype_option in (WILDTYPES_OPTIONS_RIGHT, WILDTYPES_OPTIONS_BOTH)
    ):

        if (p_inverse and direction == "left") or (not p_inverse and direction == "right"):
            p_wildtype_start = p_end - p_size
            p_wildtype_end = p_end
        else:
            p_wildtype_start = p_start
            p_wildtype_end = p_start + p_size

        return {"chrom": p_chrom, "start": p_wildtype_start, "end": p_wildtype_end, "inverse": "true" if p_inverse else "false"}

    else:
        return {}


def breakpoint_browser(request, p_id):  # noqa: C901

    setBrowserTypeCookie(request, "breakpoint")

    perc_move = (0.2, 0.1)
    perc_zoom = 1.25

    p_plot = Plot.objects.get(id=p_id)

    c_id, c_left_inverse, c_right_inverse, c_left_coordinate, c_right_coordinate, c_wildtype_option = getBreakpointPlotCookie(request, p_id)

    breakpoint_params = {}
    form_params = {}
    wildtype_left_params = {}
    wildtype_right_params = {}

    if request.method == "GET":

        p_size = get_param(request, "size", 2000000)
        p_shift = get_param(request, "shift", 0)

        p_right_inverse = request.GET.get("right_inverse", c_right_inverse)
        p_right_inverse_bool = p_right_inverse == "true"
        p_left_inverse = request.GET.get("left_inverse", c_left_inverse)
        p_left_inverse_bool = p_left_inverse == "true"

        p_left_coordinate = request.GET.get("left_coordinate", c_left_coordinate)
        p_right_coordinate = request.GET.get("right_coordinate", c_right_coordinate)

        p_left_chrom, p_left_coord = get_coordinate_or_err_msg(request, p_left_coordinate, p_id)
        p_right_chrom, p_right_coord = get_coordinate_or_err_msg(request, p_right_coordinate, p_id)

        p_wildtype_option = get_param(request, "wildtype_option", c_wildtype_option)

        p_TADeus_pvalue1 = request.GET.get("TADeus_pvalue1", "")
        p_TADeus_pvalue2 = request.GET.get("TADeus_pvalue2", "")

        setBreakpointPlotCookie(request, p_id, p_left_inverse, p_right_inverse, p_left_coordinate, p_right_coordinate, p_wildtype_option)

        if p_left_chrom is not None and p_right_chrom is not None:

            p_left_start = p_left_end = p_right_start = p_right_end = None
            p_left_width_prop = p_right_width_prop = 0

            if p_left_inverse_bool:
                p_left_end = p_left_coord + p_shift + p_size // 2
                p_left_start = p_left_end - min(p_shift + p_size // 2, p_size)
            else:
                p_left_start = p_left_coord - p_shift - p_size // 2
                p_left_end = p_left_start + min(p_shift + p_size // 2, p_size)

            if p_right_inverse_bool:
                p_right_start = p_right_coord + p_shift - p_size // 2
                p_right_end = max(p_right_coord, p_right_start - p_size)
            else:
                p_right_end = p_right_coord - p_shift + p_size // 2
                p_right_start = max(p_right_coord, p_right_end - p_size)

            left_size = int(p_size / 2) + p_shift
            right_size = int(p_size // 2) - p_shift

            p_left_width_prop = min(max(int(left_size / p_size * DEFAULT_WIDTH_PROP), 0), 1000)
            p_right_width_prop = min(max(int(right_size / p_size * DEFAULT_WIDTH_PROP), 0), 1000)

            wildtype_left_params = get_wildtype_params("left", p_left_chrom, p_left_start, p_left_end, p_left_inverse_bool, p_size, p_wildtype_option)

            wildtype_right_params = get_wildtype_params(
                "right", p_right_chrom, p_right_start, p_right_end, p_right_inverse_bool, p_size, p_wildtype_option
            )

            form_params = {
                "left_inverse": p_left_inverse,
                "right_inverse": p_right_inverse,
                "left_coordinate": p_left_coordinate,
                "right_coordinate": p_right_coordinate,
                "wildtype_option": p_wildtype_option,
            }

            breakpoint_params = {
                "left_chrom": p_left_chrom,
                "left_coord": p_left_coord,
                "right_chrom": p_right_chrom,
                "right_coord": p_right_coord,
                "right_width_prop": p_right_width_prop,
                "left_width_prop": p_left_width_prop,
                "right_inverse": p_right_inverse,
                "left_inverse": p_left_inverse,
            }

            if p_left_start:
                breakpoint_params["left_start"] = p_left_start
            if p_left_end:
                breakpoint_params["left_end"] = p_left_end
            if p_right_start:
                breakpoint_params["right_start"] = p_right_start
            if p_right_end:
                breakpoint_params["right_end"] = p_right_end

    results_left = ranking(None, p_left_chrom, p_left_coord, p_left_coord)
    results_right = ranking(None, p_right_chrom, p_right_coord, p_right_coord)

    return TemplateResponse(
        request,
        "browser/browser_breakpoint.html",
        {
            "p_id": p_id,
            "p_plot": p_plot,
            "p_size": p_size,
            "p_shift": p_shift,
            "move": (
                move_breakpoint(p_size, p_shift, perc_move[0], False, form_params),
                move_breakpoint(p_size, p_shift, perc_move[1], False, form_params),
                move_breakpoint(p_size, p_shift, perc_move[1], True, form_params),
                move_breakpoint(p_size, p_shift, perc_move[0], True, form_params),
            ),
            "zoom_in": zoom_breakpoint(p_size, p_shift, perc_zoom, True, form_params),
            "zoom_out": zoom_breakpoint(p_size, p_shift, perc_zoom, False, form_params),
            "breakpoint_params_url": "?" + urlencode(breakpoint_params, quote_via=quote_plus),
            "breakpoint_params": breakpoint_params,
            "wildtype_left_params": wildtype_left_params,
            "wildtype_right_params": wildtype_right_params,
            "wildtypes_options": WILDTYPES_OPTIONS,
            "form_params": form_params,
            "TADeus_pvalue1": p_TADeus_pvalue1,
            "TADeus_pvalue2": p_TADeus_pvalue2,
            "results_left": results_left,
            "results_right": results_right,
        },
    )


def breakpoints(request):

    breakpoints = Breakpoint.objects.all()

    if request.method == "GET":
        min_range = request.GET.get("min_range")
        max_range = request.GET.get("max_range")
        chrom = request.GET.get("chrom")

    q_left = Q()
    q_right = Q()

    if chrom:
        q_left &= Q(left_chrom__name__iexact=chrom)
        q_right &= Q(right_chrom__name__iexact=chrom)
    if min_range:
        q_left &= Q(left_coord__gte=min_range)
        q_right &= Q(right_coord__gte=min_range)
    if max_range:
        q_left &= Q(left_coord__lte=max_range)
        q_right &= Q(right_coord__lte=max_range)

    f = BreakpointFilter(request.GET, queryset=breakpoints.filter(q_left | q_right))
    table = BreakpointTable(f.qs)

    RequestConfig(request).configure(table)

    samples = Sample.objects.all().order_by("name", "id")

    return render(request, "browser/breakpoints.html", {"table": table, "filter": f, "samples": samples})
