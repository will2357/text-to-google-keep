from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("import/", views.import_create, name="import_create"),
    path("oauth/start/", views.oauth_start, name="oauth_start"),
    path("oauth/callback/", views.oauth_callback, name="oauth_callback"),
]
