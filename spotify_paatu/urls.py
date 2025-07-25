from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from game.views import google_site_verification, sitemap_view, robots_txt, language_redirect, custom_login_redirect, store_language, google_login_redirect


urlpatterns = [
    path('admin/', admin.site.urls),

    # Language-specific URLs
    path('tamil/', include('game.urls'), {'language': 'tamil'}),
    path('english/', include('game.urls'), {'language': 'english'}),
    path('hindi/', include('game.urls'), {'language': 'hindi'}),

    # Default redirect to Tamil (backward compatibility)
    path('', language_redirect, name='language_redirect'),

    # Global Community (not language-specific)
    path('community/', include('game.community_urls')),

    # Custom login redirect for language selection
    path('login-redirect/', custom_login_redirect, name='custom_login_redirect'),
    path('store-language/', store_language, name='store_language'),
    path('google-redirect/', google_login_redirect, name='google_login_redirect'),

    # Other URLs
    path('accounts/', include('allauth.urls')),
    path('googled2c2d6345bb867a9.html', google_site_verification),
    path('sitemap.xml', sitemap_view),
    path("robots.txt", robots_txt),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)