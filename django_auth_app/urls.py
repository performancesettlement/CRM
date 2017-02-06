from django.conf.urls import url
from django_auth_app import views as app_views
from rest_framework import routers
router = routers.DefaultRouter()
urlpatterns = [
    url(r'^login/$', app_views.login_user, name='login'),
    url(r'^logout/$', app_views.logout_user, name='logout'),
]
