from rest_framework import viewsets

from tadeus.api.serializers import AssemblySerializer, PlotSerializer, SampleSerializer, SpeciesSerializer, TrackFileSerializer
from tadeus.models import Assembly, Plot, Sample, Species, TrackFile


class SpeciesViewSet(viewsets.ModelViewSet):
    queryset = Species.objects.all().order_by("name")
    serializer_class = SpeciesSerializer
    http_method_names = ["get"]


class AssemblyViewSet(viewsets.ModelViewSet):
    queryset = Assembly.objects.all().order_by("name")
    serializer_class = AssemblySerializer
    # http_method_names = ['get']


class SampleViewSet(viewsets.ModelViewSet):
    queryset = Sample.objects.all().order_by("name")
    serializer_class = SampleSerializer
    # http_method_names = ['get']


class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.all().order_by("name")
    serializer_class = PlotSerializer


class TrackFileViewSet(viewsets.ModelViewSet):
    queryset = TrackFile.objects.all().order_by("name")
    serializer_class = TrackFileSerializer
    # http_method_names = ['get']
