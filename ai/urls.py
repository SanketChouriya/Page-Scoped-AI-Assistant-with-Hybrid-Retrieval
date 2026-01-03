from django.urls import path
from ai.views import AskView, AskPageView, MetricsView

urlpatterns = [
    path("ask/", AskView.as_view(), name="ask-hybrid"),
    path("ask-semantic/", AskPageView.as_view(), name="ask-semantic-only"),
    path("metrics/", MetricsView.as_view(), name="retrieval-metrics"),
]