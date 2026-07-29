from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tyre/add/", views.add_tyre, name="add_tyre"),
    path("production/add/", views.add_production, name="add_production"),
    path("dispatch/add/", views.add_dispatch, name="add_dispatch"),
    path("adjustment/add/", views.add_adjustment, name="add_adjustment"),
    path("entries/", views.entries_log, name="entries_log"),
    path("report/monthly/", views.monthly_report, name="monthly_report"),
    path("report/production-sheet/", views.production_sheet, name="production_sheet"),
    path("daily-summary/", views.daily_summary, name="daily_summary"),
]