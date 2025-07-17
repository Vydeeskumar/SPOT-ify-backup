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
        # Check BEFORE processing the response
        redirect_url = request.session.get('redirect_after_login')
        if redirect_url and request.user.is_authenticated:
            print(f"🔥 MIDDLEWARE: Found redirect flag: {redirect_url}")
            print(f"🔥 MIDDLEWARE: Current path: {request.path}")

            # If we're on the Tamil page and have a redirect flag, redirect immediately
            if request.path == '/tamil/' or request.path == '/tamil':
                print(f"🔥 MIDDLEWARE: On Tamil page, redirecting to: {redirect_url}")
                # Clear the redirect flag
                del request.session['redirect_after_login']
                return redirect(redirect_url)

        response = self.get_response(request)

        # Also check after response for redirect responses
        if redirect_url and request.user.is_authenticated:
            if response.status_code == 302 and '/tamil/' in str(response.url):
                print(f"🔥 MIDDLEWARE: Intercepting Tamil redirect response, redirecting to: {redirect_url}")
                # Clear the redirect flag
                if 'redirect_after_login' in request.session:
                    del request.session['redirect_after_login']
                return redirect(redirect_url)

        return response