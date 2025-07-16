from django.http import HttpResponsePermanentRedirect

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class WWWRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(':')[0]
        if host == 'webzombies.pythonanywhere.com':
            if not request.is_secure():
                url = request.build_absolute_uri(request.get_full_path())
                secure_url = url.replace('http://', 'https://')
                return redirect(secure_url)
        # Explicitly allow HTTP for localhost and 127.0.0.1
        elif host in ['localhost', '127.0.0.1'] and request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            non_secure_url = url.replace('https://', 'http://')
            return redirect(non_secure_url)
        return self.get_response(request)


class LanguageRedirectMiddleware:
    """Simple middleware to redirect after Google OAuth based on stored language"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is a redirect to Tamil after login
        if (response.status_code == 302 and
            response.url == '/tamil/' and
            request.user.is_authenticated):

            # Check if we have a stored language preference
            stored_language = request.session.get('selected_language')
            if stored_language and stored_language != 'tamil':
                language_redirects = {
                    'english': '/english/',
                    'hindi': '/hindi/'
                }
                redirect_url = language_redirects.get(stored_language)
                if redirect_url:
                    print(f"🔗 Middleware redirecting from Tamil to: {redirect_url}")
                    # Clear the stored language to avoid future redirects
                    del request.session['selected_language']
                    return redirect(redirect_url)

        return response