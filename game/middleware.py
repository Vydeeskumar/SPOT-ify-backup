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