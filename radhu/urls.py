from django.contrib import admin
from django.urls import path, include
from stock import views as stock_views

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
]