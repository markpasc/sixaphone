from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'sixaphone.views.home', name='home'),
    url(r'^new_post$', 'sixaphone.views.new_post'),
)
