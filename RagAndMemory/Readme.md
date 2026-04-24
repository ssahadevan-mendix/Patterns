## Architecture overview

```
User Query
    │
    ▼
┌──────────────────────────────────────────────┐
│              RAGMemoryAgent                  │
│                                              │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │   RETRIEVE  │    │   MEMORY LAYERS    │  │
│  │             │    │                    │  │
│  │ Vector Store│    │ 🧠 Working Memory  │  │
│  │  (TF-IDF /  │    │   current entities │  │
│  │  embeddings)│    │   goals, context   │  │
│  │             │    │                    │  │
│  │ top-k docs  │    │ 💬 Conv. Memory    │  │
│  │ by cosine   │    │   sliding window   │  │
│  │ similarity  │    │   of N messages    │  │
│  └──────┬──────┘    │                    │  │
│         │           │ 📖 Episodic Memory │  │
│         └───────────│   compressed past  │  │
│                     │   session summaries│  │
│                     └────────────────────┘  │
│                              │               │
│              ┌───────────────▼────────────┐  │
│              │       System Prompt        │  │
│              │  = RAG docs + episodes +   │  │
│              │    working memory          │  │
│              └───────────────┬────────────┘  │
└──────────────────────────────│───────────────┘
                               │
                        Claude API
                               │
                          Final Answer
```

---

## The three memory layers explained

| Layer | Scope | Stored as | Cleared when |
|---|---|---|---|
| **Working memory** | Current query | Key-value dict | Per query |
| **Conversation memory** | Current session | Sliding message window | `end_session()` |
| **Episodic memory** | All past sessions | Claude-generated summaries | Never (persistent) |

### To upgrade to production
- Replace the TF-IDF embedder with `text-embedding-3-small` (OpenAI) or `voyage-3` (Voyage AI)
- Swap `SimpleVectorStore` for **ChromaDB**, **Pinecone**, or **pgvector**
- Persist episodic memory to a database (SQLite, Postgres, Redis)
- Add semantic similarity for episodic memory retrieval instead of recency-based lookup
