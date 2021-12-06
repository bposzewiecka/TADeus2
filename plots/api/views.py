from rest_framework import viewsets

from plots.models import Plot

from .serializers import PlotSerializer


class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.all().order_by("name")
    serializer_class = PlotSerializer
