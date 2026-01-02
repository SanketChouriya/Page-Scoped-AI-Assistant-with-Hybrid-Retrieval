
# Page-Scoped AI Assistant with Hybrid Retrieval

A **page-scoped AI assistant** that answers user questions using **only the content of the currently viewed webpage**.  
The system combines **PostgreSQL full-text search** with **semantic retrieval** to maximize **accuracy** while minimizing **latency**.

This project demonstrates a **real-world RAG architecture**, not a toy chatbot.

---

## 🚀 Key Capabilities

- Page-scoped context (no cross-page leakage)
- Hybrid retrieval (keyword + semantic)
- Low-latency responses
- Strict grounding (no hallucinations)
- Chrome extension integration
- Graceful handling of unknown questions

---

## 🧠 Why Page-Scoped AI?

Traditional chatbots:
- Use global knowledge
- Hallucinate answers
- Are slow and unfocused

This system:
- Answers **only from the current webpage**
- Rejects out-of-context questions
- Keeps LLM context small and precise

---

## 🏗 Architecture Overview

```

Browser (Chrome Extension)
↓
Content Ingestion API (Django)
↓
PostgreSQL (Full-Text Search Index)
↓
Hybrid Retrieval Layer
↓
LLM (Context-Bound Answer)

```

---

## 🔍 Hybrid Retrieval Strategy

### 1️⃣ Keyword Search (PostgreSQL Full-Text)
- Exact term matching
- Very low latency (milliseconds)
- Ideal for factual content (policies, definitions, specs)

### 2️⃣ Semantic Retrieval (Embeddings)
- Handles paraphrased or conceptual queries
- Used only when keyword results are insufficient

### 3️⃣ LLM Answering
- Receives **only retrieved content**
- Enforced grounding to prevent hallucinations

This approach balances **precision**, **recall**, and **speed**.

---

## 🧪 Example Query Flow

**User question:**  
> “What is the return policy?”

**System behavior:**
1. Postgres FTS finds policy-related sections
2. Semantic reranking selects best match
3. LLM answers using only that context

**Out-of-context query:**  
> “What is React?”

**Response:**  
> “I don't know based on the provided context.”

---

## ⚙️ Tech Stack

- **Backend:** Django 5.x
- **Database:** PostgreSQL (Full-Text Search)
- **Retrieval:** Hybrid (Keyword + Semantic)
- **LLM:** OpenAI (context-bound)
- **Frontend:** Chrome Extension (Manifest v3)
- **Vector Store:** In-memory (demo-optimized)

---

## 🛡 Guardrails & Safety

- Page-scoped session isolation
- Strict prompt grounding
- Out-of-context detection
- Content size limits
- Graceful invalid session handling

---

## ⏱ Accuracy & Latency Focus

- Keyword retrieval: ~5–20 ms
- Semantic fallback: ~50–150 ms
- LLM call minimized by tight context
- Reduced hallucinations via strict retrieval

---

## ❌ Why Not Fine-Tuning?

- Page content is dynamic
- Session-scoped data
- RAG is cheaper, faster, and more reliable

---

## 📦 Project Structure

```

apps/
├── content/      # Page ingestion & Postgres FTS
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── search.py
│   └── urls.py
│
├── ai/           # Retrieval & reasoning
│   ├── vector_store.py
│   ├── retrieval.py
│   ├── llm.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py

```

---

## 🌐 Chrome Extension

The Chrome extension:
- Extracts visible webpage content
- Sends it to the ingestion API
- Allows users to ask page-specific questions

This turns the system into a **real, usable product**.
