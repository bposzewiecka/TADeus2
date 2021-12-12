import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from tadeus_portal.settings import TADEUS_DATA_DIR

from .defaults import FILE_SUB_TYPES, FILE_TYPE_BED, FILE_TYPE_BED_GRAPH, FILE_TYPE_HIC, FILE_TYPE_XAXIS, FILE_TYPES

# import pyBigWig


class Species(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Assembly(models.Model):
    species = models.ForeignKey(Species, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, unique=True)

    @property
    def organism(self):
        return self.species.name

    def __str__(self):
        return self.name


class Chromosome(models.Model):
    assembly = models.ForeignKey(Assembly, on_delete=models.CASCADE, related_name="chromosomes")
    name = models.CharField(max_length=50)
    size = models.IntegerField()

    class Meta:
        unique_together = (
            "assembly",
            "name",
        )

    def __str__(self):
        return self.name


class Sample(models.Model):
    name = models.CharField(max_length=200)
    tissue = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    species = models.ForeignKey(Species, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class TrackFile(models.Model):

    assembly = models.ForeignKey(Assembly, on_delete=models.PROTECT)
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=200)
    source_name = models.CharField(max_length=200, null=True, blank=True)
    source_url = models.URLField(max_length=2000, null=True, blank=True)
    file_type = models.CharField(max_length=2, choices=FILE_TYPES)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    public = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    reference = models.CharField(max_length=500, null=True, blank=True)
    bin_sizes = models.CharField(max_length=500, null=True)
    auth_cookie = models.CharField(max_length=60, null=True)
    big = models.BooleanField(default=False)
    bin_size = models.IntegerField(null=True)

    bed_sub_type = models.CharField(max_length=5, choices=FILE_SUB_TYPES, null=True)

    bin_size = models.IntegerField(default=25)

    def get_entries_db(self, chrom, start, end, name_filter=None):

        q = BedFileEntry.objects.filter(subtrack__in=self.subtracks.all()).filter(chrom=chrom)

        if name_filter:
            q = q.filter(name=name_filter)

        q = q.filter(Q(end__range=(start, end)) | Q(start__range=(start, end)) | (Q(start__lte=start) & Q(end__gte=end))).order_by("start", "end")

        return q

    """
    def get_entries_big_bed(self, chrom, start, end, name_filter=None):

        big_bed = pyBigWig.open(self.file_path)

        entries = []

        for big_bed_entry in big_bed.entries(chrom, start, end):

            entry = BedFileEntry(FileEntry)

            data = big_bed_entry[2].split("\t")

            entry.start = big_bed_entry[0]
            entry.end = big_bed_entry[1]

            if self.bed_sub_type in (BED6, BED9, BED12):
                entry.name = data[0]
                entry.score = int(data[1])
                entry.stand = data[2]

            if self.bed_sub_type in (BED9, BED12):
                entry.thick_start = int(data[3])
                entry.thick_end = int(data[4])
                entry.itemRGB = "{:02x}{:02x}{:02x}".format(*map(int, data[5].split(",")))

            if self.bed_sub_type == BED12:
                block_count = int(data[6])
                block_sizes = data[7]
                block_starts = data[8]

            entries.append(entry)

        return entries
        """

    @property
    def organism(self):
        return self.assembly.organism

    """
    def add_subtrack(self, file_path):

        from .readBed import BedOrBedGraphReader

        subtrack = Subtrack(track_file=self, file_path=file_path)

        if self.file_type not in (FILE_TYPE_BED, FILE_TYPE_BED_GRAPH):
            return

        with open(file_path) as handler:
            bed_entries = BedOrBedGraphReader(handler, subtrack)

            @transaction.atomic
            def save_bed_entries(bed_entries):
                for bed_entry in bed_entries:
                    bed_entry.save()

            save_bed_entries(bed_entries)
    """

    def __str__(self):
        return f"Track file id: {self.id}, {self.name} ({self.assembly}, {self.file_type})."

    def read_bed(self, file_handle, return_svs=False):

        from tadeus_portal.utils import save_datasource

        subtrack = Subtrack(track_file=self)
        subtrack.save()

        return save_datasource(subtrack, file_handle, return_svs)

    def get_file_paths(self):

        return [subtrack.get_file_path() for subtrack in self.subtracks.all()]

    @property
    def get_long_file_type_name(self):
        if self.file_type == FILE_TYPE_BED:
            return "Bed"
        if self.file_type == FILE_TYPE_BED_GRAPH:
            return "Bedgraph"
        if self.file_type == FILE_TYPE_HIC:
            return "HiC"
        if self.file_type == FILE_TYPE_XAXIS:
            return "XAxis"


class Subtrack(models.Model):

    track_file = models.ForeignKey(TrackFile, on_delete=models.CASCADE, related_name="subtracks")
    file_path = models.CharField(max_length=500, null=True)
    rgb = models.CharField(max_length=7, null=True)
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT, related_name="subtracks", null=True)
    name = models.CharField(max_length=500, null=True)
    default = models.BooleanField(default=False)

    def read_bed(self):

        from tadeus_portal.utils import save_datasource

        with open(self.get_file_path()) as file_handle:
            save_datasource(self, file_handle)

    def get_file_path(self):
        return os.path.join(TADEUS_DATA_DIR, self.file_path) if self.file_path else ""


class FileEntry(models.Model):

    subtrack = models.ForeignKey(Subtrack, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s_file_entries")

    chrom = models.CharField(max_length=50)
    start = models.IntegerField()
    end = models.IntegerField()
    labels = models.BooleanField(default=False)

    STRAND_TYPES = (
        ("+", "+"),
        ("-", "-"),
        (".", "."),
    )

    strand = models.CharField(max_length=1, choices=STRAND_TYPES, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.chrom}:{self.start}-{self.end}"

    def __len__(self):
        return self.end - self.start


class BedFileEntry(FileEntry):

    name = models.CharField(max_length=100, null=True)
    score = models.FloatField(null=True)

    thick_start = models.IntegerField(null=True)
    thick_end = models.IntegerField(null=True)
    itemRGB = models.CharField(max_length=6, null=True)
    block_count = models.IntegerField(null=True)
    block_sizes = models.CharField(max_length=400, null=True)
    block_starts = models.CharField(max_length=400, null=True)

    def get_block_sizes(self):
        return list(map(int, self.block_sizes.split(",")))

    def get_block_starts(self):
        return list(map(int, self.block_starts.split(",")))

    def get_adj_left(self, n=1000000):
        return max(0, self.start - n)

    def get_adj_right(self, n=1000000):
        return self.end + n
