import os

import yaml
from django.contrib.auth.models import User
from django.db import transaction

from datasources.models import Assembly, Subtrack, TrackFile
from tadeus_portal.settings import TADEUS_DATA_DIR


@transaction.atomic
def add_track_files(fn):

    with open(fn) as f:

        for track_file_data in yaml.load(f, Loader=yaml.FullLoader)["tracks"]:
            add_track_file(track_file_data)


def add_track_file(track_file_data):

    track_file = TrackFile()
    track_file.assembly = Assembly.objects.get(name=track_file_data["assembly"])
    track_file.name = track_file_data["name"]

    if "id" in track_file_data:
        track_file.id = track_file_data["id"]

    if "source_name" in track_file_data:
        track_file.source_name = track_file_data["source_name"]

    if "source_url" in track_file_data:
        track_file.source_url = track_file_data["source_url"]

    track_file.owner = User.objects.get(username=track_file_data["owner"])

    track_file.file_type = track_file_data["file_type"]

    if "bed_sub_type" in track_file_data:
        track_file.bed_sub_type = track_file_data["bed_sub_type"]

    track_file.public = track_file_data["public"]
    track_file.approved = track_file_data["approved"]

    if "big" in track_file_data:
        track_file.big = track_file_data["big"]

    if "bin_size" in track_file_data:
        track_file.bin_size = track_file_data["bin_size"]

    track_file.save()

    if "subtracks" in track_file_data:
        for subtrack_data in track_file_data["subtracks"]:
            add_subtracks(subtrack_data, track_file)


def add_subtracks(subtrack_data, track_file):

    subtrack = Subtrack()
    subtrack.file_path = subtrack_data["file_path"]

    if not subtrack.file_path.startswith("http"):
        subtrack.file_path = subtrack.file_path

    if "rgb" in subtrack_data:
        subtrack.rgb = subtrack_data["rgb"]

    if "default" in subtrack_data:
        subtrack.default = subtrack_data["default"]

    if "name" in subtrack_data:
        subtrack.name = subtrack_data["name"]

    # if 'sample' in subtrack_data:
    #    subtrack.sample = subtrack_data['sample']

    subtrack.track_file = track_file

    if not subtrack.file_path.startswith("http") and not track_file.big and track_file.file_type in ("BE", "BG"):
        subtrack.read_bed()

    subtrack.save()


globals().update(locals())

add_track_files(os.path.join(TADEUS_DATA_DIR, "hg38", "tracks.yaml"))
