from django.db import models
from django.contrib.auth.models import User
from tadeus.trackPlot import PlotBed, PlotXAxis, PlotBedGraph, PlotDomains, PlotArcs, PlotHiCMatrix, PlotVirtualHIC
from django.db.models import Q
import matplotlib.pyplot as plt
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.html import format_html
import evaluation.statistics as  statistics 
import pyBigWig
import bbi

from tadeus.defaults import DEFAULT_WIDTH_PROP, DEFAULT_PLOT_COLOR, DEFAULT_PLOT_EDGE_COLOR, DEFAULT_PLOT_COLOR_MAP_OPTIONS
from plots.models import Plot

from datasources.models import Sample, Chromosome, Assembly, Species, TrackFile, BedFileEntry

from multiprocessing import Pool

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from concurrent.futures import ThreadPoolExecutor

class Subtrack(models.Model):
    track_file =  models.ForeignKey(TrackFile, on_delete = models.CASCADE, related_name='subtracks') 
    file_path = models.CharField(max_length = 500, null = True)
    rgb = models.CharField(max_length = 7, null = True)
    sample = models.ForeignKey(Sample, on_delete = models.PROTECT, related_name='subtracks', null=True) 
    name =  models.CharField(max_length = 500, null = True)
    default = models.BooleanField(default = False)


class Track(models.Model):
    
    plot = models.ForeignKey(Plot, on_delete = models.CASCADE, related_name = 'tracks')
    subtracks = models.ManyToManyField(Subtrack, related_name = 'subtracks')
    track_file = models.ForeignKey(TrackFile, on_delete = models.PROTECT)
    no = models.IntegerField()
    
    title = models.CharField(max_length = 100, null = True, blank = True)

    domains_file = models.ForeignKey(TrackFile, on_delete = models.PROTECT, null = True, related_name = 'domains_file_tracks', blank = True)

    height = models.IntegerField(null = True, blank = True, validators = [MinValueValidator(1), MaxValueValidator(20)])

    inverted = models.BooleanField(default = False)
    
    color =  models.CharField(max_length = 6, default = DEFAULT_PLOT_COLOR)
    edgecolor = models.CharField(max_length = 6, default = DEFAULT_PLOT_EDGE_COLOR)

    COLOR_MAP_OPTIONS = ((color_map, color_map) for color_map in plt.colormaps())

    colormap =  models.CharField(max_length = 18, choices = COLOR_MAP_OPTIONS, default = DEFAULT_PLOT_COLOR_MAP_OPTIONS, null = True, blank = True)

    min_value = models.FloatField(null = True, blank = True)
    max_value = models.FloatField(null = True, blank = True)

    TRANSFORM_NONE = 0
    TRANSFORM_LOG1P = 1
    TRANSFORM_LOG = 2
    TRANSFORM_MINUS_LOG = 3

    TRANSFORM_OPTIONS = (
        (TRANSFORM_NONE, 'none'),
        (TRANSFORM_LOG1P, 'log1p'),
        (TRANSFORM_LOG, 'log'),
        (TRANSFORM_MINUS_LOG, '-log'),
    )

    transform = models.IntegerField(choices = TRANSFORM_OPTIONS, default = TRANSFORM_NONE)

    BED_DISPLAY_TILES = 1
    BED_DISPLAY_WITH_INTORNS = 2
    BED_DISPLAY_FLYBASE = 3
    BED_DISPLAY_DOMAINS = 4
    BED_DISPLAY_ARCS = 5
    BED_DISPLAY_VERTICAL_LINES = 6

    BED_DISPLAY_OPTIONS = (
        (BED_DISPLAY_TILES, 'Tiles'),
        (BED_DISPLAY_WITH_INTORNS, 'With introns'),
        (BED_DISPLAY_FLYBASE, 'Flybase'),
        (BED_DISPLAY_DOMAINS, 'Domains'),
        (BED_DISPLAY_ARCS, 'Arcs'),
        (BED_DISPLAY_VERTICAL_LINES, 'Vertical lines'),
    )

    bed_display = models.IntegerField(choices = BED_DISPLAY_OPTIONS, default = BED_DISPLAY_TILES)

    BED_STYLE_STACKED = 1
    BED_STYLE_COLLAPSED = 2
    BED_STYLE_INTERLACED = 3

    BED_STYLE_OPTIONS = (
        (BED_STYLE_STACKED, 'Stacked'),
        (BED_STYLE_COLLAPSED, 'Collapsed'),
        (BED_STYLE_INTERLACED, 'Interlaced'),
    )

    bed_style = models.IntegerField(choices = BED_STYLE_OPTIONS, default = BED_STYLE_STACKED)

    labels =  models.BooleanField(default = True)

    name_filter =  models.BooleanField(default = False)

    chromosome = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, blank=True)
    start_coordinate =  models.IntegerField(null = True, blank=True,  default = 0)
    end_coordinate =  models.IntegerField(null = True, blank=True,  default = 0)

    AGGREGATE_FUNCTION_AVG = 'mean'
    AGGREGATE_FUNCTION_SUM = 'sum'
    AGGREGATE_FUNCTION_MIN = 'min'
    AGGREGATE_FUNCTION_MAX = 'max'

    AGGREGATE_FUNCTIONS_OPTIONS = (
        (AGGREGATE_FUNCTION_AVG, 'mean'),
        (AGGREGATE_FUNCTION_SUM, 'sum'),
        (AGGREGATE_FUNCTION_MIN, 'min'),
        (AGGREGATE_FUNCTION_MAX, 'max'),
    )

    aggregate_function = models.CharField(max_length = 4, choices = AGGREGATE_FUNCTIONS_OPTIONS, default = AGGREGATE_FUNCTION_AVG)

    HIC_DISPLAY_HIC = 0
    HIC_DISPLAY_VIRTUAL4C = 1
  
    HIC_DISPLAY_OPTIONS = (
        (HIC_DISPLAY_HIC, 'HIC'),
        (HIC_DISPLAY_VIRTUAL4C, 'Virtual 4C'),
    )

    hic_display = models.IntegerField(choices = HIC_DISPLAY_OPTIONS, default = HIC_DISPLAY_HIC)

    BEDGRAPH_DISPLAY_NONE = 0
    BEDGRAPH_DISPLAY_TRANSPARENT = 1
    BEDGRAPH_DISPLAY_SOLID = 2
    BEDGRAPH_DISPLAY_STACKED = 3

    BEDGRAPH_DISPLAY_OPTIONS = (
        (BEDGRAPH_DISPLAY_TRANSPARENT, 'Transparent'),
        (BEDGRAPH_DISPLAY_SOLID, 'Solid'),
        (BEDGRAPH_DISPLAY_STACKED, 'Stacked'),
    )

    bedgraph_display = models.IntegerField(choices = BEDGRAPH_DISPLAY_OPTIONS, default = BEDGRAPH_DISPLAY_TRANSPARENT) 

    BEDGRAPH_TYPE_HISTOGRAM = 0
    BEDGRAPH_TYPE_LINECHART = 1

    BEDGRAPH_TYPE_OPTIONS = (
        (BEDGRAPH_TYPE_HISTOGRAM, 'Histogram'),
        (BEDGRAPH_TYPE_LINECHART, 'Linechart')
    )
 
    bedgraph_type = models.IntegerField(choices = BEDGRAPH_TYPE_OPTIONS, default = BEDGRAPH_TYPE_LINECHART)  

    BEDGRAPH_STYLE_LINE = 0
    BEDGRAPH_STYLE_LINE_WITH_BORDER = 1
    BEDGRAPH_STYLE_AREA = 2
    BEDGRAPH_STYLE_AREA_WITH_BORDER = 3

    BEDGRAPH_STYLE_OPTIONS = (
        (BEDGRAPH_STYLE_LINE, 'Line'),
        (BEDGRAPH_STYLE_LINE_WITH_BORDER, 'Line with border'),
        (BEDGRAPH_STYLE_AREA, 'Area'),
        (BEDGRAPH_STYLE_AREA_WITH_BORDER, 'Area with border'),
    )

    bedgraph_style =  models.IntegerField(choices = BEDGRAPH_STYLE_OPTIONS, default = BEDGRAPH_STYLE_AREA)
    
    bin_size = models.IntegerField() 

    def get_file_type(self):
        return self.track_file.file_type

    def get_bed_sub_type(self):
        return self.track_file.bed_sub_type

    def get_style_choices(self):

        if self.get_file_type() ==  self.track_file.FILE_TYPE_BED:
            if self.get_bed_sub_type() ==  self.track_file.BED12:
                return BED_DISPLAY_OPTIONS
            else:
                return (BED_DISPLAY_TILES, 'Tiles'), (BED_DISPLAY_DOMAINS, 'Domains'), (BED_DISPLAY_ARCS, 'Arcs')
        return None

    def draw_vlines_only(self):
        return self.bed_display == self.BED_DISPLAY_VERTICAL_LINES and self.track_file.file_type == self.track_file.FILE_TYPE_BED 

    def draw_track(self, col, chrom, start, end, interval_start, interval_end, 
        name_filter = None, breakpoint = None, left_side = None, width_prop = DEFAULT_WIDTH_PROP, breakpoint_coordinates = None):

        if not self.name_filter:
            name_filter = None

        trackPlot = None

        file_type = self.get_file_type()

        if file_type == self.track_file.FILE_TYPE_BED and self.bed_display in (self.BED_DISPLAY_TILES, self.track_file.BED_DISPLAY_INTRONS, self.track_file.BED_DISPLAY_FLYBASE):
            trackPlot = PlotBed(model = self)
        elif file_type == self.track_file.FILE_TYPE_BED and self.bed_display == self.BED_DISPLAY_ARCS:
            trackPlot = PlotArcs(model = self)
        elif file_type == self.track_file.FILE_TYPE_BED and self.bed_display == self.BED_DISPLAY_DOMAINS:
            trackPlot  = PlotDomains(model = self)
        elif file_type == self.track_file.FILE_TYPE_BED_GRAPH:
            trackPlot  =  PlotBedGraph(model = self)
        elif file_type == self.track_file.FILE_TYPE_HIC and self.hic_display == self.HIC_DISPLAY_HIC:
            trackPlot = PlotHiCMatrix(model = self)
        elif file_type == self.track_file.FILE_TYPE_HIC and self.hic_display == self.HIC_DISPLAY_VIRTUAL4C:
            trackPlot = PlotVirtualHIC(model = self)            
        elif file_type == self.track_file.FILE_TYPE_XAXIS:
            trackPlot  = PlotXAxis(model = self)

        return trackPlot.draw_track(col, chrom, start, end, interval_start, interval_end, name_filter, breakpoint, left_side, width_prop,   breakpoint_coordinates )

    def get_aggregate_function(self):
        if self.aggregate_function == self.AGGREGATE_FUNCTION_AVG:
            return sum
        if self.aggregate_function == self.AGGREGATE_FUNCTION_AVG:
            return np.mean
        if self.aggregate_function == self.AGGREGATE_FUNCTION_MIN:
            return min
        if self.aggregate_function == self.AGGREGATE_FUNCTION_MAX:
            return max
    
    def get_entries(self, chrom, start, end, name_filter = None):

        if self.track_file.big and self.track_file.file_type ==  self.track_file.FILE_TYPE_BED_GRAPH:
            return self.get_entries_big_wig(chrom, start, end, name_filter)
        elif self.track_file.big and self.track_file.file_type == self.track_file.FILE_TYPE_BED:
            return self.track_file.get_entries_big_bed(chrom, start, end, name_filter)
        else:
            return self.track_file.get_entries_db(chrom, start, end, name_filter)


    def get_entries_big_wig(self, chrom, start, end, name_filter = None):

        def get_entries_subtrack(file_path):

            with bbi.open(file_path) as f:     

                entries_big_wig = []

                for i, score in enumerate(f.fetch(chrom, bins_start, bins_end, bins = bins, summary = self.aggregate_function)):
                    
                    entry = BedFileEntry(FileEntry)

                    entry.chorm = chrom
                    entry.start = bins_start + i * self.bin_size
                    entry.end = bins_start + (i + 1) * self.bin_size
                    entry.score = score if score else 0

                    entries_big_wig.append(entry)

                return entries_big_wig 

        bins_start = start // self.bin_size * self.bin_size - self.bin_size
        bins_end = end // self.bin_size * self.bin_size + 2 *  self.bin_size

        bins = (bins_end - bins_start) // self.bin_size
       
        file_paths = [ subtrack.file_path for subtrack in self.subtracks.all()]

        with ThreadPoolExecutor() as executor:
            entries = executor.map(get_entries_subtrack, file_paths)

        return list(entries)

    @property
    def file_name(self):
        return self.track_file.name


@receiver(pre_save, sender=Track)
def add_defaults(sender, instance, **kwargs):
    if instance.pk is None:
        instance.bin_size = instance.track_file.bin_size

@receiver(post_save, sender=Track)
def add_default_subtracks(sender, instance, created = True,  **kwargs):
    default_subtracks = instance.track_file.subtracks.filter(default = True)
    instance.subtracks.set(default_subtracks)
