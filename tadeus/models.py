from django.db import models
from django.contrib.auth.models import User
from tadeus.trackPlot import PlotBed, PlotXAxis, PlotBedGraph, PlotDomains, PlotArcs, PlotHiCMatrix, PlotVirtualHIC
from django.db.models import Q
import matplotlib.pyplot as plt
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.html import format_html
import tadeus.statistics as  statistics 

from tadeus.defaults import DEFAULT_WIDTH_PROP

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
    assembly = models.ForeignKey(Assembly, on_delete = models.CASCADE, related_name='chromosomes')
    name = models.CharField(max_length = 50)
    size = models.IntegerField()

    class Meta:
        unique_together = ('assembly', 'name',)

    def __str__(self):
        return self.name    


class Sample(models.Model):
    name = models.CharField(max_length = 200)     
    description =  models.CharField(max_length = 1000)
    species =  models.ForeignKey(Species, on_delete = models.PROTECT) 

    def __str__(self):
        return self.name

class TrackFile(models.Model):

    FILE_TYPES = (
        ('BE', 'Bed'),
        ('BG', 'BedGraph'),
        ('BM', 'BedGraphMatrix'),
        ('HI', 'HiCMatrix'),
        ('XA', 'XAxis'),
    )

    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT) 
    sample =  models.ForeignKey(Sample, on_delete = models.PROTECT, null=True) 
    name = models.CharField(max_length = 200)
    source_name = models.CharField(max_length = 200, null =True, blank = True)
    source_url = models.URLField(max_length = 2000, null =True, blank = True)
    file_type = models.CharField(max_length=2, choices=FILE_TYPES)
    owner =  models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    public = models.BooleanField(default = False)
    approved = models.BooleanField(default = False)
    reference = models.CharField(max_length = 500, null =True, blank = True)
    file_path = models.CharField(max_length = 500, null =True)
    bin_sizes = models.CharField(max_length = 500, null=True)
    auth_cookie = models.CharField(max_length = 60, null=True)

    FILE_SUB_TYPES = (
        ('Bed3', 'Bed3'),
        ('Bed6', 'Bed6'),
        ('Bed9', 'Bed9'),
        ('Bed12', 'Bed12')
    )

    file_sub_type = models.CharField(max_length=5, choices=FILE_SUB_TYPES, null = True)

    def get_entries(self, chrom, start, end, name_filter = None):
        q = self.file_entries.filter(chrom=chrom)

        if name_filter:
            q = q.filter(name = name_filter)

        q = q.filter(Q(end__range=(start, end))| Q(start__range=(start, end)) | (Q(start__lte=start) & Q(end__gte=end))).order_by('start', 'end')

        return q

    @property
    def organism(self):
        return self.assembly.organism


    def read_bed(self):

        if self.file_type not in ('BE', 'BG'): return

        from tadeus.readBed import BedOrBedGraphReader
        from django.db import transaction

        bed_entries = BedOrBedGraphReader(open(self.file_path, 'r'), self)

        @transaction.atomic
        def save_bed_entries(bed_entries):
            for bed_entry in bed_entries: 
                bed_entry.save()

        save_bed_entries(bed_entries)

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
    block_count =   models.IntegerField(null = True)
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


    sample =  models.ForeignKey(Sample, on_delete = models.PROTECT, null=True) 

    left_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null=True, related_name='left_chrom' ) 
    left_coord = models.IntegerField()
    left_inverse = models.BooleanField(default = False)

    right_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null=True, related_name='right_chrom') 
    right_coord = models.IntegerField()
    right_inverse = models.BooleanField(default = False)

    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    public = models.BooleanField(default = False)


class Plot(models.Model):
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT)
    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    public = models.BooleanField(default = False)
    approved = models.BooleanField(default = False)
    title = models.CharField(max_length = 400)
    name =  models.CharField(max_length = 400)
    auth_cookie = models.CharField(max_length = 60, null=True)

    def getTracks(self):
        return self.tracks.order_by('no', 'id').all()

    def getTracksToPlot(self):
        tracks = self.getTracks()

        return [track for track in tracks if not track.draw_vlines_only()]

    def getColumnsDict(self):
        tracks = self.getTracksToPlot()

        d = {}

        for track in tracks:
            tracks_in_column = d.get(track.column, [])
            tracks_in_column.append(track)
            d[track.column] = tracks_in_column

        return d

    def getNameFilters(self, chrom ,start, end):
        tracks = self.getTracks()

        tracks = [track for track in tracks if track.name_filter]

        names = set( entry.name for track in tracks
                       for entry in track.get_entries(chrom, start, end))

        return names


    def getVLineEntries(self, chrom ,start, end):
        tracks = self.getTracks()

        tracks = [track for track in tracks if track.draw_vlines()]

        return [ entry.start for track in tracks
                       for entry in track.get_entries(chrom, start, end)]

    def hasEval(self):
        return  hasattr(self, 'eval') 


class Track(models.Model):
    plot = models.ForeignKey(Plot, on_delete = models.CASCADE, related_name='tracks')
    track_file = models.ForeignKey(TrackFile, on_delete = models.PROTECT)
    no = models.IntegerField()
    column = models.IntegerField(default = 1)

    title = models.CharField(max_length = 100, null = True, blank = True)

    BED_PRINT_OPTIONS = (
        ('B', 'Tiles'),
        ('V', 'Vertical Lines'),
        ('A', 'Tiles and Vertical Lines'),
    )

    bed_print_options = models.CharField(max_length = 1, choices = BED_PRINT_OPTIONS, default = 'B')

    domains_file = models.ForeignKey(TrackFile, on_delete = models.PROTECT, null = True, related_name = 'domains_file_tracks', blank=True)

    height =  models.IntegerField(null = True, blank = True, 
        validators=[
            MaxValueValidator(20),
            MinValueValidator(1)
        ])

    inverted = models.BooleanField(default = False)
    
    color =  models.CharField(max_length = 6, default= '1F78B4')
    edgecolor = models.CharField(max_length = 6, default= 'EEEEEE')

    COLOR_MAP_OPTIONS = ( (color_map, color_map) for color_map in plt.colormaps())

    colormap =  models.CharField(max_length = 15, choices = COLOR_MAP_OPTIONS, default = 'RdYlBu_r', null=True, blank=True)

    min_value = models.FloatField(null = True, blank=True)
    max_value = models.FloatField(null = True, blank=True)

    TRANSFORM_OPTIONS = (
        ('none', 'none'),
        ('log1p', 'log1p'),
        ('log', 'log'),
        ('-log', '-log'),
    )

    transform = models.CharField(max_length = 5, choices = TRANSFORM_OPTIONS, default = 'log1p')

    show_data_range = models.BooleanField(default = True)

    BEDGRAPH_STYLE_OPTIONS = (
        ('L', 'Line'),
        ('LB', 'Line with borders'),
        ('A', 'Area'),
        ('AB', 'Area with borders'),
    )

    bedgraph_style =  models.CharField(max_length = 2, choices = BEDGRAPH_STYLE_OPTIONS, default = 'L')

    BED_STYLE_OPTIONS = (
        ('tiles', 'Tiles'),
        ('introns', 'With introns'),
        ('flybase', 'Flybase'),
        ('domains', 'Domains'),
        ('arcs', 'Arcs'),
    )

    style =  models.CharField(max_length = 7, choices = BED_STYLE_OPTIONS, default = 'tiles')

    BED_DISPLAY_OPTIONS = (
        ('stacked', 'Stacked'),
        ('collapsed', 'Collapsed'),
        ('interlaced', 'Interlaced'),
    )

    display = models.CharField(max_length = 10, choices = BED_DISPLAY_OPTIONS, default = 'stacked')

    labels =  models.BooleanField(default = True)

    x_labels =  models.BooleanField(default = True)

    name_filter =  models.BooleanField(default = False)

    chromosome = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, blank=True)
    coordinate =  models.IntegerField(null = True, blank=True,  default = 0)
    neighbourhood =  models.IntegerField(null = True, blank=True,  default = 0)

    NEIGHBOURHOOD_TRANSFORM_OPTIONS = (
        ('sum', 'sum'),
        ('avg', 'avg'),
        ('min', 'min'),
        ('max', 'max'),
    )

    neighbourhood_transform = models.CharField(max_length = 5, choices = NEIGHBOURHOOD_TRANSFORM_OPTIONS, default = 'sum')
  
    HIC_DISPLAY_OPTIONS = (
        ('hic', 'HIC'),
        ('v4c', 'Virtual 4C'),
    )

    hic_display = models.CharField(max_length = 3, choices =  HIC_DISPLAY_OPTIONS, default = 'hic')

    def get_file_type(self):
        return self.track_file.file_type

    def get_file_sub_type(self):
        return self.track_file.file_sub_type

    def get_style_choices(self):
        if self.get_file_type() == 'BE':
            if self.get_file_sub_type() == 'Bed12':
                return (('tiles', 'Tiles'), ('introns', 'With introns'), ('flybase', 'Flybase'), ('domains', 'Domains'), ('arcs', 'Arcs'))
            else:
                return (('tiles', 'Tiles'), ('domains', 'Domains'), ('arcs', 'Arcs'))
        return None

    def draw_vlines_only(self):
        return  self.bed_print_options == 'V' and self.track_file.file_type == 'BE'

    def draw_vlines(self):
        return  self.bed_print_options in ('V', 'A') and self.track_file.file_type == 'BE'

    def get_entries(self, chrom, start, end, name_filter = None):
        return  self.track_file.get_entries( chrom, start, end, name_filter)

    def draw_track(self, col, chrom, start, end, interval_start, interval_end, name_filter = None, breakpoint = None, left_side = None, width_prop = DEFAULT_WIDTH_PROP):

        if not self.name_filter:
            name_filter = None

        trackPlot = None

        file_type = self.get_file_type()

        if file_type == 'BE' and self.style in ('tiles', 'introns', 'flybase'):
            trackPlot = PlotBed(model = self)
        elif file_type == 'BE' and self.style == 'arcs':
            trackPlot = PlotArcs(model = self)
        elif file_type == 'BE' and self.style == 'domains':
            trackPlot  = PlotDomains(model = self)
        elif file_type == 'BG':
            trackPlot  =  PlotBedGraph(model = self)
        elif file_type == 'HI' and self.hic_display == 'hic':
            trackPlot = PlotHiCMatrix(model = self)
        elif file_type == 'HI' and self.hic_display == 'v4c':
            trackPlot = PlotVirtualHIC(model = self)            
        elif file_type == 'XA':
            trackPlot  = PlotXAxis(model = self)

        return trackPlot.draw_track(col, chrom, start, end, interval_start, interval_end, name_filter, breakpoint, left_side, width_prop)
    
    @property
    def file_name(self):
        return self.track_file.name


class Eval(models.Model):
    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    track_file =  models.OneToOneField(TrackFile, on_delete = models.PROTECT, related_name='eval')
    name = models.CharField(max_length = 400)
    plot = models.OneToOneField(Plot, on_delete = models.PROTECT, related_name='eval')
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT) 
    auth_cookie = models.CharField(max_length = 60, null=True)

class Phenotype(models.Model):
    db = models.CharField(max_length = 10)
    pheno_id = models.CharField(max_length = 20)
    name = models.CharField(max_length = 200)
    definition = models.CharField(max_length = 1000, null=True)
    comment = models.CharField(max_length = 2000, null=True)
    is_a = models.ManyToManyField('self', symmetrical=False) 
    genes = models.ManyToManyField(Gene, related_name='phenotypes',  through='GeneToPhenotype')

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
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    phenotype = models.ForeignKey(Phenotype, on_delete=models.CASCADE)
    frequent =  models.BooleanField(default = False)

    class Meta:
        ordering = ['gene',]
