from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from capomastro.views import HomeView
from capomastro.api import router


admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'capomastro.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^', include('projects.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^', include('social_auth.urls')),
    url(r'^jenkins/', include('jenkins.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
