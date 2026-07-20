from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="cycletyre_dashboard"),
    path("item/add/", views.add_item, name="cycletyre_add_item"),
    path("production/add/", views.add_production, name="cycletyre_add_production"),
    path("sale/add/", views.add_sale, name="cycletyre_add_sale"),
    path("adjustment/add/", views.add_adjustment, name="cycletyre_add_adjustment"),
    path("entries/", views.entries_log, name="cycletyre_entries_log"),
    path("report/monthly/", views.monthly_report, name="cycletyre_monthly_report"),
]