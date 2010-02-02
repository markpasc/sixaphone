#!/usr/bin/env python

from __future__ import with_statement

from cgi import parse_qs
import logging
import mimetypes
from optparse import OptionParser
import sys
from urlparse import urlparse

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


def upload_audio(opts, filename):
    if filename.endswith('.mp3'):
        content_type = 'audio/mp3'
    else:
        content_type, encoding = mimetypes.guess_type(filename)
        if content_type is None:
            raise ValueError('Could not identify mime type of filename %r' % filename)

    with open(filename) as audio:
        post_to_typepad(audio, content_type)

    # TODO: Tell sixaphone a post was posted (so the caches are invalidated).


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
