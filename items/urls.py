from django.urls import path

from . import views


app_name = "items"

urlpatterns = [
    path("", views.report_collection, name="report-list-create"),
    path("<int:report_id>/", views.report_detail, name="report-detail"),
]
