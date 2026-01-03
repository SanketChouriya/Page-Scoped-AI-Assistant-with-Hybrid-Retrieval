from content.search import keyword_search
from ai.vector_store import semantic_search
from ai.metrics import RetrievalMetrics, Timer, collector


def hybrid_retrieve(context_id, question, k=8):
    """
    Hybrid retrieval: combines keyword (PostgreSQL FTS) and semantic (vector) search.

    Strategy:
    1. Run both keyword and semantic search
    2. If keyword search has results, prioritize those (fast, deterministic)
    3. Augment with semantic results for paraphrased/conceptual matches
    4. Deduplicate and return top-k unique chunks

    Returns:
        tuple: (chunks, error_string, metrics)
    """
    metrics = RetrievalMetrics(
        session_id=str(context_id),
        question_length=len(question),
    )
    errors = []

    # Keyword search (PostgreSQL full-text)
    with Timer() as kw_timer:
        keyword_hits, kw_error = keyword_search(context_id, question, k=k)
    metrics.keyword_search_ms = kw_timer.elapsed_ms

    if kw_error:
        errors.append(kw_error)

    keyword_contents = []
    if keyword_hits:
        keyword_contents = [section.content for section in keyword_hits]
        metrics.keyword_hits = len(keyword_contents)
        metrics.used_keyword = True

    # Semantic search (vector similarity)
    with Timer() as sem_timer:
        semantic_hits, sem_error = semantic_search(context_id, question, k=k)
    metrics.semantic_search_ms = sem_timer.elapsed_ms

    if sem_error:
        errors.append(sem_error)

    if semantic_hits:
        metrics.semantic_hits = len(semantic_hits)
        metrics.used_semantic = True

    # If we have keyword hits, use them as primary and augment with semantic
    if keyword_contents:
        # Deduplicated merge: keyword results first, then unique semantic results
        seen = set(keyword_contents)
        combined = list(keyword_contents)

        for chunk in semantic_hits or []:
            if chunk not in seen:
                combined.append(chunk)
                seen.add(chunk)

        result = combined[:k]
        metrics.total_chunks_retrieved = len(result)
        metrics.total_ms = kw_timer.elapsed_ms + sem_timer.elapsed_ms
        metrics.log()
        collector.record(metrics)
        return result, "", metrics

    # Fallback to semantic-only if no keyword matches
    if semantic_hits:
        result = semantic_hits[:k]
        metrics.total_chunks_retrieved = len(result)
        metrics.total_ms = kw_timer.elapsed_ms + sem_timer.elapsed_ms
        metrics.log()
        collector.record(metrics)
        return result, "", metrics

    # Nothing found
    error_msg = "; ".join(errors) if errors else "No matching content found"
    metrics.total_ms = kw_timer.elapsed_ms + sem_timer.elapsed_ms
    metrics.log()
    collector.record(metrics)
    return [], error_msg, metrics
