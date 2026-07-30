from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from .models import PAGES_MAP

# These URLs are always allowed - never block them
ALWAYS_ALLOWED = {'home', 'login', 'logout', 'service_worker', 'password_change', 'password_change_done'}

class PageAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Build a flat set of all protected url names
        self.protected_urls = set()
        for module, pages in PAGES_MAP.items():
            for url_name, title in pages:
                self.protected_urls.add(url_name)
        
        # Remove always-allowed from protected set to prevent loops
        self.protected_urls -= ALWAYS_ALLOWED

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            try:
                url_name = resolve(request.path_info).url_name
                
                # Only check if it's a protected URL
                if url_name and url_name in self.protected_urls:
                    profile = getattr(request.user, 'profile', None)
                    allowed_pages = getattr(profile, 'allowed_pages', []) if profile else []
                    
                    if url_name not in allowed_pages:
                        messages.error(request, 'You do not have permission to access this page.')
                        return redirect('home')
            except Exception:
                pass
                
        response = self.get_response(request)
        return response
