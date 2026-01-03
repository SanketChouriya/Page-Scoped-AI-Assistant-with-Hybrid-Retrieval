# Page-Scoped AI Assistant with Hybrid Retrieval

A **page-scoped AI assistant** that answers user questions using **only the content of the currently viewed webpage**.
The system combines **PostgreSQL full-text search** with **semantic vector retrieval** to maximize **accuracy** while minimizing **latency**.

This project demonstrates a **production-grade RAG architecture** — not a toy chatbot.

---

## Key Capabilities

- **Page-scoped context** — No cross-page leakage or hallucinations
- **Hybrid retrieval** — Keyword (PostgreSQL FTS) + Semantic (OpenAI embeddings)
- **Low-latency responses** — Keyword search in ~1ms, semantic fallback when needed
- **Strict grounding** — LLM never uses outside knowledge
- **Chrome extension** — Real product demo with polished UI
- **Metrics & observability** — Track keyword hit rate, latency breakdown
- **Guardrails** — Rate limiting, size limits, timeouts

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Chrome Extension                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Content.js  │───▶│  Popup.js   │───▶│   Popup UI  │         │
│  │ (Extract)   │    │ (API calls) │    │ (Display)   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Django Backend                              │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │   Content App        │    │      AI App          │          │
│  │  ├─ IngestPageView   │    │  ├─ AskView (hybrid) │          │
│  │  ├─ PageContext      │    │  ├─ hybrid_retrieve  │          │
│  │  ├─ PageSection      │    │  ├─ semantic_search  │          │
│  │  └─ keyword_search   │    │  ├─ ask_llm          │          │
│  └──────────────────────┘    │  └─ MetricsView      │          │
│              │               └──────────────────────┘          │
│              ▼                           │                      │
│  ┌──────────────────────┐               │                      │
│  │    PostgreSQL        │               │                      │
│  │  ├─ PageContext      │◀──────────────┤                      │
│  │  ├─ PageSection      │               │                      │
│  │  └─ GIN Index (FTS)  │               ▼                      │
│  └──────────────────────┘    ┌──────────────────────┐          │
│                              │  In-Memory Vector    │          │
│                              │  Store (Embeddings)  │          │
│                              └──────────────────────┘          │
│                                         │                      │
│                                         ▼                      │
│                              ┌──────────────────────┐          │
│                              │   OpenAI API         │          │
│                              │  ├─ GPT-4o-mini      │          │
│                              │  └─ text-embedding   │          │
│                              └──────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hybrid Retrieval Strategy

### 1. Keyword Search (PostgreSQL Full-Text Search)
- Uses `SearchVectorField` with GIN index
- Sub-millisecond latency
- Ideal for exact matches: policies, specs, definitions

### 2. Semantic Search (Vector Similarity)
- OpenAI `text-embedding-3-small` embeddings
- Cosine similarity matching
- Handles paraphrased or conceptual queries

### 3. Fusion Strategy
```python
# Pseudocode
keyword_results = postgres_fts_search(query)
semantic_results = vector_similarity_search(query)

if keyword_results:
    # Prioritize keyword (fast, deterministic)
    # Augment with unique semantic results
    return deduplicated_merge(keyword_results, semantic_results)
else:
    # Fallback to semantic only
    return semantic_results
```

### 4. LLM Answering
- Receives **only retrieved chunks** as context
- System prompt enforces strict grounding
- Returns "I don't know" for out-of-context questions

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 5.2, Django REST Framework |
| **Database** | PostgreSQL with Full-Text Search |
| **Vector Store** | In-memory (NumPy + scikit-learn) |
| **Embeddings** | OpenAI `text-embedding-3-small` |
| **LLM** | OpenAI `gpt-4o-mini` |
| **Task Queue** | Celery + Redis (optional) |
| **Frontend** | Chrome Extension (Manifest v3) |
| **CORS** | django-cors-headers |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/content/ingest-page/` | POST | Ingest page content (URL + sections) |
| `/ai/ask/` | POST | Ask question (hybrid retrieval) |
| `/ai/ask-semantic/` | POST | Ask question (semantic only) |
| `/ai/metrics/` | GET | Get aggregate performance metrics |

### Request/Response Examples

#### Ingest Page
```bash
curl -X POST http://localhost:8005/content/ingest-page/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "sections": [
      {"type": "heading", "text": "Product Overview"},
      {"type": "paragraph", "text": "This product helps you..."}
    ]
  }'

# Response
{
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "indexed",
  "section_count": 2
}
```

#### Ask Question
```bash
curl -X POST http://localhost:8005/ai/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What does this product do?"
  }'

# Response
{
  "answer": "This product helps you...",
  "usage": {
    "prompt_tokens": 156,
    "completion_tokens": 24,
    "total_tokens": 180
  },
  "metrics": {
    "timing": {
      "keyword_search_ms": 0.5,
      "semantic_search_ms": 245.3,
      "llm_response_ms": 890.2,
      "total_ms": 1136.0
    },
    "retrieval": {
      "keyword_hits": 2,
      "semantic_hits": 3,
      "total_chunks": 3,
      "used_keyword": true,
      "used_semantic": true
    }
  }
}
```

#### Get Metrics
```bash
curl http://localhost:8005/ai/metrics/

# Response
{
  "summary": {
    "total_requests": 47,
    "keyword_hit_rate": "72.3%",
    "semantic_fallback_rate": "27.7%",
    "avg_latency_ms": "1245.6ms"
  }
}
```

---

## Guardrails & Limits

| Guardrail | Limit | Purpose |
|-----------|-------|---------|
| Max section length | 10,000 chars | Prevent token overflow |
| Max sections per page | 50 | Control ingestion size |
| Max total content | 100,000 chars | Cost control |
| LLM timeout | 30 seconds | Prevent hanging requests |
| Rate limit | 100 req/hour/IP | Prevent abuse |
| Question max length | 20,000 chars | Input validation |

---

## Project Structure

```
DomSpec-ChatBot/
├── chatbot_conf/           # Django project config
│   ├── settings.py         # DB, CORS, throttling, logging
│   ├── urls.py             # Root URL routing
│   ├── celery.py           # Celery configuration
│   └── wsgi.py
│
├── content/                # Content ingestion app
│   ├── models.py           # PageContext, PageSection
│   ├── views.py            # IngestPageView
│   ├── serializers.py      # Validation + guardrails
│   ├── search.py           # PostgreSQL FTS
│   └── urls.py
│
├── ai/                     # AI/RAG engine app
│   ├── views.py            # AskView, MetricsView
│   ├── retrieval.py        # Hybrid retrieval logic
│   ├── vector_store.py     # In-memory embeddings
│   ├── llm.py              # OpenAI integration
│   ├── metrics.py          # Latency tracking
│   ├── serializers.py
│   └── urls.py
│
├── chrome_extension/       # Browser extension
│   ├── manifest.json       # Extension config (v3)
│   ├── content.js          # Page content extraction
│   ├── popup.html          # Extension UI
│   └── popup.js            # API integration
│
├── .env                    # Environment variables
├── docker-compose.yml      # Redis for Celery
├── manage.py
└── README.md
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis (optional, for Celery)
- OpenAI API key

### 1. Clone & Setup Environment
```bash
git clone <repo-url>
cd DomSpec-ChatBot

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# .env file
PG_DATABASE=dom-spec-chatbot-local
PG_HOST=127.0.0.1
PG_PORT=5432
PG_USER=your_user
PG_USER_PASSWORD=your_password

OPENAI_API_KEY=sk-your-openai-key
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 3. Setup Database
```bash
# Create PostgreSQL database
createdb dom-spec-chatbot-local

# Run migrations
python manage.py migrate
```

### 4. Run the Server
```bash
python manage.py runserver 8005
```

### 5. (Optional) Run Celery Worker
```bash
docker-compose up -d  # Start Redis
celery -A chatbot_conf worker -l info
```

---

## Chrome Extension Setup

### Load Extension
1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `chrome_extension/` folder

### Usage
1. Navigate to any webpage
2. Click the extension icon
3. Type a question about the page
4. Press Enter or click "Ask Question"

---

## Example Query Flow

**User visits:** Product documentation page
**User asks:** "What are the system requirements?"

```
1. Content.js extracts page sections
2. Popup.js sends to /content/ingest-page/
3. PostgreSQL stores sections with SearchVector
4. Vector store creates embeddings
5. User question sent to /ai/ask/
6. Keyword search finds "requirements" section (0.5ms)
7. Semantic search augments results (200ms)
8. LLM generates answer from context (900ms)
9. Response displayed in popup
```

**Out-of-context question:** "What is React?"
**Response:** "I don't know based on the provided context."

---

## Performance Characteristics

| Operation | Typical Latency |
|-----------|-----------------|
| Keyword search | 0.5 - 5 ms |
| Semantic search | 200 - 500 ms |
| LLM response | 800 - 1500 ms |
| **Total (with keyword hit)** | **~1000 - 1800 ms** |

**Keyword hit rate target:** 70%+ (reduces avg latency significantly)

---

## Why This Architecture?

### Why Hybrid Retrieval?
- **Keyword-first:** Fast, deterministic, great for factual content
- **Semantic fallback:** Handles paraphrasing and conceptual questions
- **Best of both worlds:** Speed when possible, comprehension when needed

### Why Page-Scoped?
- **No hallucinations:** LLM can only use provided context
- **Session isolation:** Each page is independent
- **Smaller context:** Faster, cheaper, more accurate

### Why Not Fine-Tuning?
- Page content is dynamic (changes every visit)
- Session-scoped data (not persistent knowledge)
- RAG is cheaper, faster, and more maintainable

---

## Future Improvements

- [ ] Persistent vector store (pgvector)
- [ ] Conversation history within session
- [ ] Multi-page context (user-controlled)
- [ ] Streaming responses
- [ ] Authentication & user sessions
- [ ] Production deployment (Gunicorn, nginx)

---

## License

MIT License - See LICENSE file for details.
