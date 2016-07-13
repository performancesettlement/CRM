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
    url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/', include('allauth.urls')),

    url(r'^account/', include('django_auth_app.urls', namespace='django_auth_app')),

    url(r'^cms-admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^avatar/', include('avatar.urls')),

    url(r'^$', views.index, name='index'),
    url(r'^home/$', login_required(FileSearchView.as_view()), name='home'),
    url(r'^home/?$', login_required(FileSearchView.as_view()), name='home_search'),
    url(r'^help/$', views.help, name="help"),
    url(r'^terms/$', views.terms, name="terms"),
    url(r'^display-log/$', views.display_log, name="display_log"),
    url(r'^erase-log/$', views.erase_log, name="erase_log"),

    url(r'^file/(?P<file_id>\d+)/$', views.file_detail, name='file_detail'),
    url(r'^file/add/$', views.file_add, name='file_add'),
    url(r'^file/recents/$', views.files_recent, name='recent_files'),
    url(r'^file/(?P<file_id>\d+)/edit/remove-participant/$', views.file_remove_participant, name='file_remove_participant'),
    url(r'^file/(?P<file_id>\d+)/edit/add-participant/$', views.file_add_participant, name='file_add_participant'),
    url(r'^file/(?P<file_id>\d+)/edit/$', views.file_edit, name='file_edit'),
    url(r'^file/(?P<file_id>\d+)/upload/$', views.documents_upload, name='documents_upload'),
    url(r'^file/import/$', views.file_import, name='file_import'),
    url(r'^file/import/check/$', views.check_file_import, name='file_import_check'),
    url(r'^file/import/download-sample/$', views.download_file_import_sample, name='download_file_import_sample'),
    url(r'^delete-documents/(?P<document_id>\d+)/$', views.documents_delete, name='documents_delete'),
    url(r'^file/(?P<file_id>\d+)/message/$', views.messages_upload, name='messages_upload'),
    url(r'^completed_by_status/?$', ajax.get_completed_by_file_status, name='completed_by_status'),
    url(r'^contact/add/$', views.add_contact, name='add_contact'),
    url(r'^contacts/$', views.list_contacts, name='list_contacts'),
    url(r'^contacts/$', views.list_contacts, name='new_list'),  # TODO: Create proper view and template.
    url(r'^campaigns/$', views.list_contacts, name='campaigns'),  # TODO: Create proper view and template.
    url(r'^workflow/$', views.list_contacts, name='workflow'),  # TODO: Create proper view and template.
    url(r'^dataSources/$', views.list_contacts, name='data_sources'),  # TODO: Create proper view and template.
    url(r'^client/add/$', views.add_client_ajax, name='ajax_client_add'),
    # url(r'^client/import/$', views.client_import, name='client_import'),
    # url(r'^client/import/check/$', views.check_client_import, name='client_import_check'),
    # url(r'^client/import/download-sample/$', views.download_client_import_sample, name='download_client_import_sample'),
    url(r'^profile/impersonate_user/$', views.impersonate_user, name='impersonate_user'),
    url(r'^profile/stop_impersonate_user/$', views.stop_impersonate_user, name='stop_impersonate_user'),
    url(r'^admin/update_preferences_for_section_collapsed_state/$', ajax.update_preferences_for_section_collapsed_state, name='update_section_collapsed_state'),
    url(r'^admin/get_preferences_for_sections_collapsed_state/$', ajax.get_preferences_for_sections_collapsed_state, name='get_sections_collapsed_state'),
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

