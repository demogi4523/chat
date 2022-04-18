from core.settings import DEFAULT_AVATAR_URL
from .models import Avatar


def get_avatar_url(req):
    user = req.user
    url = DEFAULT_AVATAR_URL
    if req.user.is_authenticated:
        url = Avatar.objects.get(user=user).url()
    return {'avatar_url': url}


def get_avatar_username(req):
    user = req.user
    username = 'Anonymous'
    if req.user.is_authenticated:
        username = user.username
    return {'avatar_username': username}
