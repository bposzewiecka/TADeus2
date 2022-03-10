import os
from concurrent.futures import ThreadPoolExecutor

import bbi
import numpy as np
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from datasources.defaults import BED12, FILE_TYPE_BED, FILE_TYPE_BED_GRAPH, FILE_TYPE_HIC, FILE_TYPE_XAXIS, get_attributes
from datasources.models import BedFileEntry, Chromosome, FileEntry, Subtrack, TrackFile
from plots.models import Plot
from tadeus_portal.settings import TADEUS_DATA_DIR
from tracks.trackPlot import PlotArcs, PlotBed, PlotBedGraph, PlotDomains, PlotHiCMatrix, PlotVirtual4C, PlotXAxis

from .defaults import (
    AGGREGATE_FUNCTION_AVG,
    AGGREGATE_FUNCTION_MAX,
    AGGREGATE_FUNCTION_MIN,
    AGGREGATE_FUNCTIONS_OPTIONS,
    BED_DISPLAY_ARCS,
    BED_DISPLAY_DOMAINS,
    BED_DISPLAY_FLYBASE,
    BED_DISPLAY_OPTIONS,
    BED_DISPLAY_TILES,
    BED_DISPLAY_VERTICAL_LINES,
    BED_DISPLAY_WITH_INTRONS,
    BED_STYLE_OPTIONS,
    BED_STYLE_STACKED,
    BEDGRAPH_DISPLAY_OPTIONS,
    BEDGRAPH_DISPLAY_TRANSPARENT,
    BEDGRAPH_STYLE_AREA,
    BEDGRAPH_STYLE_OPTIONS,
    BEDGRAPH_TYPE_LINECHART,
    BEDGRAPH_TYPE_OPTIONS,
    COLOR_MAP_OPTIONS,
    DEFAULT_PLOT_COLOR,
    DEFAULT_PLOT_COLOR_MAP_OPTIONS,
    DEFAULT_PLOT_EDGE_COLOR,
    DEFAULT_WIDTH_PROP,
    HIC_DISPLAY_HIC,
    HIC_DISPLAY_OPTIONS,
    HIC_DISPLAY_VIRTUAL4C,
    TRANSFORM_NONE,
    TRANSFORM_OPTIONS,
)


class Track(models.Model):

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="tracks")
    subtracks = models.ManyToManyField(Subtrack, related_name="subtracks")
    track_file = models.ForeignKey(TrackFile, on_delete=models.PROTECT, null=False)
    no = models.IntegerField()

    title = models.CharField(max_length=100, null=True, blank=True)

    domains_file = models.ForeignKey(TrackFile, on_delete=models.PROTECT, null=True, related_name="domains_file_tracks", blank=True)

    height = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(20)])

    inverted = models.BooleanField(default=False)

    color = models.CharField(max_length=7, default=DEFAULT_PLOT_COLOR)
    edgecolor = models.CharField(max_length=7, default=DEFAULT_PLOT_EDGE_COLOR)

    colormap = models.CharField(max_length=18, choices=COLOR_MAP_OPTIONS, default=DEFAULT_PLOT_COLOR_MAP_OPTIONS, null=True, blank=True)

    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)

    transform = models.IntegerField(choices=TRANSFORM_OPTIONS, default=TRANSFORM_NONE)

    bed_display = models.IntegerField(choices=BED_DISPLAY_OPTIONS, default=BED_DISPLAY_TILES)

    bed_style = models.IntegerField(choices=BED_STYLE_OPTIONS, default=BED_STYLE_STACKED)

    labels = models.BooleanField(default=True)

    name_filter = models.BooleanField(default=False)

    chromosome = models.ForeignKey(Chromosome, on_delete=models.PROTECT, null=True, blank=True)
    start_coordinate = models.IntegerField(null=True, blank=True, default=0)
    end_coordinate = models.IntegerField(null=True, blank=True, default=0)

    aggregate_function = models.CharField(max_length=4, choices=AGGREGATE_FUNCTIONS_OPTIONS, default=AGGREGATE_FUNCTION_AVG)

    hic_display = models.IntegerField(choices=HIC_DISPLAY_OPTIONS, default=HIC_DISPLAY_HIC)

    bedgraph_display = models.IntegerField(choices=BEDGRAPH_DISPLAY_OPTIONS, default=BEDGRAPH_DISPLAY_TRANSPARENT)
    bedgraph_type = models.IntegerField(choices=BEDGRAPH_TYPE_OPTIONS, default=BEDGRAPH_TYPE_LINECHART)

    bedgraph_style = models.IntegerField(choices=BEDGRAPH_STYLE_OPTIONS, default=BEDGRAPH_STYLE_AREA)

    bin_size = models.IntegerField(null=True, blank=True, default=0)

    def get_file_type(self):
        return self.track_file.file_type

    def get_bed_sub_type(self):
        return self.track_file.bed_sub_type

    def get_style_choices(self):

        if self.get_file_type() == FILE_TYPE_BED:
            if self.get_bed_sub_type() == BED12:
                return BED_DISPLAY_OPTIONS
            else:
                return (BED_DISPLAY_TILES, "Tiles"), (BED_DISPLAY_DOMAINS, "Domains"), (BED_DISPLAY_ARCS, "Arcs")
        return None

    def draw_vlines_only(self):
        return self.bed_display == BED_DISPLAY_VERTICAL_LINES and self.track_file.file_type == FILE_TYPE_BED

    def draw_track(
        self,
        col,
        chrom,
        start,
        end,
        interval_start,
        interval_end,
        name_filter=None,
        breakpoint=None,
        left_side=None,
        width_prop=DEFAULT_WIDTH_PROP,
        ttype="syntenic",
    ):

        if not self.name_filter:
            name_filter = None

        trackPlot = None

        file_type = self.get_file_type()

        if file_type == FILE_TYPE_BED and self.bed_display in (
            BED_DISPLAY_TILES,
            BED_DISPLAY_WITH_INTRONS,
            BED_DISPLAY_FLYBASE,
        ):
            trackPlot = PlotBed(model=self)
        elif file_type == FILE_TYPE_BED and self.bed_display == BED_DISPLAY_ARCS:
            trackPlot = PlotArcs(model=self)
        elif file_type == FILE_TYPE_BED and self.bed_display == BED_DISPLAY_DOMAINS:
            trackPlot = PlotDomains(model=self)
        elif file_type == FILE_TYPE_BED_GRAPH:
            trackPlot = PlotBedGraph(model=self)
        elif file_type == FILE_TYPE_HIC and self.hic_display == HIC_DISPLAY_HIC:
            trackPlot = PlotHiCMatrix(model=self)
        elif file_type == FILE_TYPE_HIC and self.hic_display == HIC_DISPLAY_VIRTUAL4C:
            trackPlot = PlotVirtual4C(model=self)
        elif file_type == FILE_TYPE_XAXIS:
            trackPlot = PlotXAxis(model=self)

        return trackPlot.draw_track(col, chrom, start, end, interval_start, interval_end, name_filter, breakpoint, left_side, width_prop, ttype)

    def get_aggregate_function(self):

        if self.aggregate_function == AGGREGATE_FUNCTION_AVG:
            return sum
        if self.aggregate_function == AGGREGATE_FUNCTION_AVG:
            return np.mean
        if self.aggregate_function == AGGREGATE_FUNCTION_MIN:
            return min
        if self.aggregate_function == AGGREGATE_FUNCTION_MAX:
            return max

    def get_entries(self, chrom, start, end, name_filter=None):

        if self.track_file.big and self.track_file.file_type == FILE_TYPE_BED_GRAPH:
            return self.get_entries_big_wig(chrom, start, end, name_filter)
        elif self.track_file.big and self.track_file.file_type == FILE_TYPE_BED:
            return self.track_file.get_entries_big_bed(chrom, start, end, name_filter)
        else:
            return self.track_file.get_entries_db(chrom, start, end, name_filter)

    def get_entries_big_wig(self, chrom, start, end, name_filter=None):
        def get_entries_subtrack(file_path):

            with bbi.open(os.path.join(TADEUS_DATA_DIR, file_path)) as f:
                # with bbi.open('/home/basia/wgEncodeBroadHistoneGm12878H3k27acStdSig.bigWig') as f:

                entries_big_wig = []

                for i, score in enumerate(f.fetch(chrom, bins_start, bins_end, bins=bins, summary=self.aggregate_function)):

                    entry = BedFileEntry(FileEntry)

                    entry.chorm = chrom
                    entry.start = bins_start + i * self.bin_size
                    entry.end = bins_start + (i + 1) * self.bin_size
                    entry.score = score if score else 0

                    entries_big_wig.append(entry)

                return entries_big_wig

        bins_start = start // self.bin_size * self.bin_size - self.bin_size
        bins_end = end // self.bin_size * self.bin_size + 2 * self.bin_size

        bins = (bins_end - bins_start) // self.bin_size

        file_paths = [subtrack.file_path for subtrack in self.subtracks.all()]

        with ThreadPoolExecutor() as executor:
            entries = executor.map(get_entries_subtrack, file_paths)

        return list(entries)

    @property
    def file_name(self):
        return self.track_file.name

    @property
    def get_long_track_type_name(self):

        file_type = self.track_file.get_long_file_type_name

        if self.track_file.file_type == FILE_TYPE_HIC and self.hic_display == HIC_DISPLAY_HIC:
            return file_type + " (HIC)"

        if self.track_file.file_type == FILE_TYPE_HIC and self.hic_display == HIC_DISPLAY_VIRTUAL4C:
            return file_type + " (Virtual 4C)"

        return file_type

    def __str__(self):

        return self.title if self.title else self.track_file.name

    class Meta:
        ordering = ["no"]

    def get_attributes(self):
        return get_attributes(self.track_file.file_type, self.track_file.bed_sub_type)


@receiver(pre_save, sender=Track)
def add_defaults(sender, instance, **kwargs):

    if instance.pk is None:
        instance.bin_size = instance.track_file.bin_size


@receiver(post_save, sender=Track)
def add_default_subtracks(sender, instance, created=True, **kwargs):

    default_subtracks = instance.track_file.subtracks.filter(default=True)
    instance.subtracks.set(default_subtracks)
