from django.urls import path
from .views import waiting_room_add, waiting_room_list, waiting_room_remove

urlpatterns = [
    path("", waiting_room_list, name="waiting_room_list"),
    path("add/", waiting_room_add, name="waiting_room_add"),
    path("<uuid:pk>/remove/", waiting_room_remove, name="waiting_room_remove"),
]