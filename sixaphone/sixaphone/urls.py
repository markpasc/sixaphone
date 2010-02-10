from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'sixaphone.views.home', name='home'),
    url(r'^entry/(?P<xid>6a[^/]+)$', 'sixaphone.views.entry', name='entry'),

    url(r'^favorite$', 'sixaphone.views.favorite', name='favorite'),
    url(r'^new_post$', 'sixaphone.views.new_post'),
)
