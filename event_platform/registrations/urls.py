from django.urls import path
from . import views


urlpatterns = [
    path("enlist/<str:event_id>/", views.enlist_view, name="enlist"),
    path("delist/<str:event_id>/", views.delist_view, name="delist"),
]