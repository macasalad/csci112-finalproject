from django.urls import path
from . import views


urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("create/", views.create_event_view, name="create_event"),
    path("my_events/", views.org_event_list_view, name="org_event_list"),
    path("edit/<str:event_id>/", views.edit_event_view, name="edit_event"),
    path("cancel/<str:event_id>/", views.cancel_event_view, name="cancel_event"),
    path("<str:event_id>/", views.event_detail_view, name="event_detail"),
]