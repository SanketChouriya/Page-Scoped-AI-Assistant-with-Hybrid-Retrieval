from django.urls import path
from content.views import IngestPageView

urlpatterns = [
    path("ingest-page/", IngestPageView.as_view(), name="ingest-page"),
]