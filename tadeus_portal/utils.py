import random
import string
from io import StringIO, TextIOWrapper
from itertools import zip_longest

from django.db import transaction
from django.db.models import Q
from django.utils.html import format_html

from datasources.readBed import BedOrBedGraphReader, ReadBedOrBedGraphException


def generateRandomString(n):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def get_auth_cookie(request):

    if "auth" not in request.session:
        request.session["auth"] = generateRandomString(n=25)

    request.session.set_expiry(356 * 24 * 60 * 60)

    return request.session["auth"]


def is_object_readonly(request, obj):
    auth_cookie = get_auth_cookie(request)

    return (request.user.is_authenticated and request.user != obj.owner) or (not request.user.is_authenticated and auth_cookie != obj.auth_cookie)


def only_public_or_user(request):
    user = request.user if request.user.is_authenticated else None

    if request.user.is_authenticated:
        return Q(public=True) | Q(owner=user)

    auth_cookie = get_auth_cookie(request)

    return Q(public=True) | Q(auth_cookie=auth_cookie)


def set_owner_or_cookie(request, p_obj):

    auth_cookie = get_auth_cookie(request)

    if request.user.is_authenticated:
        p_obj.owner = request.user
    else:
        p_obj.auth_cookie = auth_cookie


def getLink(link, icon):
    return format_html('<a href="{link}"><i class="fas ' + icon + '"></i></a>', link=link)


def split_seq(seq, n):
    s = [seq[i::n] for i in range(n)]
    return [[i for i in row if i is not None] for row in zip_longest(*s)]


@transaction.atomic
def save_datasource(track_file, file_handle, eval=False):

    if file_handle:
        reader = BedOrBedGraphReader(file_handle=file_handle, track_file=track_file)

    track_file.save()

    if file_handle:
        for bed_entry in reader:
            bed_entry.save()


def get_file_handle(p_type, form):

    if p_type == "file":
        f = form.files["file"]
        return TextIOWrapper(f.file)
    elif p_type == "text":
        text = form.data["text"]
        if len(text) == 0:
            raise ReadBedOrBedGraphException("Paste in data in BED or BEDGraph format.")
        return StringIO(text)
    else:
        return None
