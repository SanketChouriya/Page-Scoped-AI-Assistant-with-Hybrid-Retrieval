import uuid
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class PageContext(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class PageSection(models.Model):
    page_context = models.ForeignKey(
        PageContext, on_delete=models.CASCADE, related_name="sections"
    )
    section_type = models.CharField(max_length=50)
    content = models.TextField()
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=["search_vector"]),
        ]
