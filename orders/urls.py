from django.urls import path
from . import views

urlpatterns = [
    path('my-orders/', views.my_orders, name='my_orders'),
    path('create/', views.create_order, name='create_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('import/', views.import_orders, name='import_orders'),
]
