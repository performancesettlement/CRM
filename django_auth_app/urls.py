
from django.conf.urls import include, url
from django_auth_app import views as app_views
from django_auth_app.API import api
from rest_framework import routers
router = routers.DefaultRouter()
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/auth/$', api.AuthView.as_view(), name='authenticate'),
    url(r'^api/users/$', api.UserView.as_view(), name='users'),
    url(r'^api/profile/$', api.UserProfileView.as_view(), name='user_profile'),
    url(r'^api/upload/$', api.UploadFileView.as_view(), name='upload_view'),
    url(r'^api/confirm/(?P<activation_key>\w+)/', api.ConfirmView.as_view(), name='confirm_view'),

    url(r'^login/$', app_views.login_user, name="login"),
    url(r'^logout/$', app_views.logout_user, name="logout"),
    url(r'^register/$', app_views.register_user, name="register"),

    url(r'^confirm/(?P<activation_key>\w+)/', app_views.confirm_account, name="confirm"),
    url(r'^recover/$', app_views.recover_password, name="recover"),
    url(r'^new_password/(?P<recover_key>\w+)/', app_views.confirm_recover_account, name="confirm_recover"),
    url(r'^update_password/$', app_views.update_password, name="update_password"),
    url(r'^profile/edit/$', app_views.profile_edit_view, name="profile_edit"),
    url(r'^profile/edit/upload-picture/$', app_views.profile_upload_picture, name="profile_upload_picture"),
    url(r'^profile/', app_views.my_profile_view, name="my_profile"),
]
