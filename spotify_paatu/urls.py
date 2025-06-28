from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from game.views import google_site_verification, sitemap_view, robots_txt


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game.urls')),
    path('accounts/', include('allauth.urls')),
    path('googled2c2d6345bb867a9.html', google_site_verification),
    path('sitemap.xml', sitemap_view),
    path("robots.txt", robots_txt),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)