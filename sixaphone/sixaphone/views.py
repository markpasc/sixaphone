from __future__ import with_statement

import functools
import logging
import re

from django.contrib.auth import get_user
from django.http import HttpResponse
from templateresponse import TemplateResponse
import typepad
from typepadapp.caching import CacheInvalidator
from typepadapp.models import Asset, Favorite
import typepadapp.signals


log = logging.getLogger(__name__)


def oops(fn):
    @functools.wraps(fn)
    def hoops(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception, exc:
            log.exception(exc)
            return HttpResponse('%s: %s' % (type(exc).__name__, str(exc)), status=400, content_type='text/plain')
    return hoops


def audio_events_from_events(events):
    for event in events:
        asset = event.object
        audio = audio_from_asset(asset)
        if audio is None:
            continue
        yield audio, event


def audio_from_asset(asset):
    if asset is None:
        return
    if asset.object_type != 'tag:api.typepad.com,2009:Audio':
        return
    for audio in asset.links['rel__enclosure']:
        return audio


def home(request):
    with typepad.client.batch_request():
        request.user = get_user(request)
        events = request.group.events

    return TemplateResponse(request, 'sixaphone/home.html', {
        'events': events,
        'audio_events': list(audio_events_from_events(events)),
    })


def entry(request, xid):
    with typepad.client.batch_request():
        request.user = get_user(request)
        entry = Asset.get_by_url_id(xid)
        favs = entry.favorites

    return TemplateResponse(request, 'sixaphone/entry.html', {
        'entry': entry,
        'audio': audio_from_asset(entry),
        'favorites': favs,
    })


@oops
def favorite(request):
    if request.method != 'POST':
        return HttpResponse('POST required at this url', status=400, content_type='text/plain')

    action = request.POST.get('action', 'favorite')
    asset_id = request.POST.get('asset_id', '')
    try:
        (asset_id,) = re.findall('6a\w+', asset_id)
    except TypeError:
        raise Http404

    if action != 'favorite':
        return HttpResponse('Unsupported action %r' % action, status=400, content_type='text/plain')

    with typepad.client.batch_request():
        asset = Asset.get_by_url_id(asset_id)
    fav = Favorite()
    fav.in_reply_to = asset.asset_ref
    request.user.favorites.post(fav)
    typepadapp.signals.favorite_created.send(sender=fav, instance=fav, parent=asset,
        group=request.group)

    return HttpResponse('OK', content_type='text/plain')


@oops
def new_post(request):
    if request.method != 'POST':
        return HttpResponse('POST required', status=400, content_type='text/plain')

    # TODO: anything to keep just anyone from poking this endpoint

    CacheInvalidator(key=request.group.events)(None)
    return HttpResponse('OK', content_type='text/plain')
