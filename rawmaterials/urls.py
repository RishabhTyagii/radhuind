from django.urls import path
from . import views

urlpatterns = [

    path("", views.dashboard, name="raw_dashboard"),

    path("new-entry/", views.new_entry, name="raw_new_entry"),

    path("entries/", views.entries, name="raw_entries"),

    path("stock/", views.current_stock, name="raw_stock"),

    path("low-stock/", views.low_stock, name="raw_low_stock"),
    
    path(
    "export-current-stock/",
    views.export_current_stock_excel,
    name="export_current_stock",
),

path(
    "tally/",
    views.tally_view,
    name="raw_tally",
),

# path(
#     "tally/export/",
#     views.export_tally_excel,
#     name="export_raw_tally",
# ),
    # path("export-low-stock/", views.export_low_stock_excel, name="export_low_stock"),
]