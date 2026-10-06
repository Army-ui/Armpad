from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ═══ i18n — DOIT être en premier ═══
    path('i18n/', include('django.conf.urls.i18n')),

    # ═══ Admin ═══
    path('admin/', admin.site.urls),

    # ═══ API Docs ═══
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ═══ JWT ═══
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ═══ API REST ═══
    path('api/v1/', include('works.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/subscriptions/', include('subscriptions.urls')),

    # ═══ Auth HTML (login/logout/password-reset) ═══
    path('', include('users.web_urls')),

    # ═══ Site web (DOIT être en dernier) ═══
    path('', include('web.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
