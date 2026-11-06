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


from .saved_views import saved_report_change, saved_report_list

urlpatterns += [
    path("saved/", saved_report_list, name="saved-report-list"),
    path("<int:report_id>/save/", saved_report_change, name="saved-report-change"),
]


from .flag_views import flag_report, report_flag_list

urlpatterns += [
    path("flags/", report_flag_list, name="report-flag-list"),
    path("<int:report_id>/flag/", flag_report, name="report-flag"),
]
