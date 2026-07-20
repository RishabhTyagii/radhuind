from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="tube_dashboard"),
    path("item/add/", views.add_item, name="tube_add_item"),
    path("production/add/", views.add_production, name="tube_add_production"),
    path("sale/add/", views.add_sale, name="tube_add_sale"),
    path("adjustment/add/", views.add_adjustment, name="tube_add_adjustment"),
    path("entries/", views.entries_log, name="tube_entries_log"),
    path("report/monthly/", views.monthly_report, name="tube_monthly_report"),
]