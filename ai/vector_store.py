import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VECTOR_STORE = {}


# Batch in chunks of ~100 texts:
def embed_texts(texts: list[str], batch_size=100) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
        )
        embeddings.extend([item.embedding for item in response.data])
    return embeddings


def add(session_id, chunks: list[str]):
    embeddings = embed_texts(chunks)

    VECTOR_STORE[str(session_id)] = {
        "embeddings": np.array(embeddings),
        "chunks": chunks,
    }


def semantic_search(session_id, query: str, k=3):
    try:
        data = VECTOR_STORE.get(str(session_id))
        if not data:
            return [], f"No Data from provided sessionID (`{str(session_id)}`) received"

        query_embedding = embed_texts([query])[0]
        scores = cosine_similarity([query_embedding], data["embeddings"])[0]
        top_k = scores.argsort()[-k:][::-1]

        results = [data["chunks"][i] for i in top_k]
        return results, ""
    except Exception as e:
        return [], f"ERR @semantic_search: {str(e)}"
