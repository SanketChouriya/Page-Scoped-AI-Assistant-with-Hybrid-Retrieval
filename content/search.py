from django.contrib.postgres.search import SearchQuery, SearchRank
from content.models import PageSection


def keyword_search(context_id, query, k=5):
    try:
        search_query = SearchQuery(query)
        result =  (
            PageSection.objects
            .filter(page_context__session_id=context_id)
            .annotate(rank=SearchRank("search_vector", search_query))
            .filter(rank__gt=0)
            .order_by("-rank")[:k]
        )
        return result, ""
    except Exception as e:
        return None, f"ERR @keyword_search: {str(e)}"
