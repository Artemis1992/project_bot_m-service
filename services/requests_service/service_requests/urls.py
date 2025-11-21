# service_requests/urls.py
from django.contrib import admin
from django.urls import path, include

from .monitoring import health_check, readiness_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("requests_app.urls")),
    path("health/", health_check, name="health"),
    path("ready/", readiness_check, name="readiness"),
]
