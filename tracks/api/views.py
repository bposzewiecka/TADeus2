from rest_framework import viewsets

from tracks.api.serializers import TrackSerializer
from tracks.models import Track


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all().order_by("plot")
    serializer_class = TrackSerializer
    # http_method_names = ['get']
