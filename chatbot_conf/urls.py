from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
        # Redirects to "admin/"
        path("", lambda _: redirect("admin/")),  
        # Routes
        path("admin/", admin.site.urls),
        path("content/", include("content.urls")),
        path("ai/", include("ai.urls")),
    ]