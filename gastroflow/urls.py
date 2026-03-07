from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("menu/", include("menu.urls")),
    path("order/", include("order.urls")),
    path("", include("service.urls")),
    path("kitchen/", include("kitchen.urls")),
    path("bar/", include("bar.urls")),
    path("worker/", include("worker.urls", namespace="gf-worker")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("silk/", include("silk.urls", namespace="silk")),
    ]
