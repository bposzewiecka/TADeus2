from rest_framework import serializers

from tracks.models import Track


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = [
            "plot",
            "subtracks",
            "track_file",
            "no",
            "title",
            "domains_file",
            "height",
            "inverted",
            "color",
            "edgecolor",
            "colormap",
            "min_value",
            "max_value",
            "transform",
            "bed_display",
            "bed_style",
            "labels",
            "name_filter",
            "chromosome",
            "start_coordinate",
            "end_coordinate",
            "aggregate_function",
            "hic_display",
            "bedgraph_display",
            "bedgraph_type",
            "bedgraph_style",
            "bin_size",
        ]
