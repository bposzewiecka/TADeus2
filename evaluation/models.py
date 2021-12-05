from django.db import models
from django.contrib.auth.models import User
from tracks.models import TrackFile
from plots.models import Plot
from datasources.models import Assembly


class Evaluation(models.Model):
    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    track_file =  models.OneToOneField(TrackFile, on_delete = models.PROTECT, related_name = 'eval')
    name = models.CharField(max_length = 400)
    plot = models.OneToOneField(Plot, on_delete = models.PROTECT, related_name = 'eval')
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT) 
    auth_cookie = models.CharField(max_length = 60, null=True)