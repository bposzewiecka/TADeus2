from django.db import models
from django.contrib.auth.models import User

from datasources.models import Assembly

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
