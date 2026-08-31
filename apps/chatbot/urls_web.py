from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("chatbot/", views.ChatbotPageView.as_view(), name="chat"),
    path("chatbot/ask/", views.ChatbotAskView.as_view(), name="ask"),
    path("chatbot/clear/", views.ChatbotClearView.as_view(), name="clear"),
]
