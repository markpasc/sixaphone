from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'sixaphone.views.home', name='home'),
    url(r'^page/(?P<page>\d+)$', 'sixaphone.views.home', name='archive'),
    url(r'^entry/(?P<xid>6a[^/]+)$', 'sixaphone.views.entry', name='entry'),

    url(r'^favorite$', 'sixaphone.views.favorite', name='favorite'),
    url(r'^asset_meta$', 'sixaphone.views.asset_meta', name='asset_meta'),
    url(r'^new_post$', 'sixaphone.views.new_post'),
)
