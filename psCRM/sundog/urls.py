from sundog import views
import settings
"""lotonow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url, patterns
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from sundog.views import FileSearchView
from sundog import ajax
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

urlpatterns = [
    #admin site url
    url(r'^admin/', include(admin.site.urls)),

    #auth urls
    url(r'^account/', include('django_auth_app.urls', namespace='django_auth_app')),

    #cms urls
    url(r'^cms-admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    #Avatar
    url(r'^avatar/', include('avatar.urls')),

    #site urls
    url(r'^$', views.index, name='index'),
    url(r'^home/$', login_required(FileSearchView.as_view()), name='home'),
    url(r'^home/?$', login_required(FileSearchView.as_view()), name='home_search'),
    url(r'^help/$', views.help, name="help"),
    url(r'^display-log/$', views.display_log, name="display_log"),
    url(r'^erase-log/$', views.erase_log, name="erase_log"),
    #url(r'^areas_by_state/?$', ajax.areas_by_state, name='areas_by_state'),
    #url(r'^communities_by_area/?$', ajax.communities_by_area, name='communities_by_area'),
    url(r'^file/(?P<file_id>\d+)/$', views.file_detail, name='file_detail'),
    url(r'^file/(?P<file_id>\d+)/edit/$', views.file_edit, name='file_edit'),
    url(r'^file/add/$', views.file_add, name='file_add'),
    url(r'^file/recents/$', views.files_recent, name='recent_files'),
    url(r'^file/(?P<file_id>\d+)/edit/remove-participant/$', views.file_remove_participant, name='file_remove_participant'),
    url(r'^file/(?P<file_id>\d+)/edit/add-participant/$', views.file_add_participant, name='file_add_participant'),
    url(r'^file/(?P<file_id>\d+)/upload/$', views.documents_upload, name='documents_upload'),
    url(r'^file/import/$', views.file_import, name='file_import'),
    url(r'^file/import/check/$', views.check_file_import, name='file_import_check'),
    url(r'^file/import/download-sample/$', views.download_file_import_sample, name='download_file_import_sample'),
    url(r'^delete-documents/(?P<document_id>\d+)/$', views.documents_delete,
        name='documents_delete'),
    url(r'^file/(?P<file_id>\d+)/message/$', views.messages_upload, name='messages_upload'),
    url(r'^completed_by_status/?$', ajax.get_completed_by_file_status, name='completed_by_status'),
    url(r'^client/add/$', views.add_client_ajax, name='ajax_client_add'),
    url(r'^client/import/$', views.client_import, name='client_import'),
    url(r'^client/import/check/$', views.check_client_import, name='client_import_check'),
    url(r'^client/import/download-sample/$', views.download_client_import_sample, name='download_client_import_sample'),
    #url(r'^set-timezone/$', views.set_timezone, name='set_timezone'),
    #url(r'^files/search/?$', FileSearchView.as_view(), name='files_search_view'),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
]

handler404 = 'sundog.views.render404'

if settings.DEBUG:
    urlpatterns += patterns('',
                   url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
                       {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                   )

