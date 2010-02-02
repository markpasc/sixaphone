from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'sixaphone.views.home', name='home'),
)
