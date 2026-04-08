from django.urls import path
from .views import (
    chat_unread_count,
    conversation_detail,
    conversation_list,
    conversation_messages_json,
    start_conversation,
)

urlpatterns = [
    path("", conversation_list, name="conversation_list"),
    path("start/", start_conversation, name="start_conversation"),
    path("unread-count/", chat_unread_count, name="chat_unread_count"),
    path("conversations/<uuid:pk>/", conversation_detail, name="conversation_detail"),
    path("conversations/<uuid:pk>/messages-json/", conversation_messages_json, name="conversation_messages_json"),
]