from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("menu/", include("menu.urls", namespace="gf-menu")),
    path("order/", include("order.urls")),
    path("", include("service.urls")),
    path("worker/", include("worker.urls", namespace="gf-worker")),
    path("display/", include("consumers.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("silk/", include("silk.urls", namespace="silk")),
    ]
