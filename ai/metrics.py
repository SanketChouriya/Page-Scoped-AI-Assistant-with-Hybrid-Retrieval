"""
Latency and accuracy metrics for RAG pipeline.
Tracks retrieval performance to demonstrate engineering maturity.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval operation."""

    session_id: str
    question_length: int = 0

    # Timing (in milliseconds)
    keyword_search_ms: Optional[float] = None
    semantic_search_ms: Optional[float] = None
    llm_response_ms: Optional[float] = None
    total_ms: Optional[float] = None

    # Retrieval stats
    keyword_hits: int = 0
    semantic_hits: int = 0
    total_chunks_retrieved: int = 0

    # Which method provided results
    used_keyword: bool = False
    used_semantic: bool = False

    def log(self):
        """Log metrics in a structured format."""
        retrieval_method = []
        if self.used_keyword:
            retrieval_method.append("keyword")
        if self.used_semantic:
            retrieval_method.append("semantic")

        logger.info(
            "RETRIEVAL_METRICS | "
            f"session={self.session_id[:8]}... | "
            f"method={'+'.join(retrieval_method) or 'none'} | "
            f"keyword_ms={self.keyword_search_ms:.1f} | "
            f"semantic_ms={self.semantic_search_ms:.1f} | "
            f"llm_ms={self.llm_response_ms or 0:.1f} | "
            f"total_ms={self.total_ms:.1f} | "
            f"chunks={self.total_chunks_retrieved}"
        )

    def to_dict(self):
        """Convert to dict for API response."""
        return {
            "timing": {
                "keyword_search_ms": round(self.keyword_search_ms or 0, 1),
                "semantic_search_ms": round(self.semantic_search_ms or 0, 1),
                "llm_response_ms": round(self.llm_response_ms or 0, 1),
                "total_ms": round(self.total_ms or 0, 1),
            },
            "retrieval": {
                "keyword_hits": self.keyword_hits,
                "semantic_hits": self.semantic_hits,
                "total_chunks": self.total_chunks_retrieved,
                "used_keyword": self.used_keyword,
                "used_semantic": self.used_semantic,
            },
        }


class MetricsCollector:
    """
    Collects aggregate metrics across requests.
    Thread-safe for basic operations.
    """

    def __init__(self):
        self.total_requests = 0
        self.keyword_hit_count = 0
        self.semantic_fallback_count = 0
        self.total_latency_ms = 0.0

    def record(self, metrics: RetrievalMetrics):
        """Record metrics from a request."""
        self.total_requests += 1
        self.total_latency_ms += metrics.total_ms or 0

        if metrics.used_keyword and metrics.keyword_hits > 0:
            self.keyword_hit_count += 1
        if metrics.used_semantic and not metrics.used_keyword:
            self.semantic_fallback_count += 1

    @property
    def keyword_hit_rate(self) -> float:
        """Percentage of requests where keyword search found results."""
        if self.total_requests == 0:
            return 0.0
        return (self.keyword_hit_count / self.total_requests) * 100

    @property
    def avg_latency_ms(self) -> float:
        """Average total latency per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    def summary(self) -> dict:
        """Get summary stats."""
        return {
            "total_requests": self.total_requests,
            "keyword_hit_rate": f"{self.keyword_hit_rate:.1f}%",
            "semantic_fallback_rate": f"{(self.semantic_fallback_count / max(1, self.total_requests)) * 100:.1f}%",
            "avg_latency_ms": f"{self.avg_latency_ms:.1f}ms",
        }


# Global collector instance
collector = MetricsCollector()


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time = None
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000


def timed(func):
    """Decorator to time function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{func.__name__} took {elapsed:.1f}ms")
        return result

    return wrapper
