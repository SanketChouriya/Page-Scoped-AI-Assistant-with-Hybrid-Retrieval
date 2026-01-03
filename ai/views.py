import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ai.retrieval import hybrid_retrieve
from ai.llm import ask_llm
from ai.serializers import AskSerializer
from ai.vector_store import semantic_search
from ai.metrics import Timer, collector

logger = logging.getLogger(__name__)


class AskView(APIView):
    """
    Hybrid retrieval endpoint: tries keyword search first, then semantic.
    Use this for most queries.
    """

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Hybrid retrieve: keyword-first with semantic fallback/fusion
        chunks, error, metrics = hybrid_retrieve(data["session_id"], data["question"])

        if not chunks:
            return Response(
                {
                    "answer": "I don't have enough information from this page to answer that.",
                    "debug_error": error if error else None,
                    "metrics": metrics.to_dict() if metrics else None,
                },
                status=status.HTTP_200_OK,
            )

        # Ask LLM with timing
        context = "\n\n".join(chunks)
        with Timer() as llm_timer:
            answer, usage = ask_llm(context, data["question"])

        # Update metrics with LLM timing
        metrics.llm_response_ms = llm_timer.elapsed_ms
        metrics.total_ms += llm_timer.elapsed_ms

        return Response(
            {
                "answer": answer.get("response", answer),
                "usage": _serialize_usage(usage),
                "metrics": metrics.to_dict(),
            },
            status=status.HTTP_200_OK,
        )


class AskPageView(APIView):
    """
    Semantic-only retrieval endpoint: uses vector similarity search.
    Useful when keyword matching is insufficient.
    """

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_id = str(data["session_id"])
        question = data["question"]

        # Retrieve relevant chunks via semantic search only
        with Timer() as sem_timer:
            chunks, error = semantic_search(session_id, question)

        if not chunks:
            return Response(
                {
                    "answer": "I don't have enough information from this page to answer that.",
                    "debug_error": error if error else None,
                },
                status=status.HTTP_200_OK,
            )

        # Ask LLM with timing
        with Timer() as llm_timer:
            answer, usage = ask_llm(context="\n\n".join(chunks), question=question)

        return Response(
            {
                "answer": answer.get("response", answer),
                "usage": _serialize_usage(usage),
                "timing": {
                    "semantic_search_ms": round(sem_timer.elapsed_ms, 1),
                    "llm_response_ms": round(llm_timer.elapsed_ms, 1),
                },
            },
            status=status.HTTP_200_OK,
        )


class MetricsView(APIView):
    """
    Returns aggregate retrieval metrics.
    Useful for monitoring and demonstrating system performance.
    """

    def get(self, request):
        return Response(
            {
                "summary": collector.summary(),
                "description": {
                    "keyword_hit_rate": "Percentage of queries where PostgreSQL FTS found results (higher = lower latency)",
                    "semantic_fallback_rate": "Percentage of queries that fell back to vector search",
                    "avg_latency_ms": "Average end-to-end retrieval time",
                },
            },
            status=status.HTTP_200_OK,
        )


def _serialize_usage(usage):
    """Convert OpenAI usage object to serializable dict."""
    if usage is None:
        return None
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }
