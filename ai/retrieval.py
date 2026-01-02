from content.search import keyword_search
from ai.vector_store import semantic_search


def hybrid_retrieve(context_id, question, k=5):
    """
    Hybrid retrieval: combines keyword (PostgreSQL FTS) and semantic (vector) search.

    Strategy:
    1. Run both keyword and semantic search
    2. If keyword search has results, prioritize those (fast, deterministic)
    3. Augment with semantic results for paraphrased/conceptual matches
    4. Deduplicate and return top-k unique chunks
    """
    errors = []

    # Keyword search (PostgreSQL full-text)
    keyword_hits, kw_error = keyword_search(context_id, question, k=k)
    if kw_error:
        errors.append(kw_error)

    keyword_contents = []
    if keyword_hits:
        keyword_contents = [section.content for section in keyword_hits]

    # Semantic search (vector similarity)
    semantic_hits, sem_error = semantic_search(context_id, question, k=k)
    if sem_error:
        errors.append(sem_error)

    # If we have keyword hits, use them as primary and augment with semantic
    if keyword_contents:
        # Deduplicated merge: keyword results first, then unique semantic results
        seen = set(keyword_contents)
        combined = list(keyword_contents)

        for chunk in semantic_hits or []:
            if chunk not in seen:
                combined.append(chunk)
                seen.add(chunk)

        return combined[:k], ""

    # Fallback to semantic-only if no keyword matches
    if semantic_hits:
        return semantic_hits[:k], ""

    # Nothing found
    error_msg = "; ".join(errors) if errors else "No matching content found"
    return [], error_msg
