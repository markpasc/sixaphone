from __future__ import with_statement

from django.contrib.auth import get_user
from templateresponse import TemplateResponse
import typepad


def audio_events_from_events(events):
    for event in events:
        obj = event.object
        if obj is None:
            continue
        if obj.object_type != 'tag:api.typepad.com,2009:Audio':
            continue
        for audio in obj.links['rel__enclosure']:
            yield audio, event
            break  # only need the first


def home(request):
    with typepad.client.batch_request():
        request.user = get_user(request)
        events = request.group.events

    return TemplateResponse(request, 'sixaphone/home.html', {
        'events': events,
        'audio_events': audio_events_from_events(events),
    })
