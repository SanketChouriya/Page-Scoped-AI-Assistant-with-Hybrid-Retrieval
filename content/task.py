from celery import shared_task
from content.models import PageSection
from ai.vector_store import add

@shared_task
def process_page_context(context_id):
    try:
        sections = PageSection.objects.filter(
            page_context__session_id=context_id
        )
        chunks = [section.content for section in sections]
        add(context_id, chunks)
        return True
    except Exception as e:
        print(f"❌ ERR @process_page_context: {str(e)}")
        return False