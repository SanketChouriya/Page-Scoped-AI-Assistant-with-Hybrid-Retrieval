from django.contrib.postgres.search import SearchQuery, SearchRank
from content.models import PageSection


def keyword_search(context_id, query, k=5):
    """
    Full-text search using PostgreSQL.

    Uses OR logic between query terms for better recall.
    This helps when query terms like 'Indian' don't exactly match
    document terms like 'India' due to stemming differences.
    """
    try:
        # Split query into terms and create OR-combined search
        # This improves recall at slight cost to precision
        terms = query.split()
        if len(terms) > 1:
            # Combine terms with OR for better recall
            search_query = SearchQuery(terms[0])
            for term in terms[1:]:
                search_query = search_query | SearchQuery(term)
        else:
            search_query = SearchQuery(query)

        result = (
            PageSection.objects
            .filter(page_context__session_id=context_id)
            .annotate(rank=SearchRank("search_vector", search_query))
            .filter(rank__gt=0)
            .order_by("-rank")[:k]
        )
        return result, ""
    except Exception as e:
        return None, f"ERR @keyword_search: {str(e)}"
