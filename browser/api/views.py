from rest_framework import viewsets

from browser.api.serializers import BreakpointSerializer
from browser.models import Breakpoint


class BrowserViewSet(viewsets.ModelViewSet):
    queryset = Breakpoint.objects.all().order_by("sample")
    serializer_class = BreakpointSerializer
    http_method_names = ["get"]
