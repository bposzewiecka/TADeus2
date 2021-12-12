from django.contrib.auth.models import User
from django.db import models

from datasources.models import Assembly, BedFileEntry
from plots.models import Plot
from tracks.models import TrackFile

from .defaults import SV_TYPES


class Evaluation(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    track_file = models.OneToOneField(TrackFile, on_delete=models.PROTECT, related_name="eval")
    name = models.CharField(max_length=400)
    plot = models.OneToOneField(Plot, on_delete=models.PROTECT, related_name="eval")
    assembly = models.ForeignKey(Assembly, on_delete=models.PROTECT)
    auth_cookie = models.CharField(max_length=60, null=True)


class SVEntry(BedFileEntry):
    sv_type = models.IntegerField(choices=SV_TYPES)
    TADA_score = models.FloatField(null=True)
    ClassifyCNV = models.CharField(max_length=20, null=True)
    TADeus_score = models.FloatField(null=True)


class SVPropertyType(models.Model):
    name = models.CharField(max_length=50)


class SVProperty(models.Model):
    file_entry = models.ForeignKey(SVEntry, on_delete=models.CASCADE, related_name="properties")
    file_entry_property_type = models.ForeignKey(SVPropertyType, on_delete=models.CASCADE, related_name="properties")
    value = models.CharField(max_length=50)
