#!/usr/bin/env python

from __future__ import with_statement

from cgi import parse_qs
from datetime import datetime
import hashlib
import hmac
import logging
import mimetypes
from optparse import OptionParser
from random import choice
import shutil
import string
import sys
from urllib import urlencode
from urlparse import urlparse

import httplib2
from oauth.oauth import OAuthConsumer, OAuthToken
import typepad
import typepad.api

import local_settings


log = logging.getLogger(__name__)


def post_to_typepad(bodyfile, content_type):
    # Upload the asset.
    csr = OAuthConsumer(local_settings.OAUTH_CONSUMER_KEY, local_settings.OAUTH_CONSUMER_SECRET)
    token = OAuthToken(local_settings.OAUTH_SUPERUSER_KEY, local_settings.OAUTH_SUPERUSER_SECRET)
    typepad.client.clear_credentials()
    typepad.client.add_credentials(csr, token, domain='api.typepad.com')
    typepad.client.endpoint = 'https://api.typepad.com/'

    asset = typepad.api.Audio()
    asset.title = "a voice post"
    resp, content = typepad.api.browser_upload.upload(asset, bodyfile,
        post_type='audio',
        content_type=content_type, redirect_to='http://example.com/')

    if resp.status != 302:
        log.error("Unexpected response %d: %s", resp.status, content)
        return

    if 'location' not in resp:
        log.error('No Location in response, only %r', resp.keys())
        return

    loc = resp['location']
    loc_parts = parse_qs(urlparse(loc).query)
    if 'asset_url' not in loc_parts:
        log.error('New location %r has no asset_url', loc)
        return

    loc = loc_parts['asset_url'][0]
    log.info('New asset is %s', loc)


def ping_website(url):
    timestamp = datetime.utcnow().isoformat()
    squib = ''.join(choice(string.letters + string.digits) for i in range(10))

    sign = hmac.new(local_settings.SECRET_KEY, digestmod=hashlib.sha1)
    sign.update(timestamp)
    sign.update(squib)

    body = urlencode({
        'timestamp': timestamp,
        'squib': squib,
        'sign': sign.hexdigest(),
    })

    h = httplib2.Http()
    resp, content = h.request(method='POST', uri=url, body=body)
    if resp.status == 200:
        log.info('Server said yay!')
    else:
        log.warning('When touching the server, got response %d: %s',
            resp.status, content)


def upload_audio(opts, filename=None):
    if filename is not None:
        if filename.endswith('.mp3'):
            content_type = 'audio/mp3'
        else:
            content_type, encoding = mimetypes.guess_type(filename)
            if content_type is None:
                raise ValueError('Could not identify mime type of filename %r' % filename)

        with open(filename) as audio:
            post_to_typepad(audio, content_type)

        # Move the file, if asked.
        if opts.moveto is not None:
            shutil.move(filename, opts.moveto)

    # Tell sixaphone a post was posted (so the caches are invalidated).
    if opts.url is not None:
        ping_website(opts.url)


def main(argv=None):
    if argv is None:
        argv = sys.argv[0:]

    parser = OptionParser()

    parser.add_option('-v', '--verbose', dest="verbose", action="count",
        default=2, help="be chattier (stackable)")
    def quiet(option, opt_str, value, parser):
        parser.values.verbose -= 1
    parser.add_option('-q', '--quiet', action="callback", callback=quiet,
        help="be less chatty (stackable)")

    parser.add_option('--moveto', dest="moveto", action="store",
        default=None, help="After uploading, move the file here (optional)")
    parser.add_option('--url', dest="url", action="store",
        default=None, help="After uploading, touch a server at this URL")

    opts, args = parser.parse_args()

    log_levels = (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)
    log_level = 4 if opts.verbose > 4 else 0 if opts.verbose < 0 else opts.verbose
    logging.basicConfig(level=log_levels[log_level])
    log.setLevel(log_levels[log_level])

    try:
        upload_audio(opts, *args)
    except KeyboardInterrupt:
        return 1
    except Exception, exc:
        log.exception(exc)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
