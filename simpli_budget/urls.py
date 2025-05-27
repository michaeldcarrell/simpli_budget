from django.contrib import admin
from django.urls import path, include
from simpli_budget import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", views.Index.as_view(), name="index"),
    path("logout", views.Logout.as_view(), name="logout"),
]
