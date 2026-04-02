from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),

    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("patients/", include("apps.patients.urls")),
    path("waiting-room/", include("apps.waiting_room.urls")),
    path("consultations/", include("apps.consultations.urls")),
    path("laboratory/", include("apps.laboratory.urls")),
    path("pharmacy/", include("apps.pharmacy.urls")),
    path("billing/", include("apps.billing.urls")),
    path("admissions/", include("apps.admissions.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)