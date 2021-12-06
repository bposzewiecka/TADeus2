from rest_framework import serializers

from browser.models import Breakpoint


class BreakpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breakpoint
        fields = ["sample", "left_chrom", "left_coord", "left_inverse", "right_chrom", "right_coord", "right_inverse", "owner", "public", "assembly"]
