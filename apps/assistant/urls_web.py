from django.urls import path

from apps.assistant.views.web import AssistantChatView

app_name = "assistant"

urlpatterns = [
    path("assistant/", AssistantChatView.as_view(), name="chat"),
]
