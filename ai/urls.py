from django.urls import path
from ai.views import AskView, AskPageView

urlpatterns = [
    path("ask/", AskView.as_view(), name="ask-AI-about-page"),
]