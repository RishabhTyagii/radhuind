from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
]
