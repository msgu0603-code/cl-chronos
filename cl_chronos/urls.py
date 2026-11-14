"""Root URL configuration for the CL-CHRONOS backend."""

from api.views import CustomTokenObtainPairView
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/v1/token/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'api/v1/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path('api/v1/', include('api.urls')),
]