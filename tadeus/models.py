from django.db import models
from django.contrib.auth.models import User
from tadeus.trackPlot import PlotBed, PlotXAxis, PlotBedGraph, PlotDomains, PlotArcs, PlotHiCMatrix, PlotVirtualHIC
from django.db.models import Q
import matplotlib.pyplot as plt
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.html import format_html
import tadeus.statistics as  statistics 
import pyBigWig
import bbi

from tadeus.defaults import DEFAULT_WIDTH_PROP, DEFAULT_PLOT_COLOR, DEFAULT_PLOT_EDGE_COLOR, DEFAULT_PLOT_COLOR_MAP_OPTIONS
from multiprocessing import Pool

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from concurrent.futures import ThreadPoolExecutor

class Species(models.Model):
    name = models.CharField(max_length = 50, unique = True)

class Assembly(models.Model):
    species = models.ForeignKey(Species, on_delete = models.PROTECT)
    name = models.CharField(max_length = 50, unique = True)

    @property
    def organism(self):
        return self.species.name

    def __str__(self):
        return self.name

class Chromosome(models.Model):
    assembly = models.ForeignKey(Assembly, on_delete = models.CASCADE, related_name = 'chromosomes')
    name = models.CharField(max_length = 50)
    size = models.IntegerField()

    class Meta:
        unique_together = ('assembly', 'name',)

    def __str__(self):
        return self.name    


class Sample(models.Model):
    name = models.CharField(max_length = 200)     
    tissue = models.CharField(max_length = 100)
    description =  models.CharField(max_length = 1000)
    species =  models.ForeignKey(Species, on_delete = models.PROTECT) 

    def __str__(self):
        return self.name

class TrackFile(models.Model):

    FILE_TYPE_BED = 'BE'
    FILE_TYPE_BED_GRAPH = 'BG'
    FILE_TYPE_HIC = 'HI'
    FILE_TYPE_XAXIS = 'XA'

    FILE_TYPES = (
        (FILE_TYPE_BED, 'Bed'),
        (FILE_TYPE_BED_GRAPH, 'BedGraph'),
        (FILE_TYPE_HIC, 'HiCMatrix'),
        (FILE_TYPE_XAXIS, 'XAxis'),
    )

    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT) 
    sample =  models.ForeignKey(Sample, on_delete = models.PROTECT, null = True) 
    name = models.CharField(max_length = 200)
    source_name = models.CharField(max_length = 200, null = True, blank = True)
    source_url = models.URLField(max_length = 2000, null = True, blank = True)
    file_type = models.CharField(max_length = 2, choices = FILE_TYPES)
    owner =  models.ForeignKey(User, on_delete = models.PROTECT, null = True) 
    public = models.BooleanField(default = False)
    approved = models.BooleanField(default = False)
    reference = models.CharField(max_length = 500, null = True, blank = True)
    bin_sizes = models.CharField(max_length = 500, null = True)
    auth_cookie = models.CharField(max_length = 60, null = True)
    big = models.BooleanField(default = False)    
    bin_size = models.IntegerField(null = True)

    BED3 = 'Bed3'
    BED6 = 'Bed6'
    BED9 = 'Bed9'
    BED12 = 'Bed12'

    FILE_SUB_TYPES = (
        (BED3, BED3),
        (BED6, BED6),
        (BED9, BED9),
        (BED12, BED12)
    )

    bed_sub_type = models.CharField(max_length = 5, choices = FILE_SUB_TYPES, null = True)

    bin_size = models.IntegerField(default = 25) 

    def get_entries_db(self, chrom, start, end, name_filter = None):

        q = self.file_entries.filter(chrom=chrom)

        if name_filter:
            q = q.filter(name = name_filter)

        q = q.filter(Q(end__range=(start, end))| Q(start__range=(start, end)) | (Q(start__lte=start) & Q(end__gte=end))).order_by('start', 'end')

        return q

    def get_entries_big_bed(self, chrom, start, end, name_filter = None):

        big_bed = pyBigWig.open(self.file_path)

        entries = []

        for big_bed_entry in big_bed.entries(chrom, start, end):

            entry = BedFileEntry(FileEntry)

            data = big_bed_entry[2].split('\t')

            entry.start = big_bed_entry[0]
            entry.end = big_bed_entry[1]

            if self.bed_sub_type in (BED6, BED9, BED12):
                entry.name =  data[0]
                entry.score = int(data[1])
                entry.stand = data[2]

            if self.bed_sub_type in (BED9, BED12):
                entry.thick_start = int(data[3])
                entry.thick_end = int(data[4])
                entry.itemRGB = '{:02x}{:02x}{:02x}'.format(*map(int, data[5].split(',')))

            if self.bed_sub_type == BED12:
                block_count =  int(data[6])
                block_sizes = data[7]
                block_starts = data[8]

            entries.append(entry)
 
        return entries

    @property
    def organism(self):
        return self.assembly.organism

    def read_bed(self):

        if self.file_type not in (FILE_TYPE_BED, FILE_TYPE_BED_GRAPH): return

        from tadeus.readBed import BedOrBedGraphReader
        from django.db import transaction

        bed_entries = BedOrBedGraphReader(open(self.subtracks[0].file_path, 'r'), self)

        @transaction.atomic
        def save_bed_entries(bed_entries):
            for bed_entry in bed_entries: 
                bed_entry.save()

        save_bed_entries(bed_entries)

    def get_attributes(self):

        attributes = []

        attributes.append('title')
        attributes.append('no')
        attributes.append('height')
        attributes.append('edgecolor')

        if self.file_type in (self.FILE_TYPE_BED_GRAPH, self.FILE_TYPE_HIC):
            attributes.append('transform')
                  
        if self.file_type == self.FILE_TYPE_BED:
            attributes.append('labels')
            attributes.append('color')
            attributes.append('bed_display')

        bed_with_name_and_color = self.file_type == self.FILE_TYPE_BED and (self.track.bed_sub_type in (BED6, BED9, BED12))

        if bed_with_name_and_color:
            attributes.append('labels')
            attributes.append('name_filter')

        if self.file_type in self.FILE_TYPE_HIC or bed_with_name_and_color:
            attributes.append('colormap')

        if self.file_type in (self.FILE_TYPE_BED_GRAPH, self.FILE_TYPE_HIC) or bed_with_name_and_color:            
            attributes.append('min_value')
            attributes.append('max_value')

        if self.file_type == self.FILE_TYPE_HIC:
            attributes.append('domains_file')
            attributes.append('inverted')
            attributes.append('hic_display')
            attributes.append('chromosome')
            attributes.append('start_coordinate')
            attributes.append('end_coordinate')

        if self.file_type == self.FILE_TYPE_BED_GRAPH:
            attributes.append('subtracks')
            attributes.append('bedgraph_display')
            attributes.append('bedgraph_type')
            attributes.append('bedgraph_style')
            attributes.append('style')
            attributes.append('bin_size')      
            attributes.append('aggregate_function')        
     
        return attributes

class Subtrack(models.Model):
    track_file =  models.ForeignKey(TrackFile, on_delete = models.CASCADE, related_name='subtracks') 
    file_path = models.CharField(max_length = 500, null = True)
    rgb = models.CharField(max_length = 7, null = True)
    sample = models.ForeignKey(Sample, on_delete = models.PROTECT, related_name='subtracks', null=True) 
    name =  models.CharField(max_length = 500, null = True)
    default = models.BooleanField(default = False)

class FileEntry(models.Model):

    def __str__(self):
        return '{}:{:,}-{:,}'.format(self.chrom, self.start, self.end)

    track_file =  models.ForeignKey(TrackFile, on_delete = models.CASCADE, related_name='file_entries') 
   
    chrom = models.CharField(max_length = 50)
    start =  models.IntegerField()
    end = models.IntegerField()
    labels = models.BooleanField(default = False)

    STRAND_TYPES = (
        ('+', '+'),
        ('-', '-'),
        ('.', '.'),
    )

    strand = models.CharField(max_length = 1, choices = STRAND_TYPES, null = True)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}:{:,}-{:,}'.format(self.chrom, self.start, self.end)

    def __len__(self):
        return  self.end - self.start

class BedFileEntry(FileEntry):
    name = models.CharField(max_length = 100,  null = True)
    score =  models.FloatField(null = True)

    thick_start = models.IntegerField(null = True)
    thick_end = models.IntegerField(null = True)
    itemRGB =  models.CharField(max_length = 6, null=True)
    block_count = models.IntegerField(null = True)
    block_sizes = models.CharField(max_length = 400, null = True)
    block_starts = models.CharField(max_length = 400, null = True)

    def get_block_sizes(self):
        return list(map(int, self.block_sizes.split(',')))

    def get_block_starts(self):
        return list(map(int, self.block_starts.split(',')))

    def get_adj_left(self, n = 1000000):
        return max(0,  self.start - n)

    def get_adj_right(self, n = 1000000):
        return self.end + n

    ensembl_gene_id = models.CharField(null=True, max_length = 20)
    biotype = models.CharField(max_length = 20)


    def set_eval_pvalue(self):
        enh_prom_file = TrackFile.objects.get(pk = 40)
        n1 = len([ enh_prom.name.upper() for enh_prom in enh_prom_file.get_entries(self.chrom, self.start, self.start)])
        n2 = len([ enh_prom.name.upper() for enh_prom in enh_prom_file.get_entries(self.chrom, self.end, self.end)])

        self.score = statistics.get_eval_pvalue(max(n1,n2))

class Gene(BedFileEntry):
    pass

class Breakpoint(models.Model):

    def __str__(self):
        return '{}:{:,}-{:,}'.format(self.chrom, self.start, self.end)

    sample =  models.ForeignKey(Sample, on_delete = models.PROTECT, null = True) 

    left_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, related_name = 'left_chrom') 
    left_coord = models.IntegerField()
    left_inverse = models.BooleanField(default = False)

    right_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, related_name = 'right_chrom') 
    right_coord = models.IntegerField()
    right_inverse = models.BooleanField(default = False)

    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    public = models.BooleanField(default = False)
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT, related_name = 'breakpoints')

class Plot(models.Model):
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT)
    owner = models.ForeignKey(User, on_delete = models.PROTECT, null = True) 
    public = models.BooleanField(default = False)
    approved = models.BooleanField(default = False)
    title = models.CharField(max_length = 400)
    name =  models.CharField(max_length = 400)
    auth_cookie = models.CharField(max_length = 60, null = True)

    def getTracks(self):
        return self.tracks.order_by('no', 'id').all()

    def getTracksToPlot(self):
        tracks = self.getTracks()

        return [track for track in tracks if not track.draw_vlines_only()]

    def getNameFilters(self, chrom ,start, end):
        tracks = self.getTracks()

        tracks = [track for track in tracks if track.name_filter]

        names = set(entry.name for track in tracks for entry in track.get_entries(chrom, start, end))

        return names

    def getVLineEntries(self, chrom ,start, end):
        tracks = self.getTracks()

        tracks = [track for track in tracks if track.draw_vlines_only()]

        return [ entry.start for track in tracks for entry in track.get_entries(chrom, start, end)]

    def hasEval(self):
        return  hasattr(self, 'eval') 


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

    colormap =  models.CharField(max_length = 15, choices = COLOR_MAP_OPTIONS, default = DEFAULT_PLOT_COLOR_MAP_OPTIONS, null = True, blank = True)

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

class Eval(models.Model):
    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    track_file =  models.OneToOneField(TrackFile, on_delete = models.PROTECT, related_name = 'eval')
    name = models.CharField(max_length = 400)
    plot = models.OneToOneField(Plot, on_delete = models.PROTECT, related_name = 'eval')
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT) 
    auth_cookie = models.CharField(max_length = 60, null=True)

class Phenotype(models.Model):
    db = models.CharField(max_length = 10)
    pheno_id = models.CharField(max_length = 20)
    name = models.CharField(max_length = 200)
    definition = models.CharField(max_length = 1000, null = True)
    comment = models.CharField(max_length = 2000, null = True)
    is_a = models.ManyToManyField('self', symmetrical = False) 
    genes = models.ManyToManyField(Gene, related_name = 'phenotypes',  through = 'GeneToPhenotype')

    def __str__(self):
        return self.pheno_id

    @property
    def url(self): 
        link = None

        if self.db  == 'HPO':
            link = 'http://compbio.charite.de/hpoweb/showterm?id={pheno_id}'.format(pheno_id = self.pheno_id)

        if self.db  == 'OMIM':
            link = 'https://www.omim.org/entry/{pheno_id}'.format(pheno_id = self.pheno_id)

        if self.db  == 'ORPHA':
            link = 'https://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert={pheno_id}'.format(pheno_id = self.pheno_id.split(':')[1])       

        return link

    @property
    def link(self):

        link = self.url

        if self.db  == 'HPO':   
            return format_html('<a href="{link}" target="_blank">{name}</a>', link = link, name = self.pheno_id)

        if self.db  == 'OMIM':
            return format_html('<a href="{link}" target="_blank">OMIM:{name}</a>', link = link, name = self.pheno_id)

        if self.db  == 'ORPHA':
            return format_html('<a href="{link}" target="_blank">{name}</a>', link = link, name = self.pheno_id)          

        return None

class GeneToPhenotype(models.Model):
    gene = models.ForeignKey(Gene, on_delete = models.CASCADE)
    phenotype = models.ForeignKey(Phenotype, on_delete = models.CASCADE)
    frequent =  models.BooleanField(default = False)

    class Meta:
        ordering = ['gene',]