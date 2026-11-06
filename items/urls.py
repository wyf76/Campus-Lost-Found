from django.urls import path

from . import views


app_name = "items"

urlpatterns = [
    path("", views.report_collection, name="report-list-create"),
    path("<int:report_id>/", views.report_detail, name="report-detail"),
]


from .account_views import resolve_report

urlpatterns += [
    path("<int:report_id>/resolve/", resolve_report, name="report-resolve"),
]


from .edit_views import edit_report

urlpatterns += [
    path("<int:report_id>/edit/", edit_report, name="report-edit"),
]
