from django.contrib import admin
from django.urls import path, include
from stock import views as stock_views
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.conf import settings

@never_cache
def service_worker(request):
    sw_path = settings.BASE_DIR / 'static' / 'service-worker.js'
    with open(sw_path, 'rb') as f:
        content = f.read()
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', stock_views.login_view, name='login'),
    path('logout/', stock_views.logout_view, name='logout'),
    path('', stock_views.home, name='home'),
    path('tyre/', include('stock.urls')),
    path('tube/', include('cycletube.urls')),
    path('raw-materials/', include('rawmaterials.urls')),
    path('cycletyre/', include('cycletyres.urls')),
    path('tallysync/', include('tallysync.urls')),
    path('service-worker.js', service_worker, name='service_worker'),
]



