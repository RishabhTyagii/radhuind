from django.urls import path
from . import views

urlpatterns = [
    path("webhook/", views.tally_webhook, name="tally_webhook"),
    path("", views.sales_summary, name="tally_sales_summary"),
    path("mapping/", views.mapping_list, name="tally_mapping_list"),
    path("mapping/add/", views.add_mapping, name="tally_add_mapping"),
    path("logs/", views.sync_log, name="tally_sync_log"),
]