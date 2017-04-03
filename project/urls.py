from django.conf.urls import patterns, url

urlpatterns = patterns('polygonproduction.views',
    url(r'^$', 'render_pamphlet', {'page': 'home.html'}),
    url(r'^home.html$',      'render_pamphlet', name='home'),
    url(r'^stage.html$',     'render_pamphlet', name='stage'),
    url(r'^retail.html$',    'render_pamphlet', name='retail'),
    url(r'^karaoke.html$',   'render_pamphlet', name='karaoke'),
    url(r'^contact.html$',   'render_pamphlet', name='contact'),
    url(r'^refresh.html$',   'refresh_view',    name='refresh'),
    url(r'^projects.html$',  'render_albums',   name='projects'),
    url(r'^projects/(\w+)/$','render_album', name='album'),
    url(r'^projects/(\w+)/(\d+)/$','render_photo', name='photo'),
)
