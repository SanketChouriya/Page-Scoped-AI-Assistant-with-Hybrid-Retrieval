from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.postgres.search import SearchVector

from content.models import PageSection, PageContext
from content.serializers import IngestPageSerializer
from ai.vector_store import add


class IngestPageView(APIView):
    def post(self, request):
        serializer = IngestPageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Create PageContext and PageSections atomically
        with transaction.atomic():
            context = PageContext.objects.create(url=data["url"])
            sections = PageSection.objects.bulk_create(
                [
                    PageSection(
                        page_context=context,
                        section_type=s["type"],
                        content=s["text"],
                    )
                    for s in data["sections"]
                ]
            )

            # Populate search_vector for full-text search
            PageSection.objects.filter(page_context=context).update(
                search_vector=SearchVector("content")
            )

        # Build chunks list and populate in-memory vector store
        chunks = [s["text"] for s in data["sections"]]
        add(context.session_id, chunks)

        return Response(
            {
                "context_id": str(context.session_id),
                "status": "indexed",
                "section_count": len(sections),
            },
            status=status.HTTP_201_CREATED,
        )
