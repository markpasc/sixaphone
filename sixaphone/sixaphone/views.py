from __future__ import with_statement

import functools
import hashlib
import hmac
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user
from django.core.cache import cache
from django.http import HttpResponse
import simplejson as json
from templateresponse import TemplateResponse
import typepad
from typepadapp.caching import CacheInvalidator
from typepadapp.models import Asset, Favorite
import typepadapp.signals

from sixaphone.models import Tag


log = logging.getLogger(__name__)

ONE_DAY = 86400


def oops(fn):
    @functools.wraps(fn)
    def hoops(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception, exc:
            log.exception(exc)
            return HttpResponse('%s: %s' % (type(exc).__name__, str(exc)), status=400, content_type='text/plain')
    return hoops


def audio_entries_from_entries(entries):
    for entry in entries:
        audio = audio_from_asset(entry)
        if audio is None:
            continue
        yield audio, entry


def audio_from_asset(asset):
    if asset is None:
        return
    if asset.object_type != 'tag:api.typepad.com,2009:Audio':
        return
    for audio in asset.links['rel__enclosure']:
        return audio


def add_tags_to_entries(audio_entries):
    xids = list()
    entry_with_xid = dict()
    for audio, entry in audio_entries:
        xid = entry.xid
        xids.append(xid)
        entry_with_xid[xid] = entry

    tags = Tag.objects.filter(asset__in=xids)
    for tag in tags:
        asset = entry_with_xid[tag.asset]
        try:
            asset.tags.append(tag)
        except AttributeError:
            asset.tags = [tag]


def home(request, page=1):
    page = int(page)
    start_index = (page - 1) * 10 + 1
    max_results = 10

    with typepad.client.batch_request():
        request.user = get_user(request)
        events = request.group.events.filter(max_results=max_results, start_index=start_index)

    audio_entries = list(audio_entries_from_entries(event.object for event
        in events if event.object))
    add_tags_to_entries(audio_entries)

    return TemplateResponse(request, 'sixaphone/home.html', {
        'page': page,
        'prev_page': page - 1 if page > 1 else False,
        'next_page': page + 1 if start_index + max_results < events.total_results else False,
        'stardex': start_index + max_results,
        'totresu': events.total_results,
        'audio_entries': audio_entries,
    })


@oops
def asset_meta(request, fresh=False):
    if not request.user.is_authenticated():
        return HttpResponse('silly rabbit, asset_meta is for authenticated users',
            status=400, content_type='text/plain')

    user_id = request.user.xid
    cache_key = 'favorites:%s' % user_id
    favs = None if fresh else cache.get(cache_key)

    if favs is None:
        log.debug("Oops, going to server for %s's asset_meta", request.user.xid)

        fav_objs = {}
        html_ids = request.POST.getlist('asset_id')
        with typepad.client.batch_request():
            for html_id in html_ids:
                assert html_id.startswith('asset-')
                xid = html_id[6:]
                fav_objs[html_id] = Favorite.head_by_user_asset(user_id, xid)

        favs = list(html_id for html_id, fav_obj in fav_objs.items()
            if fav_obj.found())
        if not fresh:
            cache.set(cache_key, favs, ONE_DAY)
    else:
        log.debug('Yay, returning asset_meta for %s from cache', request.user.xid)

    favs = dict((html_id, {"favorite": True}) for html_id in favs)
    return HttpResponse(json.dumps(favs), content_type='application/json')


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


def tag(request, tag, page=1):
    page = int(page)
    first = (page - 1) * 10
    last = first + 10 + 1

    tags = Tag.objects.filter(tag=tag).order_by('-created')[first:last]
    has_next_page = True if len(tags) > 10 else False
    tags = tags[:10]

    with typepad.client.batch_request():
        request.user = get_user(request)
        assets = [Asset.get_by_url_id(tagject.asset) for tagject in tags]

    audio_entries = list(audio_entries_from_entries(assets))
    add_tags_to_entries(audio_entries)

    return TemplateResponse(request, 'sixaphone/tag.html', {
        'audio_entries': audio_entries,
        'tag': tag,
        'page': page,
        'prev_page': page - 1 if page > 1 else False,
        'next_page': page + 1 if len(tags) > 10 else False,
    })


@oops
def favorite(request):
    if request.method != 'POST':
        return HttpResponse('POST required at this url', status=400, content_type='text/plain')
    if not request.user.is_authenticated():
        return HttpResponse('silly rabbit, only signed-in folks can favorite', status=400, content_type='text/plain')

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
def add_tags(request):
    if request.method != 'POST':
        return HttpResponse('POST required at this url', status=400, content_type='text/plain')
    if not request.user.is_authenticated():
        return HttpResponse('silly rabbit, only signed-in folks can add tags', status=400, content_type='text/plain')

    action = request.POST.get('action', 'add')
    asset_id = request.POST.get('asset_id', '')
    tags = request.POST.get('tags', '')
    try:
        (asset_id,) = re.findall('6a\w+', asset_id)
    except TypeError:
        raise Http404

    if action != 'add':
        return HttpResponse('Unsupported action %r' % action, status=400, content_type='text/plain')
    if not tags:
        return HttpResponse('Unsupported tags %r' % tags, status=400, content_type='text/plain')

    with typepad.client.batch_request():
        request.user = get_user(request)
    xid = request.user.xid
    by_name = request.user.display_name

    result = list()
    for tag in tags.split(','):
        tag = tag.strip()
        t = Tag(asset=asset_id, tag=tag, by=xid, by_name=by_name)
        t.save()
        result.append({'tag': tag, 'name': by_name})

    return HttpResponse(json.dumps(result), content_type='application/javascript+json')


def uncache_favorites(sender, instance, **kwargs):
    cache_key = 'favorites:%s' % instance.author.xid
    cache.delete(cache_key)


typepadapp.signals.favorite_created.connect(uncache_favorites)
typepadapp.signals.favorite_deleted.connect(uncache_favorites)


@oops
def new_post(request):
    if request.method != 'POST':
        return HttpResponse('POST required', status=400, content_type='text/plain')

    # Since we're just protecting against cache misses, do something pretty
    # simple to protect this endpoint.
    signer = hmac.new(settings.SECRET_KEY, digestmod=hashlib.sha1)
    signer.update(request.POST['timestamp'])
    signer.update(request.POST['squib'])
    expected = signer.hexdigest()

    sign = request.POST['sign']
    if sign != expected:
        return HttpResponse('Invalid signature :(', status=400, content_type='text/plain')

    CacheInvalidator(key=request.group.events)(None)
    return HttpResponse('OK', content_type='text/plain')
