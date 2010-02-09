from __future__ import with_statement

from django.contrib.auth import get_user
from django.http import HttpResponse
from templateresponse import TemplateResponse
import typepad
from typepadapp.caching import CacheInvalidator
from typepadapp.models import Asset


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


def new_post(request):
    if request.method != 'POST':
        return HttpResponse('POST required', status=400, content_type='text/plain')

    # TODO: anything to keep just anyone from poking this endpoint

    CacheInvalidator(key=request.group.events)(None)
    return HttpResponse('OK', content_type='text/plain')
