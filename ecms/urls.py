from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

# Customize admin site branding
admin.site.site_header = "DataNest Administration"
admin.site.site_title = "DataNest Admin"
admin.site.index_title = "Welcome to DataNest Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('accounts.urls')),
    path('documents/', include('documents.urls')),
    path('workflows/', include('workflows.urls')),
    path('notifications/', include('notifications.urls')),
    path('folders/', include('folders.urls')),
    path('versions/', include('versions.urls')),
    path('reports/', include('reports.urls')),
    path('api/', include('documents.api.urls')),
    path('api/', include('workflows.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
