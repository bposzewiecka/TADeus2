from rest_framework import viewsets
from rest_framework.response import Response

from tracks.api.serializers import TrackSerializer
from tracks.models import (
    AGGREGATE_FUNCTIONS_OPTIONS,
    BED_DISPLAY_OPTIONS,
    BED_STYLE_OPTIONS,
    BEDGRAPH_DISPLAY_OPTIONS,
    BEDGRAPH_STYLE_OPTIONS,
    BEDGRAPH_TYPE_OPTIONS,
    COLOR_MAP_OPTIONS,
    HIC_DISPLAY_OPTIONS,
    TRANSFORM_OPTIONS,
    Track,
)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all().order_by("plot")
    serializer_class = TrackSerializer
    # http_method_names = ['get']


class TrackParametersOptionsViewSet(viewsets.ViewSet):
    def list(self, request, format=None):

        content = {
            "TRANSFORM_OPTIONS": TRANSFORM_OPTIONS,
            "BED_DISPLAY_OPTIONS": BED_DISPLAY_OPTIONS,
            "BED_STYLE_OPTIONS": BED_STYLE_OPTIONS,
            "AGGREGATE_FUNCTIONS_OPTIONS": AGGREGATE_FUNCTIONS_OPTIONS,
            "HIC_DISPLAY_OPTIONS": HIC_DISPLAY_OPTIONS,
            "BEDGRAPH_DISPLAY_OPTIONS": BEDGRAPH_DISPLAY_OPTIONS,
            "BEDGRAPH_TYPE_OPTIONS": BEDGRAPH_TYPE_OPTIONS,
            "BEDGRAPH_STYLE_OPTIONS": BEDGRAPH_STYLE_OPTIONS,
            "COLOR_MAP_OPTIONS": COLOR_MAP_OPTIONS,
        }

        return Response(content)
