from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """Custom login redirect that respects language selection"""
        # Check for next parameter first
        next_url = request.GET.get('next')
        if next_url:
            print(f"🔗 Account adapter: next={next_url}")
            # Validate that the next URL is one of our supported languages
            valid_redirects = ['/tamil/', '/english/', '/hindi/']
            if next_url in valid_redirects:
                print(f"✅ Account adapter redirecting to: {next_url}")
                return next_url
        
        # Default to Tamil
        print(f"❌ Account adapter defaulting to Tamil")
        return '/tamil/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        """Custom social login redirect that respects language selection"""
        # Check for next parameter first
        next_url = request.GET.get('next')
        if next_url:
            print(f"🔗 Social adapter: next={next_url}")
            # Validate that the next URL is one of our supported languages
            valid_redirects = ['/tamil/', '/english/', '/hindi/']
            if next_url in valid_redirects:
                print(f"✅ Social adapter redirecting to: {next_url}")
                return next_url
        
        # Check session for stored language preference
        stored_language = request.session.get('selected_language')
        if stored_language:
            language_redirects = {
                'tamil': '/tamil/',
                'english': '/english/',
                'hindi': '/hindi/'
            }
            redirect_url = language_redirects.get(stored_language, '/tamil/')
            print(f"✅ Social adapter using stored language: {stored_language} -> {redirect_url}")
            return redirect_url
        
        # Default to Tamil
        print(f"❌ Social adapter defaulting to Tamil")
        return '/tamil/'
