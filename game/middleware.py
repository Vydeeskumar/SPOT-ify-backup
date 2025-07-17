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
    """Simple middleware to redirect after Google OAuth based on redirect flag"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if we have a redirect flag set by the signal
        redirect_url = request.session.get('redirect_after_login')
        if redirect_url and request.user.is_authenticated:
            print(f"🔥 MIDDLEWARE: Found redirect flag: {redirect_url}")

            # Check if this is a redirect to Tamil after login
            if response.status_code == 302 and response.url == '/tamil/':
                print(f"🔥 MIDDLEWARE: Intercepting Tamil redirect, redirecting to: {redirect_url}")
                # Clear the redirect flag
                del request.session['redirect_after_login']
                return redirect(redirect_url)

        return response