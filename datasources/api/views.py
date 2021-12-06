from rest_framework import viewsets

from datasources.models import Assembly, Sample, Species, TrackFile

from .serializers import AssemblySerializer, SampleSerializer, SpeciesSerializer, TrackFileSerializer


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


class TrackFileViewSet(viewsets.ModelViewSet):
    queryset = TrackFile.objects.all().order_by("name")
    serializer_class = TrackFileSerializer
    # http_method_names = ['get']
