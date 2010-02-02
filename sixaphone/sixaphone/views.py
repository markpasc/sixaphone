from __future__ import with_statement

from django.contrib.auth import get_user
from templateresponse import TemplateResponse
import typepad


def home(request):
    with typepad.client.batch_request():
        request.user = get_user(request)
        events = request.group.events

    return TemplateResponse(request, 'sixaphone/home.html', {
        'events': events,
    })
