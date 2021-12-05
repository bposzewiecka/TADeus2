import random
import string

from django.db.models import Q
from django.utils.html import format_html


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
